import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useLoginDialogStore } from './loginDialog'

describe('login dialog store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    window.sessionStorage.clear()
  })

  it('persists and consumes an internal OIDC redirect target once', () => {
    const store = useLoginDialogStore()

    store.open({ redirectTo: '/console/evaluations?status=running' })
    store.persistOidcRedirectTarget()

    expect(store.consumeOidcRedirectTarget('/')).toBe('/console/evaluations?status=running')
    expect(store.consumeOidcRedirectTarget('/')).toBe('')
  })

  it('does not persist external or root redirect targets', () => {
    const store = useLoginDialogStore()

    store.open({ redirectTo: 'https://example.test/console' })
    store.persistOidcRedirectTarget()
    expect(store.consumeOidcRedirectTarget('/')).toBe('')

    store.open({ redirectTo: '/' })
    store.persistOidcRedirectTarget()
    expect(store.consumeOidcRedirectTarget('/console')).toBe('')
  })
})
