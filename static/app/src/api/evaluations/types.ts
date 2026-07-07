export type EvaluationDomain = 'N' | 'CV' | 'MM' | 'SAFETY' | 'AUDIO' | string

export type EvaluationListItem = {
  id: string | number
  name: string
  description?: string
  domain: EvaluationDomain
  sence: string
  url?: string
  createdAt?: string
  updatedAt?: string
  owner?: string
  datasets: number[]
  datasetsConfig?: EvaluationDatasetConfig[]
  model?: string
  specialEvent?: string
}

export type EvaluationDatasetConfig = {
  id?: number
  dataset?: string
  datasetShow?: string
  is_admin?: boolean
  name?: string
  output?: string
  taskName?: string
  taskId?: number
  leaderboard?: boolean
  description?: string
}

export type EvaluationDataset = {
  id: number
  key: string
  scenario: string
  task?: string
  label?: string
  subject?: string
  tags?: unknown[]
  language?: string
  domain: EvaluationDomain
  name?: string
  description?: string
  available?: boolean
  package?: string
  leaderboard?: boolean
  descriptionEn?: string
  disturbances?: Array<{
    name: string
    label?: string
    group?: 'C' | 'F' | string
  }>
}

export type EvaluationPayload = {
  sence: string
  name: string
  description?: string
  domain: EvaluationDomain
  url?: string
  agreement: boolean
  scenarios?: string[]
  datasets: number[]
  datasetsConfig?: EvaluationDatasetConfig[]
  pkgs?: string[]
  model?: string
  modelType?: string
  onlineModelName?: string
  onlineApiKey?: string
  environVars?: Record<string, unknown>
  paperUrl?: string
  modelUrl?: string
  tokenizer?: {
    tokenizerName?: string
    maxSequenceLength?: number | string
    endOfTextToken?: string
    prefixToken?: string
  }
  pretrainedTokenizerId?: string
  tokenizerName?: string
  maxSequenceLength?: number | string
  endOfTextToken?: string
  prefixToken?: string
  dimensions?: string[]
  includeRobustness?: boolean
  robustEnv?: string
  leaderboardLite?: boolean
  leaderboardMeta?: Record<string, unknown>
  lite_model?: string
  lite_baseModel?: string
  lite_revision?: string
  lite_precision?: string
  lite_private?: boolean
  lite_weightType?: string
  lite_modelType?: string
  lite_runsh?: string
  lite_adapter?: string
  modelGenKwargs?: string
  jointBasicImage?: string
  jointBasicImageType?: string
  jointPriority?: string
  acceleratorModel?: string
  jointResource?: unknown
  jointQueueId?: string
}

export type EvaluationDetail = EvaluationListItem & {
  agreement?: boolean
  scenarios?: string[]
  pkgs?: string[]
  modelId?: string
  modelToken?: string
  modelRevision?: string
  tokenizer?: {
    tokenizerName?: string
    maxSequenceLength?: number | string
    endOfTextToken?: string
    prefixToken?: string
  }
  pretrainedTokenizerId?: string
  modelType?: string
  onlineModelName?: string
  onlineApiKey?: string
  environVars?: Record<string, unknown>
  paperUrl?: string
  modelUrl?: string
  tokenizerName?: string
  maxSequenceLength?: number | string
  endOfTextToken?: string
  prefixToken?: string
  dimensions?: string[]
  includeRobustness?: boolean
  robustEnv?: string
  leaderboardLite?: boolean
  leaderboardMeta?: Record<string, unknown>
  modelGenKwargs?: string
  jointBasicImage?: string
  jointBasicImageType?: string
  jointPriority?: string
  acceleratorModel?: string
  jointResource?: unknown
}

export type EvaluationBatchStatus =
  | 'M'
  | 'P'
  | 'PPR'
  | 'PPE'
  | 'PST'
  | 'PSC'
  | 'R'
  | 'DI'
  | 'HE'
  | 'S'
  | 'F'
  | 'C'
  | string

