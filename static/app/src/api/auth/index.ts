import { httpClient, resolveApiUrl } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import type { AuthUser, LoginPayload, OidcStatus } from './types'

export const OIDC_STATUS_TIMEOUT_MS = 3000
export const oidcLoginUrl = resolveApiUrl('/users/oidc/login')

let oidcStatusCache: OidcStatus | undefined
let oidcStatusPromise: Promise<OidcStatus> | undefined

export const loginApi = async (payload: LoginPayload) => {
  await httpClient.post('/users/login', payload)
}

export const getOidcStatus = async () => {
  if (oidcStatusCache) return oidcStatusCache

  oidcStatusPromise ??= httpClient
    .get<OidcStatus>('/users/oidc/status', {
      timeout: OIDC_STATUS_TIMEOUT_MS
    })
    .then(({ data }) => {
      oidcStatusCache = data
      return data
    })
    .catch((error) => {
      oidcStatusPromise = undefined
      throw error
    })

  return oidcStatusPromise
}

export const getCachedOidcStatus = () => oidcStatusCache

export const meApi = async () => {
  const { data } = await httpClient.get<AuthUser>('/users/me')
  return data
}

export const logoutApi = async () => {
  await httpClient.delete('/users/me')
}

export const refreshCurrentUser = async () => {
  const authStore = useAuthStore()

  try {
    const user = await meApi()
    authStore.setUser(user)
    return user
  } catch (error) {
    authStore.clearUser()
    throw error
  }
}
