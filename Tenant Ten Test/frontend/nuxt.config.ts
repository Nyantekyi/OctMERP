import { defineNuxtConfig } from "nuxt/config"

export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    public: {
      // Can be overridden at runtime with NUXT_PUBLIC_API_BASE_URL.
      apiBaseUrl: "http://localhost:8000",
    },
  },
  compatibilityDate: "2026-01-01",
})
