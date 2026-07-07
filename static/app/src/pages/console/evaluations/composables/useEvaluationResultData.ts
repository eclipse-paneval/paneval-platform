import { computed, type Ref } from 'vue'
import type { EvaluationBatchResult, EvaluationDataset } from '@/api/evaluations/types'

const toFixedMetric = (value: unknown) => {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? Number(numberValue.toFixed(4)) : 0
}

const taskLabel = (dataset?: EvaluationDataset) => {
  return dataset?.label || dataset?.scenario || dataset?.task || dataset?.key || '-'
}

export const useEvaluationResultData = (
  datasets: Ref<EvaluationDataset[]>,
  results: Ref<EvaluationBatchResult[]>
) => {
  const datasetsMap = computed(
    () => new Map(datasets.value.map((dataset) => [dataset.id, dataset]))
  )

  const accResults = computed(() => results.value.filter((item) => !item.disturbance))

  const accTableData = computed(() => {
    const rows: Array<Record<string, unknown>> = []
    const taskGroups = new Map<string, Array<Record<string, unknown>>>()

    accResults.value.forEach((result) => {
      ;(result.details || []).forEach((detail) => {
        const dataset = detail.datasetId ? datasetsMap.value.get(detail.datasetId) : undefined
        if (!dataset) {
          return
        }

        const taskName = taskLabel(dataset)
        if (!taskGroups.has(taskName)) {
          taskGroups.set(taskName, [])
        }

        taskGroups.get(taskName)?.push({
          taskName,
          datasetName: dataset.name || dataset.key || detail.datasetId,
          accuracy: toFixedMetric(detail.accuracy),
          mean: toFixedMetric(result.accuracy)
        })
      })
    })

    taskGroups.forEach((groupRows) => {
      groupRows.forEach((row, index) => {
        rows.push({
          ...row,
          rowspan: index === 0 ? groupRows.length : 0
        })
      })
    })

    return rows
  })

  const robustnessResults = computed(() => results.value.filter((item) => item.disturbance))

  const getCleanMetric = (
    datasetId: number,
    key: 'accuracy' | 'robustness',
    robType?: 'C' | 'F'
  ) => {
    for (const result of accResults.value) {
      const detail = result.details?.find((item) => item.datasetId === datasetId)
      if (!detail) {
        continue
      }

      if (key === 'robustness' && robType) {
        const robustnesses = detail.robustnesses as Record<string, number> | undefined
        return toFixedMetric(robustnesses?.[robType])
      }

      return toFixedMetric(detail[key])
    }

    return 0
  }

  const getDisturbanceMetric = (result: EvaluationBatchResult, datasetId: number) => {
    const detail = result.details?.find((item) => item.datasetId === datasetId)
    return toFixedMetric(detail?.accuracy)
  }

  const buildRobustnessTableData = (robType: 'C' | 'F') => {
    const rows: Array<Record<string, unknown>> = []

    datasets.value.forEach((dataset) => {
      const disturbances = (dataset.disturbances || []).filter((item) =>
        robType === 'F' ? item.group === 'F' : item.group !== 'F'
      )
      const datasetResults = robustnessResults.value.filter((result) => {
        return (
          disturbances.some((disturbance) => disturbance.name === result.disturbance) &&
          result.details?.some((detail) => detail.datasetId === dataset.id)
        )
      })

      datasetResults.forEach((result, index) => {
        const disturbance = disturbances.find((item) => item.name === result.disturbance)
        rows.push({
          scenarioLabel: index === 0 ? taskLabel(dataset) : '',
          datasetLabel: index === 0 ? dataset.name || dataset.key : '',
          accuracy: index === 0 ? getCleanMetric(dataset.id, 'accuracy') : '',
          disturbanceLabel: disturbance?.label || result.disturbance || '-',
          metric: getDisturbanceMetric(result, dataset.id),
          rbAcc: index === 0 ? getCleanMetric(dataset.id, 'robustness', robType) : '',
          scenarioRowspan: index === 0 ? datasetResults.length : 0,
          datasetRowspan: index === 0 ? datasetResults.length : 0,
          accuracyRowspan: index === 0 ? datasetResults.length : 0,
          rbAccRowspan: index === 0 ? datasetResults.length : 0
        })
      })
    })

    return rows
  }

  const robContentTableData = computed(() => buildRobustnessTableData('C'))
  const robFormatTableData = computed(() => buildRobustnessTableData('F'))

  return {
    accTableData,
    robContentTableData,
    robFormatTableData
  }
}
