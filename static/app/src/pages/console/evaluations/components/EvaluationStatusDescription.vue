<script setup lang="ts">
import { ElTable, ElTableColumn, ElText } from 'element-plus'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type {
  EvaluationBatchStatus,
  EvaluationDag,
  EvaluationDataset
} from '@/api/evaluations/types'
import { batchStatusTitle, batchStatusType, RUNNING_STATUS } from './batchConstants'
import BlockTitle from './BlockTitle.vue'

const props = defineProps<{
  dags: EvaluationDag[]
  datasets: EvaluationDataset[]
  check?: boolean
}>()

const { t } = useI18n()

const languageLabel = (language?: string) => {
  const map: Record<string, string> = {
    en: t('evaluation.english'),
    zh: t('evaluation.chinese')
  }

  return language ? map[language] || language : '-'
}

const taskLabel = (dataset?: EvaluationDataset) => {
  return dataset?.label || dataset?.scenario || dataset?.task || dataset?.key || '-'
}

const aggregateDatasetStatus = (dags: EvaluationDag[]): EvaluationBatchStatus => {
  if (!dags.length) {
    return 'default'
  }

  if (dags.some((dag) => dag.status === 'F')) {
    return 'F'
  }

  if (dags.some((dag) => dag.status === 'C')) {
    return 'C'
  }

  const running = dags.find((dag) => dag.status && RUNNING_STATUS.includes(dag.status))
  if (running?.status) {
    return running.status
  }

  if (dags.every((dag) => dag.status === 'S')) {
    return 'S'
  }

  return dags[0]?.status || 'default'
}

