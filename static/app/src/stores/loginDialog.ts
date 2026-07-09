import { defineStore } from 'pinia'

type OpenLoginDialogOptions = {
  redirectTo?: string
}

const OIDC_REDIRECT_TARGET_KEY = 'paneval:oidcRedirectTarget'

const normalizeRedirectTarget = (target?: string) => {
  if (!target || target === '/' || !target.startsWith('/') || target.startsWith('//')) {
    return ''
  }

  return target
}

export const useLoginDialogStore = defineStore('loginDialog', {
  state: () => ({
    visible: false,
    redirectTo: ''
  }),
  actions: {
    open(options: OpenLoginDialogOptions = {}) {
      this.redirectTo = normalizeRedirectTarget(options.redirectTo)
      this.visible = true
    },
    close() {
      this.visible = false
    },
    resetRedirect() {
      this.redirectTo = ''
    },
    persistOidcRedirectTarget() {
      const target = normalizeRedirectTarget(this.redirectTo)

      if (target) {
        window.sessionStorage.setItem(OIDC_REDIRECT_TARGET_KEY, target)
        return
      }

      window.sessionStorage.removeItem(OIDC_REDIRECT_TARGET_KEY)
    },
    consumeOidcRedirectTarget(currentPath = '') {
      const target = normalizeRedirectTarget(
        window.sessionStorage.getItem(OIDC_REDIRECT_TARGET_KEY) || undefined
      )
      window.sessionStorage.removeItem(OIDC_REDIRECT_TARGET_KEY)

      return target && target !== currentPath ? target : ''
    }
  }
})
