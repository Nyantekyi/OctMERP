import type { H3Event } from 'h3'

import {
  createError,
  getCookie,
  getRequestHeader,
  getRequestHost,
  getRequestProtocol,
  getRequestURL,
} from 'h3'

type TenantSummary = {
  id: string | null
  name: string | null
  schema_name: string | null
}

type TenantResolution = {
  recognized: boolean
  domain: string | null
  tenant: TenantSummary
}

type CacheEntry = {
  expiresAt: number
  value: TenantResolution
}

const tenantCache = globalThis.__erpTenantCache || new Map<string, CacheEntry>()

globalThis.__erpTenantCache = tenantCache

declare global {
  var __erpTenantCache: Map<string, CacheEntry> | undefined
}

export function normalizeTenantDomain(value?: string | null) {
  const domain = (value || '').trim().toLowerCase()
  if (!domain) {
    return ''
  }

  const withoutProtocol = domain.includes('://') ? (domain.split('://', 2)[1] ?? '') : domain
  const withoutPath = withoutProtocol.split('/', 1)[0] || ''
  return withoutPath.split(':', 1)[0] || ''
}

export function getIncomingTenantDomain(event: H3Event) {
  return normalizeTenantDomain(
    getRequestHeader(event, 'x-forwarded-host') || getRequestHost(event, { xForwardedHost: true }),
  )
}

export function getBackendApiBase(event: H3Event) {
  return useRuntimeConfig(event).backendApiBase.replace(/\/+$/, '')
}

export function getAuthCookieName(event: H3Event) {
  return useRuntimeConfig(event).authCookieName
}

export function getAuthToken(event: H3Event) {
  return getCookie(event, getAuthCookieName(event))
}

export function getTenantHeaders(event: H3Event) {
  const tenantHost = event.context.tenantHost || getIncomingTenantDomain(event)
  const protocol = getRequestProtocol(event, { xForwardedProto: true })

  return {
    'x-forwarded-host': tenantHost,
    'x-forwarded-proto': protocol,
  }
}

export async function resolveTenant(event: H3Event): Promise<TenantResolution> {
  const tenantDomain = getIncomingTenantDomain(event)
  if (!tenantDomain) {
    throw createError({ statusCode: 400, statusMessage: 'Missing tenant host.' })
  }

  const config = useRuntimeConfig(event)
  const cachedEntry = tenantCache.get(tenantDomain)
  if (cachedEntry && cachedEntry.expiresAt > Date.now()) {
    return cachedEntry.value
  }

  const endpoint = `${getBackendApiBase(event)}/tenant/resolve/`

  
  try {
    const resolution = await $fetch<TenantResolution>(endpoint, {
      headers: {
        accept: 'application/json',
        ...getTenantHeaders(event),
      },
      query: { domain: tenantDomain },
      retry: 0,
    })

    tenantCache.set(tenantDomain, {
      expiresAt: Date.now() + Number(config.tenantCacheTtlMs || 60000),
      value: resolution,
    })

    return resolution
  } catch {
    throw createError({ statusCode: 502, statusMessage: 'Unable to resolve tenant.' })
  }
}

export function buildBackendUrl(event: H3Event, path: string) {
  const trimmedPath = path.replace(/^\/+/, '')
  const url = new URL(`${getBackendApiBase(event)}/${trimmedPath}`)
  const requestUrl = getRequestURL(event)

  for (const [key, value] of requestUrl.searchParams.entries()) {
    url.searchParams.append(key, value)
  }

  return url.toString()
}

export function requireAuthToken(event: H3Event) {
  const token = getAuthToken(event)
  if (!token) {
    throw createError({ statusCode: 401, statusMessage: 'Authentication required.' })
  }

  return token
}