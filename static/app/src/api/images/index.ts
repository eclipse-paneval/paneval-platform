import { httpClient } from '@/api/client'
import type {
  ImageData,
  ImageFormData,
  ImageListParams,
  ImageListResponse,
  ImageTableResponse
} from './types'

const compactParams = (params: Record<string, unknown>) => {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== '')
  )
}

export const listImages = async ({
  page,
  pageIndex,
  pageSize,
  status,
  orderBy,
  keywords
}: ImageListParams = {}): Promise<ImageListResponse> => {
  const response = await httpClient.get<ImageListResponse>('/images/', {
    params: compactParams({
      page: page ?? pageIndex,
      pageSize,
      status,
      orderBy,
      keywords
    })
  })

  return response.data
}

export const getImages = async (params: ImageListParams = {}): Promise<ImageTableResponse> => {
  const response = await listImages(params)

  return {
    total: response.count,
    list: response.results
  }
}

export const createImage = async (payload: ImageFormData) => {
  const response = await httpClient.post('/images/', payload)

  return response.data
}

export const auditImage = async (
  id: string | number,
  payload: {
    stage1Status: string
    reason?: string
  }
) => {
  const response = await httpClient.put(`/images/${id}/status`, payload)

  return response.data
}

export const deleteImage = async (id: string | number) => {
  await httpClient.delete(`/images/${id}`)
}

export type { ImageData, ImageFormData }
