/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_USE_MOCK: string
  readonly VITE_API_BASE: string
  readonly VITE_WS_BASE: string
  readonly VITE_AI_BASE: string
<<<<<<< HEAD
  readonly VITE_AMAP_KEY: string
  readonly VITE_AMAP_SECURITY_CODE: string
=======
>>>>>>> feature-cui
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
