<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { Edit } from '@element-plus/icons-vue'
import { ElButton, ElCheckbox, ElInput, ElTable, ElTableColumn } from 'element-plus'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { getDatasets } from '@/api/evaluations'
import type { EvaluationDataset } from '@/api/evaluations/types'
import { datasetText, evalBatchText, evalText } from '../evaluationFormLabels'

const modelValue = defineModel<number[]>({ default: [] })
const packages = defineModel<string[]>('packages', { default: [] })

const props = defineProps<{
  completion?: boolean
}>()

const emit = defineEmits<{
  completed: [value: boolean]
  mounted: []
}>()

const filterText = ref('')
const multipleTableRef = ref<InstanceType<typeof ElTable>>()
const multipleSelection = ref<EvaluationDataset[]>([])
const category = reactive({
  zh: false,
  en: false,
  leaderboard: false
})
const zhIndeterminate = ref(false)
const enIndeterminate = ref(false)
const leaderboardIndeterminate = ref(false)

const { data: datasets, isLoading } = useQuery({
  queryKey: ['evaluation-nlp-datasets'],
  queryFn: getDatasets
})

const fullDatasets = computed(() =>
  (datasets.value || []).filter((dataset) => dataset.domain === 'N' && dataset.available !== false)
)

const filteredDatasets = computed(() => {
  const lowerText = filterText.value.trim().toLowerCase()
  if (!lowerText) {
    return fullDatasets.value
  }

  return fullDatasets.value.filter((dataset) =>
    [dataset.label, dataset.name].some((value) => (value || '').toLowerCase().includes(lowerText))
  )
})

const selectedDatasets = computed(() =>
  fullDatasets.value.filter((dataset) => modelValue.value.includes(dataset.id))
)

const zhDatasets = computed(() => fullDatasets.value.filter((dataset) => dataset.language === 'zh'))
const enDatasets = computed(() => fullDatasets.value.filter((dataset) => dataset.language === 'en'))
const leaderboardDatasets = computed(() =>
  fullDatasets.value.filter((dataset) => dataset.leaderboard)
)

const languageLabel = (language?: string) => {
  const map: Record<string, string> = {
    zh: datasetText.zh,
    en: datasetText.en
  }
  return language ? map[language] || language : '-'
}

const sameIds = (left: number[], right: number[]) => {
  if (left.length !== right.length) {
    return false
  }

  const rightIds = new Set(right)
  return left.every((id) => rightIds.has(id))
}

const toggleSelection = (rows?: EvaluationDataset[], selected?: boolean) => {
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

const handleCheck = (rows: EvaluationDataset[], selected: boolean) => {
  toggleSelection(rows, selected)
}

const handleSelectionChange = (value: EvaluationDataset[]) => {
  multipleSelection.value = value
  modelValue.value = value.map((dataset) => dataset.id)
  packages.value = Array.from(
    new Set(value.map((dataset) => dataset.package).filter(Boolean) as string[])
  )

  const zhSelectedCount = value.filter((dataset) => dataset.language === 'zh').length
  const enSelectedCount = value.filter((dataset) => dataset.language === 'en').length
  const leaderboardSelectedCount = value.filter((dataset) => dataset.leaderboard).length

  category.zh = zhDatasets.value.length > 0 && zhSelectedCount === zhDatasets.value.length
  category.en = enDatasets.value.length > 0 && enSelectedCount === enDatasets.value.length
  category.leaderboard =
    leaderboardDatasets.value.length > 0 &&
    leaderboardSelectedCount === leaderboardDatasets.value.length

  zhIndeterminate.value = zhSelectedCount > 0 && zhSelectedCount < zhDatasets.value.length
  enIndeterminate.value = enSelectedCount > 0 && enSelectedCount < enDatasets.value.length
  leaderboardIndeterminate.value =
    leaderboardSelectedCount > 0 && leaderboardSelectedCount < leaderboardDatasets.value.length
}

const handleClickConfirm = () => {
  if (!modelValue.value.length || packages.value.length > 1) {
    return
  }
  emit('completed', true)
}

const handleClickEdit = async () => {
  emit('completed', false)
  await toggleRowSelection()
}

watch(
  () => datasets.value,
  async () => {
    await toggleRowSelection()
    emit('mounted')
  },
  { once: true }
)

watch(
  () => modelValue.value,
  async (value) => {
    if (
      sameIds(
        value,
        multipleSelection.value.map((dataset) => dataset.id)
      )
    ) {
      return
    }
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
</script>

<template>
  <div v-loading="isLoading" class="nlp-dataset-selector" element-loading-text="Loading...">
    <template v-if="!props.completion">
      <div v-if="false" class="cata-wrapper">
        <ElCheckbox
          v-model="category.zh"
          :indeterminate="zhIndeterminate"
          :disabled="zhDatasets.length === 0"
          @change="(value) => handleCheck(zhDatasets, Boolean(value))"
        >
          {{ datasetText.zh }}
        </ElCheckbox>
        <ElCheckbox
          v-model="category.en"
          :indeterminate="enIndeterminate"
          :disabled="enDatasets.length === 0"
          @change="(value) => handleCheck(enDatasets, Boolean(value))"
        >
          {{ datasetText.en }}
        </ElCheckbox>
        <ElCheckbox
          v-model="category.leaderboard"
          :indeterminate="leaderboardIndeterminate"
          :disabled="leaderboardDatasets.length === 0"
          @change="(value) => handleCheck(leaderboardDatasets, Boolean(value))"
        >
          {{ evalText.leaderboardDatasets || 'Listed Datasets' }}
        </ElCheckbox>
      </div>
      <div class="search-wrapper w-full">
        <ElInput
          v-model="filterText"
          :placeholder="evalText.searchDatasets || 'Search for dataset name'"
          class="flex-1"
          clearable
          size="large"
        />
        <ElButton
          size="large"
          type="primary"
          class="ml-[12px]"
          :title="evalText.clickConfirm || 'Click to confirm'"
          @click="handleClickConfirm"
        >
          {{ evalText.datasetConfirm || 'Confirmation' }}
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
          <ElTableColumn :label="evalText.language || 'Types'" property="language" width="100">
            <template #default="{ row }">{{ languageLabel(row.language) }}</template>
          </ElTableColumn>
          <ElTableColumn property="label" :label="evalBatchText.datasetName" />
          <ElTableColumn property="package" :label="evalText.system || 'Evaluation System'" />
          <ElTableColumn property="descriptionEn" :label="evalBatchText.datasetDesc" />
        </ElTable>
      </div>
    </template>

    <template v-else>
      <div class="cata-wrapper flex">
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
          <ElTableColumn :label="evalText.language || 'Types'" property="language" width="90">
            <template #default="{ row }">{{ languageLabel(row.language) }}</template>
          </ElTableColumn>
          <ElTableColumn property="label" :label="evalBatchText.datasetName" />
          <ElTableColumn property="package" :label="evalText.system || 'Evaluation System'" />
          <ElTableColumn property="descriptionEn" :label="evalBatchText.datasetDesc" />
        </ElTable>
      </div>
    </template>
  </div>
</template>

<style scoped>
.nlp-dataset-selector {
  width: 100%;
}

.search-wrapper {
  margin-top: 12px;
  display: flex;
}

.content-wrapper {
  margin-top: 12px;
}

.dataset-action-icon {
  width: 16px;
  height: 16px;
}
</style>