export type EvaluationBatch = {
  id: string | number
  evaluationId: string | number
  sequence?: number
  dryRun?: boolean
  status?: EvaluationBatchStatus
  owner?: string
  submitted?: boolean
  trySequence?: number
  jointJobId?: string
  priority?: string
  onlineModelName?: string
  createdAt?: string
  updatedAt?: string
  resource?: {
    acceleratorModel?: string
    acceleratorCount?: number
    cpuCores?: number
    memGib?: number
  }
  modelRevision?: string
  includeRobustness?: boolean
}

export type EvaluationBatchResponse = {
  count: number
  next?: string | null
  previous?: string | null
  results: EvaluationBatch[]
}

export type EvaluationDag = {
  id: string | number
  datasetId?: number
  runEntry?: string
  status?: EvaluationBatchStatus
  result?: Record<string, unknown>
  disturbance?: string
  createdAt?: string
  updatedAt?: string
  stoppedAt?: string | number
  startedAt?: string | number
}

export type EvaluationResultDetail = {
  datasetId?: number
  accuracy?: number
  calibration?: number
  robustness?: number
  fairness?: number
  bias?: number
  numEval?: number
  numTrain?: number
  truncated?: number
  numTrials?: number
  modelOrAdapter?: string
  numOutputTokens?: number
  numPromptTokens?: number
  robustnesses?: Record<string, number>
}

export type EvaluationBatchResult = {
  datasetKey?: string
  dataset?: string
  datasetIds?: number[]
  datasetId?: number
  name?: string
  status?: EvaluationBatchStatus | number | string
  accuracy?: number
  calibration?: number
  robustness?: number
  fairness?: number
  bias?: number
  winRate?: number
  disturbance?: string
  details?: (EvaluationResultDetail & Record<string, unknown>)[]
  lbx?: unknown
  data?: unknown
}

export type EvaluationBatchResultResponse = {
  results?: EvaluationBatchResult[]
  robustnesses?: unknown[]
  reportUrl?: string
  lbx?: unknown
}

export type EvaluationBatchLogResponse = {
  results: string
  page: {
    total: number
  }
}

export type EvaluationListParams = {
  pageIndex?: string | number
  pageSize?: string | number
  me?: string | number
  createUser?: string
  modelName?: string
  domain?: string
  specialEvent?: string
}

export type EvaluationListResponse = {
  total: number
  list: EvaluationListItem[]
}

export type PaginatedEvaluationResponse = {
  count: number
  next?: string | null
  previous?: string | null
  results: EvaluationListItem[]
}

export type MultimodalDatasetGroup = {
  id: number
  name: string
  data: EvaluationDatasetConfig[]
}

export type EvaluationPaging = {
  page: number
  pageSize: number
  total: number
}

export type EvaluationImage = {
  id?: string | number
  name: string
  tag: string
  baseUrl?: string
  registryUrl?: string
  imageSize?: string
  createdTime?: string | number
  createdAt?: string | number
  desc?: string
  comment?: string
  dockerfile?: string
  frameLabel?: string
  label?: string
  processorLabel?: string
  packageInfo?: string
  jointRaw?: {
    imageSize?: string
    frameLabel?: string
    label?: string
    processorLabel?: string
    registryUrl?: string
    baseUrl?: string
  }
}

export type EvaluationImageResponse = {
  items: EvaluationImage[]
  paging: EvaluationPaging
}

export type CustomImageResponse = {
  count: number
  results: EvaluationImage[]
}

export type EvaluationQueue = {
  id: string | number
  acceleratorModel?: string
  quotaDetailList?: Array<{
    resourceDetail?: {
      acceleratorModel?: string
    }
  }>
}

export type EvaluationQueueResponse = {
  queueSummaryInfos: EvaluationQueue[]
}

export type EvaluationResource = {
  acceleratorModel?: string
  acceleratorCount?: number
  cpuCores?: number
  memGib?: number
}

export type EvaluationResourceResponse = {
  items: EvaluationResource[]
  paging: EvaluationPaging
}
