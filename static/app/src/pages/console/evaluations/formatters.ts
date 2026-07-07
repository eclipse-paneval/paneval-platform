import type {
  EvaluationDataset,
  EvaluationDatasetConfig,
  EvaluationDomain
} from '@/api/evaluations/types'

export const sceneLabel = (scene?: string) => {
  const map: Record<string, string> = {
    EA: 'Online evaluation',
    EM: 'Offline evaluation'
  }

  return scene ? map[scene] || scene : '-'
}

export const domainLabel = (domain: EvaluationDomain) => {
  const map: Record<string, string> = {
    N: 'NLP',
    C: 'CV',
    CV: 'CV',
    M: 'Multimodal',
    MM: 'Multimodal',
    A: 'Audio',
    AUDIO: 'Audio',
    S: 'Innovation',
    SF: 'Safety',
    SAFETY: 'Safety'
  }

  return map[domain] || domain || '-'
}

const safetyDatasetLabels: Record<string, string> = {
  'A.1': 'Violation of Core Values',
  'A.2': 'Discriminatory Content',
  'A.3': 'Commercial Violations and Illegal Practices',
  'A.4': 'Infringement of Others’ Legal Rights',
  'A.5': 'Failure to Meet Service-Specific Safety Requirements',
  总体评估: 'Overall'
}

const datasetLabel = (dataset: EvaluationDataset) => {
  if (['SF', 'SAFETY'].includes(dataset.domain)) {
    return (
      safetyDatasetLabels[dataset.name || ''] ||
      dataset.name ||
      dataset.description ||
      dataset.label ||
      dataset.scenario ||
      String(dataset.id)
    )
  }

  return dataset.name || dataset.label || dataset.scenario || String(dataset.id)
}

export const buildDatasetLabelMap = (datasets: EvaluationDataset[] = []) => {
  return new Map(datasets.map((dataset) => [dataset.id, datasetLabel(dataset)]))
}

export const datasetLabels = (
  datasetIds: number[] = [],
  datasetMap: Map<number, string>,
  datasetsConfig?: EvaluationDatasetConfig[]
) => {
  if (datasetsConfig?.length) {
    return datasetsConfig.map(
      (dataset) => dataset.datasetShow || dataset.name || dataset.dataset || '-'
    )
  }

  return datasetIds.map((id) => datasetMap.get(id) || String(id))
}

export const datasetSummary = (
  datasetIds: number[] = [],
  datasetMap: Map<number, string>,
  datasetsConfig?: EvaluationDatasetConfig[]
) => {
  const labels = datasetLabels(datasetIds, datasetMap, datasetsConfig)
  return labels.length ? labels.join(', ') : '-'
}
