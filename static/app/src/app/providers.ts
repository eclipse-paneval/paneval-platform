import type { App } from 'vue'
import ElementPlus from 'element-plus'
import elementEn from 'element-plus/es/locale/lang/en'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { i18n } from '@/i18n'
import { router } from '@/router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
})

export const installProviders = (app: App) => {
  app.use(createPinia())
  app.use(i18n)
  app.use(router)
  app.use(ElementPlus, {
    locale: elementEn
  })
  app.use(VueQueryPlugin, {
    queryClient
  })
}
