import { defineStore } from 'pinia'

type OpenLoginDialogOptions = {
  redirectTo?: string
}

export const useLoginDialogStore = defineStore('loginDialog', {
  state: () => ({
    visible: false,
    redirectTo: ''
  }),
  actions: {
    open(options: OpenLoginDialogOptions = {}) {
      this.redirectTo = options.redirectTo || ''
      this.visible = true
    },
    close() {
      this.visible = false
    },
    resetRedirect() {
      this.redirectTo = ''
    }
  }
})
