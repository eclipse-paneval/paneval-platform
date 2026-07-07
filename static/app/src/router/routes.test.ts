import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import en from '@/locales/en.json'
import { routes } from './routes'

const currentDir = dirname(fileURLToPath(import.meta.url))

const flattenPaths = () => {
  return routes.flatMap((route) => {
    const parent = route.path
    return (route.children || []).map((child) => {
      const childPath = child.path ? `/${child.path}` : ''
      return `${parent}${childPath}`.replace('//', '/')
    })
  })
}

const readLocaleValue = (key: string) => {
  return key.split('.').reduce<unknown>((current, segment) => {
    if (current && typeof current === 'object' && segment in current) {
      return (current as Record<string, unknown>)[segment]
    }
    return undefined
  }, en)
}

describe('routes', () => {
  it('includes the scaffold entry points', () => {
    expect(flattenPaths()).toEqual(
      expect.arrayContaining([
        '/',
        '/console',
        '/console/evaluations',
        '/console/evaluations/create',
        '/console/evaluations/:id/edit',
        '/console/evaluations/:id'
      ])
    )
  })

  it('protects console routes with auth metadata', () => {
    const consoleRoute = routes.find((route) => route.path === '/console')

    expect(consoleRoute?.meta?.requiresAuth).toBe(true)
  })

  it('redirects the console root to model evaluations', () => {
    const consoleRoute = routes.find((route) => route.path === '/console')
    const indexRoute = consoleRoute?.children?.find((route) => route.path === '')

    expect(indexRoute?.redirect).toBe('/console/evaluations')
  })

  it('defines document title keys for visible application routes', () => {
    const titledPaths = flattenPaths().filter((path) => path !== '/console')
    const titleByPath = new Map(
      routes.flatMap((route) => {
        const parent = route.path
        return (route.children || []).map((child) => {
          const childPath = child.path ? `/${child.path}` : ''
          return [`${parent}${childPath}`.replace('//', '/'), child.meta?.titleKey]
        })
      })
    )

    for (const path of titledPaths) {
      expect(titleByPath.get(path), `${path} should define route meta.titleKey`).toEqual(
        expect.any(String)
      )
    }
  })

  it('resolves route document title keys from the English locale', () => {
    const titleKeys = routes.flatMap((route) =>
      (route.children || []).flatMap((child) =>
        typeof child.meta?.titleKey === 'string' ? [child.meta.titleKey] : []
      )
    )

    for (const titleKey of titleKeys) {
      expect(readLocaleValue(titleKey), `${titleKey} should exist in the English locale`).toEqual(
        expect.any(String)
      )
    }
  })

  it('uses Vue Router HTML5 history mode instead of hash mode', () => {
    const routerSource = readFileSync(resolve(currentDir, 'index.ts'), 'utf8')

    expect(routerSource).toContain('createWebHistory')
    expect(routerSource).not.toContain('createWebHashHistory')
  })
})
