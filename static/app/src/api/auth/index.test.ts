import { afterEach, describe, expect, it, vi } from 'vitest'
import { httpClient, resolveApiUrl } from '@/api/client'
import { getCachedOidcStatus, getOidcStatus, loginApi, OIDC_STATUS_TIMEOUT_MS, oidcLoginUrl } from './index'

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

  it('fetches OpenID Connect availability', async () => {
    const getSpy = vi.spyOn(httpClient, 'get').mockResolvedValue({ data: { enabled: true } })

    await expect(getOidcStatus()).resolves.toEqual({ enabled: true })
    await expect(getOidcStatus()).resolves.toEqual({ enabled: true })

    expect(getSpy).toHaveBeenCalledWith('/users/oidc/status', {
      timeout: OIDC_STATUS_TIMEOUT_MS
    })
    expect(getSpy).toHaveBeenCalledTimes(1)
    expect(getCachedOidcStatus()).toEqual({ enabled: true })
  })

  it('builds the OpenID Connect login redirect from the configured API base', () => {
    expect(oidcLoginUrl).toBe(resolveApiUrl('/users/oidc/login'))
    expect(resolveApiUrl('/users/oidc/login', 'https://example.test/api/')).toBe(
      'https://example.test/api/users/oidc/login'
    )
  })
})
