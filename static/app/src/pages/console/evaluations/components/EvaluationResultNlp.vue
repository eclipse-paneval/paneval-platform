<script setup lang="ts">
import { ElButton, ElCol, ElEmpty, ElRow } from 'element-plus'
import { computed, ref, toRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationBatchResults } from '@/api/evaluations'
import type { EvaluationBatchResult, EvaluationDataset } from '@/api/evaluations/types'
import { useEvaluationResultData } from '../composables/useEvaluationResultData'
import AccuracyTable from './AccuracyTable.vue'
import BlockTitle from './BlockTitle.vue'
import RobustnessTable from './RobustnessTable.vue'

const props = defineProps<{
  evaluationId: string | number
  batchId?: string | number
  datasets: EvaluationDataset[]
  type?: string
  submitted?: boolean
}>()

const loading = ref(false)
const results = ref<EvaluationBatchResult[]>([])
const { t } = useI18n()

const { accTableData, robContentTableData, robFormatTableData } = useEvaluationResultData(
  toRef(props, 'datasets'),
  results
)

const hasResultData = computed(
  () =>
    accTableData.value.length > 0 ||
    robContentTableData.value.length > 0 ||
    robFormatTableData.value.length > 0
)

const loadResults = async () => {
  if (!props.batchId) {
    results.value = []
    return
  }

  loading.value = true
  try {
    const response = await getEvaluationBatchResults({
      evaluationId: props.evaluationId,
      batchId: props.batchId
    })
    results.value = response.results || []
  } finally {
    loading.value = false
  }
}

watch(() => props.batchId, loadResults, { immediate: true })
</script>

<template>
  <ElRow v-if="false" class="my-[30px]">
    <ElCol :span="24" class="text-right">
      <ElButton type="primary" :disabled="type !== 'success' || submitted">
        {{ t('evaluationBatch.submitToLeaderboard') }}
      </ElButton>
    </ElCol>
  </ElRow>

  <template v-if="loading || hasResultData">
    <BlockTitle class="my-[16px]">{{ t('evaluationBatch.accuracyEvaluation') }}</BlockTitle>
    <AccuracyTable :table-data="accTableData" :loading="loading" />

    <BlockTitle class="my-[16px]">
      {{ t('evaluationBatch.robustnessContentScrambling') }}
    </BlockTitle>
    <RobustnessTable :table-data="robContentTableData" :loading="loading" type="content" />

    <BlockTitle class="my-[16px]">
      {{ t('evaluationBatch.robustnessFormatScrambling') }}
    </BlockTitle>
    <RobustnessTable :table-data="robFormatTableData" :loading="loading" type="format" />
  </template>
  <ElEmpty v-else :description="t('common.empty')" />
</template>
