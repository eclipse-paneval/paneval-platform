import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    deployRegion: import.meta.env.VITE_DEPLOY_REGION,
    analyticsEnabled: import.meta.env.VITE_ENABLE_ANALYTICS === 'true'
  })
})
