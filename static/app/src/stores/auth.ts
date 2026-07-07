import { defineStore } from 'pinia'
import type { AuthUser } from '@/api/auth/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as AuthUser | null
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    displayName: (state) => state.user?.username || state.user?.name || state.user?.email || ''
  },
  actions: {
    setUser(user: AuthUser) {
      this.user = user
    },
    clearUser() {
      this.user = null
    }
  }
})
