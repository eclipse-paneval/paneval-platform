import { afterEach, describe, expect, it, vi } from 'vitest'
import { httpClient } from '@/api/client'
import { loginApi } from './index'

describe('auth api', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('submits username and password to the login endpoint', async () => {
    const postSpy = vi.spyOn(httpClient, 'post').mockResolvedValue({ data: undefined })

    await loginApi({
      username: 'alice',
      password: 'secret'
    })

    expect(postSpy).toHaveBeenCalledWith('/users/login', {
      username: 'alice',
      password: 'secret'
    })
  })
})
