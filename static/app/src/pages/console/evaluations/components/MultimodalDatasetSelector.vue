<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { Edit, SortDown, SortUp } from '@element-plus/icons-vue'
import {
  ElButton,
  ElCheckbox,
  ElInput,
  ElRadio,
  ElRadioGroup,
  ElTable,
  ElTableColumn
} from 'element-plus'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { getMultimodalDatasets } from '@/api/evaluations'
import type { EvaluationDatasetConfig } from '@/api/evaluations/types'
import { evalBatchText, evalText, multimodalTaskNameMap } from '../evaluationFormLabels'

const modelValue = defineModel<EvaluationDatasetConfig[]>({ default: [] })
const tids = defineModel<string[]>('tids', { default: [] })

const props = defineProps<{
  completion?: boolean
}>()

const emit = defineEmits<{
  completed: [value: boolean]
  mounted: []
}>()

type MultimodalDatasetRow = EvaluationDatasetConfig & {
  id: number
  taskId: number
  taskName: string
  leaderboard?: boolean
}

const filterText = ref('')
const factor = ref('all')
const multipleTableRef = ref<InstanceType<typeof ElTable>>()
const multipleSelection = ref<MultimodalDatasetRow[]>([])
const form = reactive<Record<string, boolean>>({})
const isIndeterminate = reactive<Record<string, boolean>>({})

const { data: groups, isLoading } = useQuery({
  queryKey: ['evaluation-multimodal-datasets'],
  queryFn: getMultimodalDatasets
})

const multimodalTasks = computed(() =>
  (groups.value || []).map((group) => ({
    ...group,
    data: group.data.map((dataset) => ({
      ...dataset,
      id: Number(dataset.id),
      taskId: group.id,
      taskName: group.name
    }))
  }))
)

const fullDatasets = computed(() =>
  multimodalTasks.value.flatMap((group) =>
    group.data.map((dataset) => ({
      ...dataset,
      description: dataset.description || ''
    }))
  )
)

const currentDatasets = computed(() => {
  if (factor.value === 'all') {
    return fullDatasets.value
  }

  return fullDatasets.value.filter(
    (dataset) => dataset.leaderboard || dataset.description === '榜单任务'
  )
})

const filteredDatasets = computed(() => {
  const lowerText = filterText.value.trim().toLowerCase()
  if (!lowerText) {
    return currentDatasets.value
  }

  return currentDatasets.value.filter((dataset) =>
    (dataset.datasetShow || '').toLowerCase().includes(lowerText)
  )
})

const selectedDatasets = computed(() =>
  multipleSelection.value.filter((selectedItem) =>
    currentDatasets.value.some((datasetItem) => datasetItem.id === selectedItem.id)
  )
)

const taskLabel = (name?: string) => (name ? multimodalTaskNameMap[name] || name : '-')

const leaderboardLabel = (row: MultimodalDatasetRow) =>
  row.leaderboard ? evalBatchText.leaderboadTasks : evalBatchText.nonLeaderboardTasks

const toggleSelection = (rows?: MultimodalDatasetRow[], selected?: boolean) => {
  if (rows?.length) {
    rows.forEach((row) => {
      multipleTableRef.value?.toggleRowSelection(row, selected)
    })
  } else {
    multipleTableRef.value?.clearSelection()
  }
}

const toggleRowSelection = async () => {
  await nextTick()
  toggleSelection(selectedDatasets.value, true)
}

const handleCheckMultimodal = (value: boolean, key: string) => {
  isIndeterminate[key] = false
  const currentTaskDatasets = multimodalTasks.value.find((item) => item.id === Number(key))?.data
  toggleSelection(currentTaskDatasets, value)
}

const handleSelectionChange = (value: MultimodalDatasetRow[]) => {
  const selectedIds = value.map((dataset) => dataset.id)
  const duplicateIds = selectedIds.filter((id, index) => selectedIds.indexOf(id) !== index)

  if (duplicateIds.length) {
    multipleSelection.value = multipleSelection.value.filter(
      (dataset) => !duplicateIds.includes(dataset.id)
    )
    toggleSelection(
      value.filter((dataset) => duplicateIds.includes(dataset.id)),
      false
    )
  } else {
    multipleSelection.value = value
  }

  modelValue.value = multipleSelection.value
  tids.value = Object.keys(form).filter((item) => form[item])

  for (const key of Object.keys(form)) {
    const datasetsCount = multimodalTasks.value.find((item) => item.id === Number(key))?.data.length
    const selectedCount = value.filter((dataset) => dataset.taskId === Number(key)).length
    form[key] = Boolean(datasetsCount && selectedCount === datasetsCount)
    isIndeterminate[key] = selectedCount > 0 && selectedCount < Number(datasetsCount || 0)
  }
}

const handleClickConfirm = async () => {
  if (factor.value === 'leaderboard') {
    multipleSelection.value = multipleSelection.value.filter(
      (dataset) => dataset.leaderboard || dataset.description === '榜单任务'
    )
    modelValue.value = multipleSelection.value
  }
  await nextTick()
  emit('completed', true)
}

const handleClickEdit = async () => {
  emit('completed', false)
  await toggleRowSelection()
}

