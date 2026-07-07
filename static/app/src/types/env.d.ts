interface ImportMetaEnv {
  readonly VITE_API_BASEPATH: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_UPLOAD_BASE_URL: string
  readonly VITE_STATIC_BASE_URL: string
  readonly VITE_PRIVACY_URL: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_DEPLOY_REGION: 'local' | 'eu'
  readonly VITE_BASE_PATH: string
  readonly VITE_DROP_DEBUGGER?: string
  readonly VITE_DROP_CONSOLE?: string
  readonly VITE_SOURCEMAP?: string
  readonly VITE_OUT_DIR?: string
  readonly VITE_APP_TITLE: string
  readonly VITE_USE_ONLINE_ICON: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