const formatDate = (value?: string | number) => {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
    .format(new Date(value))
    .replace(/\//g, '-')
}

const datasetRows = computed(() => {
  return props.datasets
    .map((dataset) => {
      const relatedDags = props.dags.filter(
        (dag) => dag.datasetId === dataset.id && !dag.disturbance
      )
      if (!relatedDags.length) {
        return undefined
      }

      const startedAt = relatedDags
        .map((dag) => dag.startedAt)
        .filter((value): value is string | number => Boolean(value))
        .sort()[0]
      const stoppedAt = relatedDags
        .map((dag) => dag.stoppedAt)
        .filter((value): value is string | number => Boolean(value))
        .sort()
        .at(-1)

      return {
        id: dataset.id,
        language: languageLabel(dataset.language),
        taskName: taskLabel(dataset),
        datasetName: dataset.name || dataset.key || dataset.id,
        status: aggregateDatasetStatus(relatedDags),
        start: formatDate(startedAt),
        stop: formatDate(stoppedAt)
      }
    })
    .filter((row): row is NonNullable<typeof row> => Boolean(row))
})

const disturbanceRows = (group: 'C' | 'F') => {
  return props.datasets.flatMap((dataset) => {
    const disturbances = (dataset.disturbances || []).filter((item) =>
      group === 'F' ? item.group === 'F' : item.group !== 'F'
    )

    return disturbances.flatMap((disturbance) => {
      const dag = props.dags.find(
        (item) => item.datasetId === dataset.id && item.disturbance === disturbance.name
      )
      if (!dag) {
        return []
      }

      return [
        {
          language: languageLabel(dataset.language),
          taskName: taskLabel(dataset),
          datasetName: dataset.name || dataset.key || dataset.id,
          disturbance: disturbance.label || disturbance.name,
          status: dag.status || 'default',
          start: formatDate(dag.startedAt),
          stop: formatDate(dag.stoppedAt)
        }
      ]
    })
  })
}

const robContentRows = computed(() => disturbanceRows('C'))
const robFormatRows = computed(() => disturbanceRows('F'))
</script>

<template>
  <div class="status-description">
    <BlockTitle v-if="!check" class="mb-[16px]">
      {{ t('evaluationBatch.accuracyEvaluation') }}
    </BlockTitle>

    <ElTable :data="datasetRows" border style="width: 100%" flexible>
      <ElTableColumn :label="t('evaluation.types')" width="100">
        <template #default="{ row }">{{ row.language }}</template>
      </ElTableColumn>
      <ElTableColumn :label="t('evaluationBatch.taskName')" width="180">
        <template #default="{ row }">{{ row.taskName }}</template>
      </ElTableColumn>
      <ElTableColumn
        prop="datasetName"
        :label="t('evaluationBatch.datasetName')"
        width="150"
        show-overflow-tooltip
      />
      <ElTableColumn :label="t('common.status')">
        <template #default="{ row }">
          <ElText :type="batchStatusType(row.status)">
            {{ batchStatusTitle(row.status) }}
          </ElText>
        </template>
      </ElTableColumn>
      <ElTableColumn v-if="!check" :label="t('evaluationBatch.startAt')">
        <template #default="{ row }">{{ row.start }}</template>
      </ElTableColumn>
      <ElTableColumn v-if="!check" :label="t('evaluationBatch.stopAt')">
        <template #default="{ row }">{{ row.stop }}</template>
      </ElTableColumn>
    </ElTable>

    <template v-if="!check">
      <BlockTitle class="my-[16px]">
        {{ t('evaluationBatch.robustnessContentScrambling') }}
      </BlockTitle>
      <ElTable
        v-if="robContentRows.length"
        :data="robContentRows"
        border
        style="width: 100%"
        flexible
      >
        <ElTableColumn :label="t('evaluation.types')" width="100">
          <template #default="{ row }">{{ row.language }}</template>
        </ElTableColumn>
        <ElTableColumn :label="t('evaluationBatch.taskName')" width="180">
          <template #default="{ row }">{{ row.taskName }}</template>
        </ElTableColumn>
        <ElTableColumn
          prop="datasetName"
          :label="t('evaluationBatch.datasetName')"
          show-overflow-tooltip
        />
        <ElTableColumn
          prop="disturbance"
          :label="t('evaluationBatch.disturbance')"
          show-overflow-tooltip
        />
        <ElTableColumn :label="t('common.status')">
          <template #default="{ row }">
            <ElText :type="batchStatusType(row.status)">
              {{ batchStatusTitle(row.status) }}
            </ElText>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="t('evaluationBatch.startAt')">
          <template #default="{ row }">{{ row.start }}</template>
        </ElTableColumn>
        <ElTableColumn :label="t('evaluationBatch.stopAt')">
          <template #default="{ row }">{{ row.stop }}</template>
        </ElTableColumn>
      </ElTable>

      <BlockTitle class="my-[16px]">
        {{ t('evaluationBatch.robustnessFormatScrambling') }}
      </BlockTitle>
      <ElTable
        v-if="robFormatRows.length"
        :data="robFormatRows"
        border
        style="width: 100%"
        flexible
      >
        <ElTableColumn :label="t('evaluation.types')" width="100">
          <template #default="{ row }">{{ row.language }}</template>
        </ElTableColumn>
        <ElTableColumn :label="t('evaluationBatch.taskName')" width="180">
          <template #default="{ row }">{{ row.taskName }}</template>
        </ElTableColumn>
        <ElTableColumn
          prop="datasetName"
          :label="t('evaluationBatch.datasetName')"
          show-overflow-tooltip
        />
        <ElTableColumn
          prop="disturbance"
          :label="t('evaluationBatch.disturbance')"
          show-overflow-tooltip
        />
        <ElTableColumn :label="t('common.status')">
          <template #default="{ row }">
            <ElText :type="batchStatusType(row.status)">
              {{ batchStatusTitle(row.status) }}
            </ElText>
          </template>
        </ElTableColumn>
        <ElTableColumn :label="t('evaluationBatch.startAt')">
          <template #default="{ row }">{{ row.start }}</template>
        </ElTableColumn>
        <ElTableColumn :label="t('evaluationBatch.stopAt')">
          <template #default="{ row }">{{ row.stop }}</template>
        </ElTableColumn>
      </ElTable>
    </template>
  </div>
</template>

<style scoped>
.status-description {
  width: 100%;
}
</style>
