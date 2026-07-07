<script setup lang="ts">
import { ElTable, ElTableColumn, ElText } from 'element-plus'
import { useI18n } from 'vue-i18n'

defineProps<{
  tableData: Array<Record<string, unknown>>
  loading?: boolean
  type: 'content' | 'format'
}>()

const { t } = useI18n()

const toPercentageNumber = (value: number) => {
  if (!Number.isFinite(value)) {
    return '-'
  }

  return `${(value * 100).toFixed(2)}%`
}

const spanMethod = ({ row, columnIndex }: { row: Record<string, number>; columnIndex: number }) => {
  const keys = ['scenarioRowspan', 'datasetRowspan', 'accuracyRowspan', '', '', 'rbAccRowspan']
  const key = keys[columnIndex]
  if (!key) {
    return undefined
  }

  const rowspan = row[key]
  return rowspan > 0 ? { rowspan, colspan: 1 } : { rowspan: 0, colspan: 0 }
}
</script>

<template>
  <div>
    <p class="mb-[16px] ml-[12px]">
      <ElText type="primary" size="small">
        {{ t('evaluationBatch.nlpRobustnessTip') }}
      </ElText>
    </p>
    <ElTable
      v-if="tableData && tableData.length > 0"
      v-loading="loading"
      :data="tableData"
      border
      style="width: 100%"
      :span-method="spanMethod"
      size="small"
    >
      <ElTableColumn prop="scenarioLabel" :label="t('evaluationBatch.taskName')" />
      <ElTableColumn prop="datasetLabel" :label="t('evaluationBatch.datasetName')" />
      <ElTableColumn
        prop="accuracy"
        :label="t('evaluationBatch.accuracy')"
        :width="type === 'content' ? 100 : undefined"
        align="center"
      >
        <template #default="{ row }">
          <ElText type="primary" size="small" style="font-weight: 500">
            {{ toPercentageNumber(Number(row.accuracy)) }}
          </ElText>
        </template>
      </ElTableColumn>
      <ElTableColumn prop="disturbanceLabel" :label="t('evaluationBatch.disturbance')" />
      <ElTableColumn
        prop="metric"
        :label="t('evaluationBatch.indicatorValue')"
        align="center"
        width="120"
      >
        <template #default="{ row }">
          <ElText type="primary" size="small">
            {{ toPercentageNumber(Number(row.metric)) }}
          </ElText>
        </template>
      </ElTableColumn>
      <ElTableColumn prop="rbAcc" :label="t('evaluationBatch.rbAcc')" align="center">
        <template #default="{ row }">
          <ElText type="primary" size="small">
            {{ toPercentageNumber(Number(row.rbAcc)) }}
          </ElText>
        </template>
      </ElTableColumn>
    </ElTable>
  </div>
</template>
