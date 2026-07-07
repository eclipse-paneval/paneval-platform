export type ImageSource = 'P' | 'F' | string

export type ImageStatus = 'P' | 'PC' | 'PF' | 'R' | 'D' | 'C' | string

export type ImageUser = {
  id?: string | number
  username?: string
  name?: string
  email?: string
}

export type ImageData = {
  id: string | number
  imageId?: string | number
  name: string
  tag: string
  url?: string
  registryUrl?: string
  dockerfile?: string
  source?: ImageSource
  comment?: string
  status?: ImageStatus
  stage1Status?: ImageStatus
  stage2Status?: ImageStatus
  reason?: string
  createdAt?: string
  created_at?: string
  updatedAt?: string
  updated_at?: string
  user?: ImageUser | string
  jointRaw?: {
    imageSize?: string
    frameLabel?: string
    label?: string
    processorLabel?: string
    registryUrl?: string
    baseUrl?: string
  }
}

export type ImageFormData = {
  name: string
  tag: string
  url: string
  source: ImageSource
  dockerfile: string
  comment: string
}

export type ImageListParams = {
  page?: string | number
  pageIndex?: string | number
  pageSize?: string | number
  status?: ImageStatus
  orderBy?: string
  keywords?: string
}

export type ImageListResponse = {
  count: number
  results: ImageData[]
}

export type ImageTableResponse = {
  total: number
  list: ImageData[]
}
