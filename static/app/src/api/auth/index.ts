import { httpClient } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import type { AuthUser, LoginPayload } from './types'

export const loginApi = async (payload: LoginPayload) => {
  await httpClient.post('/users/login', payload)
}

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
