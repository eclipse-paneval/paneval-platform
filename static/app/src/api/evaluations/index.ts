import { httpClient } from '@/api/client'
import type {
  EvaluationDataset,
  EvaluationBatchResponse,
  EvaluationBatchResultResponse,
  EvaluationBatchLogResponse,
  EvaluationDetail,
  EvaluationDag,
  EvaluationImageResponse,
  EvaluationListParams,
  EvaluationListResponse,
  EvaluationPayload,
  EvaluationQueueResponse,
  EvaluationResourceResponse,
  CustomImageResponse,
  MultimodalDatasetGroup,
  PaginatedEvaluationResponse
} from './types'

const compactParams = (params: Record<string, unknown>) => {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== '')
  )
}

export const getEvaluations = async ({
  pageIndex: page,
  pageSize,
  me,
  createUser,
  modelName,
  domain,
  specialEvent
}: EvaluationListParams = {}): Promise<EvaluationListResponse> => {
  const response = await httpClient.get<PaginatedEvaluationResponse>('/evaluations/', {
    params: compactParams({ page, pageSize, me, createUser, modelName, domain, specialEvent })
  })

  return {
    total: response.data.count,
    list: response.data.results
  }
}

export const removeEvaluation = async (id: string | number) => {
  await httpClient.delete(`/evaluations/${id}`)
}

export const getDatasets = async (): Promise<EvaluationDataset[]> => {
  const response = await httpClient.get<EvaluationDataset[]>('/evaluations/datasets', {
    params: {}
  })

  return response.data
}

export const getMultimodalDatasets = async (): Promise<MultimodalDatasetGroup[]> => {
  const response = await httpClient.get<MultimodalDatasetGroup[]>('/evaluations/mmdata', {
    params: {}
  })

  return response.data
}

export const createEvaluation = async (payload: EvaluationPayload) => {
  const response = await httpClient.post('/evaluations/', payload)

  return response.data
}

export const getEvaluation = async (id: string | number): Promise<EvaluationDetail> => {
  const response = await httpClient.get<EvaluationDetail>(`/evaluations/${id}`)

  return response.data
}

export const updateEvaluation = async (id: string | number, payload: EvaluationPayload) => {
  const response = await httpClient.patch(`/evaluations/${id}`, payload)

  return response.data
}

export const getEvaluationImages = async (page: number, pageSize: number) => {
  const response = await httpClient.get<EvaluationImageResponse>('/evaluations/images', {
    params: { page, pageSize }
  })

  return response.data
}

export const getCustomImages = async ({
  page,
  pageSize,
  status = 'R'
}: {
  page: number
  pageSize: number
  status?: string
}) => {
  const response = await httpClient.get<CustomImageResponse>('/images/', {
    params: { page, pageSize, status }
  })

  return response.data
}

export const getEvaluationQueues = async (page: number, pageSize: number) => {
  const response = await httpClient.get<EvaluationQueueResponse>('/evaluations/queues', {
    params: { page, pageSize }
  })

  return response.data
}

export const getEvaluationQueueResources = async ({
  page,
  pageSize,
  id
}: {
  page: number
  pageSize: number
  id: string | number
}) => {
  const response = await httpClient.get<EvaluationResourceResponse>(
    `/evaluations/queues/${id}/resources`,
    {
      params: { page, pageSize }
    }
  )

  return response.data
}

export const createTokenizerUpload = async () => {
  const response = await httpClient.post<{ id: string | number }>('/evaluations/tokenizers')

  return response.data
}

export const getEvaluationBatches = async ({
  evaluationId,
  page = 1
}: {
  evaluationId: string | number
  page?: string | number
}) => {
  const response = await httpClient.get<EvaluationBatchResponse>(
    `/evaluations/${evaluationId}/batches/`,
    {
      params: { page }
    }
  )

  return response.data
}

export const runEvaluationBatch = async ({
  evaluationId,
  dryRun,
  resource,
  priority
}: {
  evaluationId: string | number
  dryRun?: boolean
  resource?: unknown
  priority?: string
}) => {
  const response = await httpClient.post(
    `/evaluations/${evaluationId}/batches/`,
    compactParams({ dryRun, resource, priority })
  )

  return response.data
}

export const getEvaluationBatchDags = async ({
  evaluationId,
  batchId
}: {
  evaluationId: string | number
  batchId: string | number
}) => {
  const response = await httpClient.get<EvaluationDag[]>(
    `/evaluations/${evaluationId}/batches/${batchId}/dags`
  )

  return response.data
}

export const getEvaluationBatchResults = async ({
  evaluationId,
  batchId
}: {
  evaluationId: string | number
  batchId: string | number
}) => {
  const response = await httpClient.get<EvaluationBatchResultResponse>(
    `/evaluations/${evaluationId}/batches/${batchId}/results`
  )

  return response.data
}

export const stopEvaluationBatch = async ({
  evaluationId,
  batchId
}: {
  evaluationId: string | number
  batchId: string | number
}) => {
  await httpClient.delete(`/evaluations/${evaluationId}/batches/${batchId}`)
}

export const continueEvaluationBatch = async ({
  evaluationId,
  batchId
}: {
  evaluationId: string | number
  batchId: string | number
}) => {
  const response = await httpClient.put(
    `/evaluations/${evaluationId}/batches/${batchId}/resumption`
  )

  return response.data
}

export const getEvaluationBatchLog = async ({
  evaluationId,
  batchId,
  kind,
  trySequence,
  page = 1
}: {
  evaluationId: string | number
  batchId?: string | number
  kind: string
  trySequence?: string | number
  page?: string | number
}) => {
  const response = await httpClient.get<EvaluationBatchLogResponse>(
    `/evaluations/${evaluationId}/batches/${batchId}/logs/${kind}`,
    {
      params: compactParams({ page, trySequence })
    }
  )

  return response.data
}

export const startManualEvaluating = async (dagId: string | number) => {
  const response = await httpClient.put(`/evaluations/dags/${dagId}/evaluation`)

  return response.data
}

export const updateEvaluationBatchDatasets = async ({
  evaluationId,
  batchId,
  datasets,
  datasetsConfig,
  includeRobustness
}: {
  evaluationId: string | number
  batchId: string | number
  datasets: number[]
  datasetsConfig?: unknown[]
  includeRobustness?: boolean
}) => {
  const response = await httpClient.put(
    `/evaluations/${evaluationId}/batches/${batchId}/datasets`,
    {
      datasets,
      datasetsConfig,
      includeRobustness
    }
  )

  return response.data
}

export const startMultimodalSurvey = async (batchId?: string | number) => {
  const response = await httpClient.post(`/evaluations/batches/${batchId}/survey`)

  return response.data
}
