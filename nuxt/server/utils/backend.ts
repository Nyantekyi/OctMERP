import type { H3Event } from 'h3'
import { createError, deleteCookie, getCookie, getQuery, readBody, setCookie } from 'h3'

const accessCookieName = 'erp_access_token'
const refreshCookieName = 'erp_refresh_token'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

interface BackendRequestOptions {
  method?: HttpMethod
  query?: Record<string, unknown>
  body?: unknown
  accessToken?: string | null
}

function secureCookie() {
  return (import.meta as unknown as { env: { PROD: boolean } }).env.PROD
}

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    path: '/',
    sameSite: 'lax' as const,
    secure: secureCookie(),
    maxAge
  }
}

function normalisePath(path: string) {
  const trimmed = path.replace(/^\/+/, '')
  return trimmed.endsWith('/') ? trimmed : `${trimmed}/`
}

function errorData(error: any) {
  return error?.data ?? error?.response?._data ?? error?.response?.data ?? null
}

function toBackendError(error: any) {
  const data = errorData(error)
  const statusCode = error?.response?.status ?? error?.statusCode ?? 500
  const statusMessage = data?.detail ?? data?.message ?? error?.statusMessage ?? 'Django backend request failed.'

  return createError({
    statusCode,
    statusMessage,
    data
  })
}

export function getDjangoUrl(event: H3Event, path: string) {
  const config = useRuntimeConfig(event)
  const baseUrl = String(config.djangoBaseUrl).replace(/\/+$/, '')
  return `${baseUrl}/${normalisePath(path)}`
}

export function persistTokens(event: H3Event, accessToken: string, refreshToken: string) {
  setCookie(event, accessCookieName, accessToken, cookieOptions(60 * 30))
  setCookie(event, refreshCookieName, refreshToken, cookieOptions(60 * 60 * 24 * 7))
}

export function clearTokens(event: H3Event) {
  deleteCookie(event, accessCookieName, { path: '/' })
  deleteCookie(event, refreshCookieName, { path: '/' })
}

async function requestDjango<T>(
  event: H3Event,
  path: string,
  options: BackendRequestOptions,
  token?: string | null
): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase() as HttpMethod
  const headers = token
    ? { Authorization: `Bearer ${token}` }
    : undefined

  const response = await $fetch(getDjangoUrl(event, path), {
    method,
    headers,
    query: options.query,
    body: options.body as Record<string, unknown> | BodyInit | null | undefined
  })

  return response as T
}

export async function refreshAccessToken(event: H3Event): Promise<string | null> {
  const refreshToken = getCookie(event, refreshCookieName)

  if (!refreshToken) {
    clearTokens(event)
    return null
  }

  try {
    const payload = await $fetch<{ access: string, refresh?: string }>(getDjangoUrl(event, 'auth/refresh'), {
      method: 'POST',
      body: { refresh: refreshToken }
    })

    persistTokens(event, payload.access, payload.refresh ?? refreshToken)
    return payload.access
  } catch {
    clearTokens(event)
    return null
  }
}

export async function callDjango<T>(
  event: H3Event,
  path: string,
  options: BackendRequestOptions = {}
): Promise<T> {
  const accessToken = options.accessToken ?? getCookie(event, accessCookieName)

  try {
    return await requestDjango<T>(event, path, options, accessToken)
  } catch (error: any) {
    const statusCode = error?.response?.status ?? error?.statusCode

    if (statusCode === 401) {
      const nextAccessToken = await refreshAccessToken(event)

      if (nextAccessToken) {
        return await requestDjango<T>(event, path, options, nextAccessToken)
      }

      clearTokens(event)
    }

    throw toBackendError(error)
  }
}

export async function readRequestPayload(event: H3Event): Promise<{
  method: HttpMethod
  query: Record<string, unknown>
  body: unknown
}> {
  const method = event.method.toUpperCase() as HttpMethod
  const query = getQuery(event)
  const body = ['POST', 'PUT', 'PATCH'].includes(method)
    ? await readBody(event)
    : undefined

  return { method, query, body }
}
