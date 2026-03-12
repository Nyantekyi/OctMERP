export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()

  const api = $fetch.create({
    baseURL: config.public.apiBase,
    timeout: 10000,
    retry: 3
  })

  return {
    provide: {
      api
    }
  }
})
