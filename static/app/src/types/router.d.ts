import 'vue-router'
import type { LocaleMessageKey } from '@/i18n/types'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    titleKey?: LocaleMessageKey
    keepAlive?: boolean
  }
}

export {}
