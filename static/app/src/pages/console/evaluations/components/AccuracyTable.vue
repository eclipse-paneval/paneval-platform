<script setup lang="ts">
import { ElTable, ElTableColumn, ElText } from 'element-plus'
import { useI18n } from 'vue-i18n'

defineProps<{
  tableData: Array<Record<string, unknown>>
  loading?: boolean
}>()

const { t } = useI18n()

const toPercentageNumber = (value: number) => {
  if (!Number.isFinite(value)) {
    return '-'
  }

  return `${(value * 100).toFixed(2)}%`
}
</script>

<template>
  <ElTable v-loading="loading" :data="tableData" border style="width: 100%" flexible size="small">
    <ElTableColumn prop="taskName" :label="t('evaluationBatch.taskName')" />
    <ElTableColumn prop="datasetName" :label="t('evaluationBatch.datasetName')" />
    <ElTableColumn prop="accuracy" :label="t('evaluationBatch.indicatorValueAccuracy')">
      <template #default="{ row }">
        <ElText type="primary" size="small">
          {{ toPercentageNumber(Number(row.accuracy)) }}
        </ElText>
      </template>
    </ElTableColumn>
  </ElTable>
</template>
