<script setup lang="ts">
import { ElCollapse, ElSkeleton } from 'element-plus'
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { getMultimodalDatasets } from '@/api/evaluations'
import type { MultimodalDatasetGroup } from '@/api/evaluations/types'
import MultimodalDatasetOption from './MultimodalDatasetOption.vue'

const datasetsModel = defineModel<string[]>('datasets', { default: () => [] })
const idsModel = defineModel<number[]>('ids', { default: () => [] })

const props = defineProps<{
  status?: Record<string, string | number | undefined>
  staff?: boolean
}>()

const emit = defineEmits<{
  all: [datasets: MultimodalDatasetGroup[]]
}>()

const scenarios = ref<MultimodalDatasetGroup[]>([])
const checkedScenarios = reactive<Record<string, string[] | undefined>>({})

const selectedDatasets = computed(() => datasetsModel.value || [])

const updateModelValue = () => {
  const datasetsObj = selectedDatasets.value.map((item) => JSON.parse(item))
  idsModel.value.forEach((item) => {
    const scenario = scenarios.value.find((candidate) => Number(candidate.id) === Number(item))
    const selected = scenario?.data.filter((dataset) =>
      datasetsObj.some((selectedDataset) => selectedDataset.datasetShow === dataset.datasetShow)
    )
    checkedScenarios[item] =
      selected && selected.length > 0
        ? selected.map((dataset) => JSON.stringify(dataset))
        : undefined
  })
}

const loadDatasets = async () => {
  const response = await getMultimodalDatasets()
  scenarios.value = response.map((item) => ({
    ...item,
    data: item.data.filter((dataset) => (dataset?.is_admin ? props.staff : true))
  }))
  emit('all', scenarios.value)
  updateModelValue()
}

onBeforeMount(() => {
  void loadDatasets()
})

watch(
  selectedDatasets,
  (value, oldValue) => {
    const next = [...(value || [])].sort().join(',')
    const previous = [...(oldValue || [])].sort().join(',')
    if (next === previous) {
      return
    }
    updateModelValue()
  },
  { deep: true }
)

watch(
  checkedScenarios,
  (value) => {
    const datasets = Object.values(value).flatMap((item) => item || [])
    datasetsModel.value = datasets
    idsModel.value = Object.entries(value).flatMap(([key, selected]) =>
      selected && selected.length > 0 ? [Number(key)] : []
    )
  },
  { deep: true }
)
</script>

<template>
  <ElCollapse v-if="scenarios.length" class="w-full">
    <MultimodalDatasetOption
      v-for="item in scenarios"
      :key="item.id"
      v-model="checkedScenarios[item.id]"
      :option="item"
      :status="status"
      :staff="staff"
    />
  </ElCollapse>
  <ElSkeleton v-else :rows="2" animated />
</template>
