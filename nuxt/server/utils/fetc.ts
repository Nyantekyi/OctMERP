import type { H3Event } from 'h3'

import { getRequestHeader } from 'h3'

import type { HttpMethod } from './all'

interface FetchOptions {
  method?: HttpMethod
  query?: Record<string, unknown>
  body?: unknown
  headers?: Record<string, string>
}

export async function fetchApi<T>(
  path: string,
  options: FetchOptions,
  event: H3Event
): Promise<T> {
  const runtimeConfig = useRuntimeConfig(event)
  const upstreamBase = runtimeConfig.golderppath

  const authorization = getRequestHeader(event, 'authorization')
  const cookie = getRequestHeader(event, 'cookie')

  const response = await $fetch(`${upstreamBase}${path}`, {
    method: options.method,
    query: options.query,
    body: options.body as Record<string, unknown> | undefined,
    headers: {
      accept: 'application/json',
      ...(authorization ? { authorization } : {}),
      ...(cookie ? { cookie } : {}),
      ...options.headers
    }
  })

  return response as T
}
