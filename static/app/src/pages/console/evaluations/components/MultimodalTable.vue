<script setup lang="ts">
import { ElButton, ElEmpty, ElSkeleton, ElTable, ElTableColumn, ElText } from 'element-plus'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationBatchResults } from '@/api/evaluations'
import { multimodalStatusTitle, multimodalStatusType } from './batchConstants'
import BlockTitle from './BlockTitle.vue'
import MmTree from './MmTree.vue'
import { multimodalTaskName } from './multimodalLabels'

const props = defineProps<{
  evaluationId: string | number
  batchId?: string | number
  active?: string
  submitted?: boolean
}>()

const results = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const { t } = useI18n()

const showEvaluationDetail = computed(() => props.active !== 'checkInference')
const accuracyResults = computed(() => results.value.filter((item) => item.lbx !== 1))
const displayRows = computed(() =>
  showEvaluationDetail.value ? accuracyResults.value : results.value
)
const robustnessResults = computed(() => {
  const grouped: Record<string, Record<string, Record<string, unknown>[]>> = {}

  results.value
    .filter((item) => item.lbx === 1)
    .forEach((item) => {
      const task = multimodalTaskName(item.name)
      const dataset = String(item.parent || item.dataset || '-')
      grouped[task] = grouped[task] || {}
      grouped[task][dataset] = grouped[task][dataset] || []
      grouped[task][dataset].push(item)
    })

  return grouped
})

const hasRobustnessResults = computed(() =>
  Object.values(robustnessResults.value).some((datasets) => Object.keys(datasets).length > 0)
)

const metricData = (row: Record<string, unknown>) => {
  const data = row.data as { data?: unknown } | undefined
  return data?.data || row.details || {}
}

const rowDataValue = (row: Record<string, unknown>, key: string) => {
  const data = row.data as Record<string, unknown> | undefined
  return data?.[key]
}

const formatDate = (value: unknown) => (value ? String(value) : '-')

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
    results.value = (response.results || []) as unknown as Record<string, unknown>[]
  } finally {
    loading.value = false
  }
}

watch(() => props.batchId, loadResults, { immediate: true })
</script>

<template>
  <div class="multimodal-result-table">
    <div v-if="false" class="mb-[16px] text-right">
      <ElButton type="primary" :disabled="submitted">
        {{ t('evaluationBatch.submitToLeaderboard') }}
      </ElButton>
    </div>
    <ElSkeleton :rows="6" animated :throttle="0" :loading="loading">
      <template #default>
        <ElEmpty v-if="!results.length" :description="t('common.empty')" />
        <template v-else>
          <BlockTitle v-if="showEvaluationDetail" class="mb-[16px]">
            {{ t('evaluationBatch.accuracyEvaluation') }}
          </BlockTitle>
          <ElTable stripe :data="displayRows" size="small" border>
            <ElTableColumn :label="t('evaluationBatch.task')">
              <template #default="{ row }">
                <ElText size="small" type="info">{{ multimodalTaskName(row.name) }}</ElText>
              </template>
            </ElTableColumn>
            <ElTableColumn :label="t('evaluationBatch.dataset')">
              <template #default="{ row }">
                <ElText size="small" type="info">{{ row.dataset || row.datasetKey || '-' }}</ElText>
              </template>
            </ElTableColumn>
            <ElTableColumn :label="t('common.status')">
              <template #default="{ row }">
                <ElText :type="multimodalStatusType(String(row.status ?? ''))" size="small">
                  {{ multimodalStatusTitle(String(row.status ?? '')) }}
                </ElText>
              </template>
            </ElTableColumn>
            <ElTableColumn
              v-if="showEvaluationDetail"
              :label="`${t('evaluationBatch.indicator')} & ${t('evaluationBatch.value')}`"
              width="295"
              header-align="center"
            >
              <template #default="{ row }">
                <MmTree :tree-data="metricData(row)" />
              </template>
            </ElTableColumn>
            <ElTableColumn :label="t('evaluationBatch.startTime')" show-overflow-tooltip>
              <template #default="{ row }">
                <ElText size="small" type="info">{{
                  formatDate(rowDataValue(row, 'starttime'))
                }}</ElText>
              </template>
            </ElTableColumn>
            <ElTableColumn :label="t('evaluationBatch.stopTime')" show-overflow-tooltip>
              <template #default="{ row }">
                <ElText size="small" type="info">{{
                  formatDate(rowDataValue(row, 'endtime'))
                }}</ElText>
              </template>
            </ElTableColumn>
          </ElTable>
        </template>
        <template v-if="showEvaluationDetail && results.length">
          <BlockTitle class="my-[16px]">
            {{ t('evaluationBatch.robustnessEvaluation') }}
          </BlockTitle>
          <p class="mb-[16px] ml-[12px]">
            <ElText type="primary" size="small">
              {{ t('evaluationBatch.robustnessTip') }}
            </ElText>
          </p>
          <template v-if="hasRobustnessResults">
            <template v-for="(datasets, task) in robustnessResults" :key="task">
              <template v-for="(list, dataset) in datasets" :key="dataset">
                <ElTable stripe :data="list" size="small" border class="mb-[8px]">
                  <ElTableColumn :label="t('evaluationBatch.task')">
                    <template #default>
                      <ElText size="small" type="info">{{ task }}</ElText>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="t('evaluationBatch.dataset')">
                    <template #default>
                      <ElText size="small" type="info">{{ dataset }}</ElText>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="t('common.status')">
                    <template #default="{ row }">
                      <ElText :type="multimodalStatusType(String(row.status ?? ''))" size="small">
                        {{ multimodalStatusTitle(String(row.status ?? '')) }}
                      </ElText>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn
                    :label="`${t('evaluationBatch.indicator')} & ${t('evaluationBatch.value')}`"
                    width="295"
                    header-align="center"
                  >
                    <template #default="{ row }">
                      <MmTree :tree-data="metricData(row)" />
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="t('evaluationBatch.startTime')" show-overflow-tooltip>
                    <template #default="{ row }">
                      <ElText size="small" type="info">
                        {{ formatDate(rowDataValue(row, 'starttime')) }}
                      </ElText>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn :label="t('evaluationBatch.stopTime')" show-overflow-tooltip>
                    <template #default="{ row }">
                      <ElText size="small" type="info">
                        {{ formatDate(rowDataValue(row, 'endtime')) }}
                      </ElText>
                    </template>
                  </ElTableColumn>
                </ElTable>
              </template>
            </template>
          </template>
        </template>
      </template>
    </ElSkeleton>
  </div>
</template>