const move = (index: number, direction: 'up' | 'down') => {
  const datasets = [...multipleSelection.value]
  if (direction === 'up' && index > 0) {
    ;[datasets[index], datasets[index - 1]] = [datasets[index - 1], datasets[index]]
  }
  if (direction === 'down' && index < datasets.length - 1) {
    ;[datasets[index], datasets[index + 1]] = [datasets[index + 1], datasets[index]]
  }
  multipleSelection.value = datasets
  modelValue.value = datasets
}

watch(
  () => multimodalTasks.value,
  async (tasks) => {
    tasks.forEach((task) => {
      form[task.id] = false
      isIndeterminate[task.id] = false
    })
    multipleSelection.value = modelValue.value as MultimodalDatasetRow[]
    await toggleRowSelection()
    emit('mounted')
  },
  { once: true }
)

watch(
  () => modelValue.value,
  async (value) => {
    multipleSelection.value = value as MultimodalDatasetRow[]
    await toggleRowSelection()
  },
  { immediate: true }
)

watchDebounced(
  () => filterText.value,
  async () => {
    await toggleRowSelection()
  },
  { debounce: 50, maxWait: 500 }
)

watch(
  () => factor.value,
  async () => {
    await toggleRowSelection()
  }
)
</script>

<template>
  <div v-loading="isLoading" class="multimodal-dataset-selector" element-loading-text="Loading...">
    <template v-if="!props.completion">
      <div class="cata-wrapper">
        <ElCheckbox
          v-for="task in multimodalTasks"
          :key="task.id"
          v-model="form[task.id]"
          :indeterminate="isIndeterminate[task.id]"
          @change="(value) => handleCheckMultimodal(Boolean(value), String(task.id))"
        >
          {{ taskLabel(task.name) }}
        </ElCheckbox>
      </div>
      <div class="search-wrapper w-full">
        <ElRadioGroup v-model="factor" class="mr-[12px]">
          <ElRadio value="all">All</ElRadio>
          <ElRadio value="leaderboard">{{ evalText.leaderboardDatasets }}</ElRadio>
        </ElRadioGroup>
        <ElInput
          v-model="filterText"
          :placeholder="evalText.searchDatasets"
          class="flex-1"
          clearable
          size="large"
        />
        <ElButton
          size="large"
          type="primary"
          class="ml-[12px]"
          :title="evalText.clickConfirm"
          @click="handleClickConfirm"
        >
          {{ evalText.datasetConfirm }}
        </ElButton>
      </div>
      <div class="content-wrapper">
        <ElTable
          ref="multipleTableRef"
          :data="filteredDatasets"
          style="width: 100%"
          max-height="550"
          row-key="id"
          @selection-change="handleSelectionChange"
        >
          <ElTableColumn type="selection" width="55" reserve-selection />
          <ElTableColumn property="taskName" :label="evalText.tasks">
            <template #default="{ row }">{{ taskLabel(row.taskName || row.name) }}</template>
          </ElTableColumn>
          <ElTableColumn property="datasetShow" :label="evalBatchText.datasetName" />
          <ElTableColumn property="description" :label="evalBatchText.datasetDesc">
            <template #default="{ row }">{{ leaderboardLabel(row) }}</template>
          </ElTableColumn>
        </ElTable>
      </div>
    </template>

    <template v-else>
      <div class="cata-wrapper flex">
        <div>
          <ElCheckbox
            v-for="task in multimodalTasks"
            :key="task.id"
            v-model="form[task.id]"
            disabled
            :indeterminate="isIndeterminate[task.id]"
          >
            {{ taskLabel(task.name) }}
          </ElCheckbox>
        </div>
        <div class="ml-[12px]">
          <ElButton
            type="primary"
            class="ml-[12px]"
            circle
            :title="evalText.edit"
            @click="handleClickEdit"
          >
            <Edit class="dataset-action-icon" />
          </ElButton>
        </div>
      </div>
      <div class="content-wrapper">
        <ElTable :data="selectedDatasets" style="width: 100%" max-height="550">
          <ElTableColumn property="taskName" :label="evalText.tasks">
            <template #default="{ row }">{{ taskLabel(row.taskName || row.name) }}</template>
          </ElTableColumn>
          <ElTableColumn property="datasetShow" :label="evalBatchText.datasetName" />
          <ElTableColumn property="description" :label="evalBatchText.datasetDesc">
            <template #default="{ row }">{{ leaderboardLabel(row) }}</template>
          </ElTableColumn>
          <ElTableColumn :label="evalText.orderOfExecution || 'Order'">
            <template #default="{ $index }">
              <ElButton
                size="small"
                type="primary"
                :disabled="$index === selectedDatasets.length - 1"
                plain
                @click="move($index, 'down')"
              >
                <SortDown class="dataset-action-icon" />
              </ElButton>
              <ElButton
                size="small"
                type="primary"
                :disabled="$index === 0"
                plain
                @click="move($index, 'up')"
              >
                <SortUp class="dataset-action-icon" />
              </ElButton>
            </template>
          </ElTableColumn>
        </ElTable>
      </div>
    </template>
  </div>
</template>

<style scoped>
.multimodal-dataset-selector {
  width: 100%;
}

.search-wrapper {
  margin-top: 12px;
  display: flex;
}

.search-wrapper :deep(.el-radio) {
  margin-right: 12px;
}

.content-wrapper {
  margin-top: 12px;
}

.dataset-action-icon {
  width: 16px;
  height: 16px;
}
</style>
