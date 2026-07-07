import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.DEV_API_PROXY_TARGET || 'http://120.92.17.239:9080'
  const wsProxyTarget = env.DEV_WS_PROXY_TARGET || 'ws://120.92.17.239:9080'
  const dropOptions = [
    env.VITE_DROP_CONSOLE === 'true' ? 'console' : undefined,
    env.VITE_DROP_DEBUGGER === 'true' ? 'debugger' : undefined
  ].filter((item): item is 'console' | 'debugger' => Boolean(item))

  return {
    base: env.VITE_BASE_PATH || '/',
    plugins: [vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    esbuild: dropOptions.length > 0 ? { drop: dropOptions } : undefined,
    server: {
      port: 4000,
      host: '0.0.0.0',
      hmr: {
        overlay: false
      },
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true
        },
        '/ws': {
          target: wsProxyTarget,
          changeOrigin: true,
          ws: true
        }
      }
    },
    build: {
      outDir: env.VITE_OUT_DIR || 'dist',
      sourcemap: env.VITE_SOURCEMAP === 'true' ? 'inline' : false,
      rollupOptions: {
        onwarn(warning, warn) {
          if (warning.message?.includes('contains an annotation that Rollup cannot interpret')) {
            return
          }
          warn(warning)
        }
      }
    },
    test: {
      environment: 'jsdom',
      globals: true
    }
  }
})
