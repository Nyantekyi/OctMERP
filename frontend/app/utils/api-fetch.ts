type ApiFetchOptions = Parameters<typeof $fetch>[1] & {
  requiresAuth?: boolean
}

const API_PROXY_BASE = '/api/core'

function normalizeProxyPath(path: string) {
  return path.replace(/^\/+/, '')
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}) {
  const endpoint = `${API_PROXY_BASE}/${normalizeProxyPath(path)}`
  const { requiresAuth = true, ...fetchOptions } = options

  try {
    return await $fetch<T>(endpoint, {
      ...fetchOptions,
      credentials: 'include',
      headers: {
        ...(fetchOptions?.headers || {}),
        'x-requires-auth': String(requiresAuth),
      },
    })
  } catch (error: any) {
    if (error?.statusCode === 401 && requiresAuth) {
      throw createError({ statusCode: 401, statusMessage: 'You must be authenticated to complete this request.' })
    }

    throw error
  }
}

export async function apiFetchRaw<T>(path: string, options: ApiFetchOptions = {}) {
  const endpoint = `${API_PROXY_BASE}/${normalizeProxyPath(path)}`
  const { requiresAuth = true, ...fetchOptions } = options

  try {
    return await $fetch.raw<T>(endpoint, {
      ...fetchOptions,
      credentials: 'include',
      headers: {
        ...(fetchOptions?.headers || {}),
        'x-requires-auth': String(requiresAuth),
      },
    })
  } catch (error: any) {
    if (error?.statusCode === 401 && requiresAuth) {
      throw createError({ statusCode: 401, statusMessage: 'You must be authenticated to complete this request.' })
    }

    throw error
  }
}