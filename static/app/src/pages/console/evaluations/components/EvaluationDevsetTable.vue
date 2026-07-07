<script setup lang="ts">
import { ElEmpty, ElTable, ElTableColumn } from 'element-plus'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getEvaluationBatchResults } from '@/api/evaluations'

const props = defineProps<{
  evaluationId: string | number
  batchId?: string | number
  active: string
}>()

const loading = ref(false)
const rows = ref<Record<string, unknown>[]>([])
const { t } = useI18n()

const flattenDetails = (value: unknown): Record<string, unknown>[] => {
  if (!Array.isArray(value)) {
    return []
  }

  return value.flatMap((item) => {
    const details = (item as { details?: unknown }).details
    return Array.isArray(details) ? (details as Record<string, unknown>[]) : []
  })
}

const loadResults = async () => {
  if (!props.batchId || props.active !== 'checkInference') {
    rows.value = []
    return
  }

  loading.value = true
  try {
    const response = await getEvaluationBatchResults({
      evaluationId: props.evaluationId,
      batchId: props.batchId
    })
    rows.value = flattenDetails(response.results)
  } finally {
    loading.value = false
  }
}

const tableRows = computed(() => rows.value)

const formatCompletions = (items?: Array<{ text?: string }>) => {
  return items?.map((item) => item.text || '').join('\n') || ''
}

watch(() => [props.batchId, props.active], loadResults, { immediate: true })
</script>

<template>
  <div class="devset-table">
    <div class="description mb-[12px]">
      {{ t('evaluationBatch.dryRunResultDescription') }}
    </div>
    <ElTable v-if="loading || tableRows.length" v-loading="loading" stripe :data="tableRows">
      <ElTableColumn type="index" label="ID" width="60" />
      <ElTableColumn :label="t('evaluationBatch.dataset')" width="130">
        <template #default="{ row }">
          <span class="predict">{{ row.taskId || row.datasetId || '-' }}</span>
          <span v-if="row.disturbance" class="predict">-{{ row.disturbance }}</span>
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('evaluationBatch.sample')" min-width="300">
        <template #default="{ row }">
          <pre class="sample">{{
            row.states?.[0]?.request?.prompt || row.prompt || row.input || '-'
          }}</pre>
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('evaluationBatch.label')" min-width="180">
        <template #default="{ row }">
          <pre class="predict">{{ row.states?.[0]?.golds?.join('\n') || row.label || '-' }}</pre>
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('evaluationBatch.predict')" min-width="220">
        <template #default="{ row }">
          <pre class="predict">{{
            formatCompletions(row.states?.[0]?.response?.completions) ||
            row.predict ||
            row.output ||
            '-'
          }}</pre>
        </template>
      </ElTableColumn>
    </ElTable>
    <ElEmpty v-else :description="t('common.empty')" />
  </div>
</template>

<style scoped>
.description {
  color: #7f8499;
  font-size: 14px;
}

.sample {
  font-size: 12px;
  white-space: break-spaces;
}

.predict {
  font-size: 12px;
  white-space: pre-line;
}

.devset-table :deep(.el-table .el-table__cell) {
  vertical-align: top;
}
</style>
