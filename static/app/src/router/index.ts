import { createRouter, createWebHistory, type RouteLocationNormalizedLoaded } from 'vue-router'
import { refreshCurrentUser } from '@/api/auth'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useLoginDialogStore } from '@/stores/loginDialog'
import { routes } from './routes'

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

const DEFAULT_DOCUMENT_TITLE = 'PanEval'

const getRouteTitle = (to: RouteLocationNormalizedLoaded) => {
  const matchedWithTitle = [...to.matched].reverse().find((route) => route.meta.titleKey)
  const titleKey = matchedWithTitle?.meta.titleKey

  return typeof titleKey === 'string' && titleKey.trim()
    ? `${DEFAULT_DOCUMENT_TITLE} - ${i18n.global.t(titleKey)}`
    : DEFAULT_DOCUMENT_TITLE
}

router.beforeEach(async (to) => {
  const requiresAuth = to.matched.some((route) => route.meta.requiresAuth)

  if (!requiresAuth) {
    return true
  }

  const authStore = useAuthStore()
  const loginDialogStore = useLoginDialogStore()

  if (authStore.isAuthenticated) {
    const target = loginDialogStore.consumeOidcRedirectTarget(to.fullPath)
    if (target) {
      return target
    }

    return true
  }

  try {
    await refreshCurrentUser()
    const target = loginDialogStore.consumeOidcRedirectTarget(to.fullPath)
    if (target) {
      return target
    }

    return true
  } catch {
    loginDialogStore.open({
      redirectTo: to.fullPath
    })
    return { name: 'home' }
  }
})

router.afterEach((to) => {
  document.title = getRouteTitle(to)
})
