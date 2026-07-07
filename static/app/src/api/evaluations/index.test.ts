import { afterEach, describe, expect, it, vi } from 'vitest'
import { httpClient } from '@/api/client'
import {
  createEvaluation,
  createTokenizerUpload,
  getDatasets,
  getCustomImages,
  getEvaluation,
  getEvaluations,
  removeEvaluation,
  updateEvaluation
} from './index'

describe('evaluation api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads evaluations from the compatible endpoint', async () => {
    const getSpy = vi.spyOn(httpClient, 'get').mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 10,
            name: 'Aquila benchmark',
            owner: 'alice',
            domain: 'N',
            sence: 'model',
            datasets: [1, 2]
          }
        ]
      }
    })

    const evaluations = await getEvaluations({
      pageIndex: 2,
      pageSize: 20,
      modelName: 'Aquila',
      domain: 'N'
    })

    expect(getSpy).toHaveBeenCalledWith('/evaluations/', {
      params: {
        page: 2,
        pageSize: 20,
        modelName: 'Aquila',
        domain: 'N'
      }
    })
    expect(evaluations.total).toBe(1)
    expect(evaluations.list[0]).toMatchObject({
      id: 10,
      name: 'Aquila benchmark',
      owner: 'alice'
    })
  })

  it('removes an evaluation by id', async () => {
    const deleteSpy = vi.spyOn(httpClient, 'delete').mockResolvedValue({ data: undefined })

    await removeEvaluation(10)

    expect(deleteSpy).toHaveBeenCalledWith('/evaluations/10')
  })

  it('loads datasets for the create form', async () => {
    const getSpy = vi.spyOn(httpClient, 'get').mockResolvedValue({
      data: [{ id: 1, key: 'reasoning', scenario: 'Reasoning', domain: 'N', datasets: [] }]
    })

    const datasets = await getDatasets()

    expect(getSpy).toHaveBeenCalledWith('/evaluations/datasets', {
      params: {}
    })
    expect(datasets[0]).toMatchObject({ id: 1, key: 'reasoning' })
  })

  it('loads approved custom images for the mirror selector', async () => {
    const getSpy = vi.spyOn(httpClient, 'get').mockResolvedValue({
      data: {
        count: 1,
        results: [{ id: 1, name: 'custom-runtime', tag: 'latest', status: 'R' }]
      }
    })

    const images = await getCustomImages({ page: 2, pageSize: 10 })

    expect(getSpy).toHaveBeenCalledWith('/images/', {
      params: { page: 2, pageSize: 10, status: 'R' }
    })
    expect(images.count).toBe(1)
    expect(images.results[0]).toMatchObject({ name: 'custom-runtime' })
  })

  it('creates a tokenizer upload before uploading files', async () => {
    const postSpy = vi.spyOn(httpClient, 'post').mockResolvedValue({ data: { id: 42 } })

    const tokenizer = await createTokenizerUpload()

    expect(postSpy).toHaveBeenCalledWith('/evaluations/tokenizers')
    expect(tokenizer.id).toBe(42)
  })

  it('creates, retrieves, and updates evaluations', async () => {
    const payload = {
      sence: 'model',
      name: 'Aquila benchmark',
      description: 'Baseline run',
      domain: 'N',
      url: 'https://example.com/model',
      agreement: true,
      scenarios: ['reasoning'],
      datasets: [1]
    }
    const postSpy = vi.spyOn(httpClient, 'post').mockResolvedValueOnce({ data: { id: 10 } })
    const getSpy = vi.spyOn(httpClient, 'get').mockResolvedValueOnce({
      data: { id: 10, ...payload, owner: 'alice' }
    })
    const patchSpy = vi.spyOn(httpClient, 'patch').mockResolvedValueOnce({ data: { id: 10 } })

    await createEvaluation(payload)
    const evaluation = await getEvaluation(10)
    await updateEvaluation(10, payload)

    expect(postSpy).toHaveBeenCalledWith('/evaluations/', payload)
    expect(getSpy).toHaveBeenCalledWith('/evaluations/10')
    expect(patchSpy).toHaveBeenCalledWith('/evaluations/10', payload)
    expect(evaluation).toMatchObject({ id: 10, name: 'Aquila benchmark' })
  })
})
