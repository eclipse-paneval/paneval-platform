<script setup lang="ts">
import { ElCheckbox, ElCheckboxGroup, ElCollapseItem } from 'element-plus'
import { computed, ref, watch } from 'vue'
import type { EvaluationDatasetConfig, MultimodalDatasetGroup } from '@/api/evaluations/types'

const modelValue = defineModel<string[]>({ default: () => [] })

const props = defineProps<{
  option: MultimodalDatasetGroup
  status?: Record<string, string | number | undefined>
  staff?: boolean
}>()

const checkAll = ref(false)
const isIndeterminate = ref(false)
const checkedDatasets = ref<string[]>([])

const datasetOptions = computed(() =>
  (props.option.data || []).filter((dataset) => (dataset?.is_admin ? props.staff : true))
)

const datasetKey = (dataset: EvaluationDatasetConfig) => JSON.stringify(dataset)

const datasetSucceeded = (dataset: EvaluationDatasetConfig) => {
  const status = props.status?.[datasetKey(dataset)]
  return status !== undefined && Number(status) === 1
}

const hasSuccessDataset = computed(() =>
  checkedDatasets.value.some(
    (item) => props.status?.[item] !== undefined && Number(props.status[item]) === 1
  )
)

const syncCheckState = (value: string[]) => {
  const checkedCount = value?.length || 0
  checkAll.value = checkedCount > 0 && checkedCount === datasetOptions.value.length
  isIndeterminate.value = checkedCount > 0 && checkedCount < datasetOptions.value.length
}

const handleCheckAllChange = (value: boolean) => {
  checkedDatasets.value = value ? datasetOptions.value.map(datasetKey) : []
  isIndeterminate.value = false
  modelValue.value = checkedDatasets.value
}

const handleCheckedChange = (value: Array<string | number | boolean>) => {
  const nextValue = value.map((item) => String(item))
  syncCheckState(nextValue)
  modelValue.value = nextValue
}

watch(
  modelValue,
  (value) => {
    const nextValue = value || []
    if (nextValue.join(',') === checkedDatasets.value.join(',')) {
      return
    }
    checkedDatasets.value = nextValue
    syncCheckState(nextValue)
  },
  { immediate: true }
)

watch(datasetOptions, () => syncCheckState(checkedDatasets.value))
</script>

<template>
  <ElCollapseItem :name="option.id">
    <template #title>
      <ElCheckbox
        v-model="checkAll"
        :indeterminate="isIndeterminate"
        :disabled="hasSuccessDataset"
        @change="(value) => handleCheckAllChange(Boolean(value))"
        @click.stop
      >
        <span class="flex items-center">{{ option.name }}</span>
      </ElCheckbox>
    </template>

    <ElCheckboxGroup v-model="checkedDatasets" @change="handleCheckedChange">
      <ElCheckbox
        v-for="dataset in datasetOptions"
        :key="dataset.datasetShow || dataset.dataset || dataset.id"
        :value="datasetKey(dataset)"
        :disabled="datasetSucceeded(dataset)"
      >
        {{ dataset.datasetShow || dataset.dataset || dataset.name }}
      </ElCheckbox>
    </ElCheckboxGroup>
  </ElCollapseItem>
</template>
