// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui'],
  runtimeConfig: {
    backendApiBase: import.meta.env.NUXT_BACKEND_API_BASE || import.meta.env.NUXT_DJANGO_API_BASE || 'http://127.0.0.1:8000/api',
    authCookieName: import.meta.env.NUXT_AUTH_COOKIE_NAME || 'erp_knox_token',
    tenantCacheTtlMs: Number.parseInt(import.meta.env.NUXT_TENANT_CACHE_TTL_MS || '60000', 10),
  },
})
