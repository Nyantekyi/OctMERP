import { createError, defineEventHandler, getRequestURL } from 'h3'

import { resolveTenant } from '../utils/backend'

const ignoredPrefixes = ['/_nuxt', '/__nuxt_error', '/favicon', '/robots.txt']

export default defineEventHandler(async (event) => {
  const pathname = getRequestURL(event).pathname
  if (ignoredPrefixes.some(prefix => pathname.startsWith(prefix))) {
    return
  }

  const resolution = await resolveTenant(event)
  if (!resolution.recognized) {
    throw createError({ statusCode: 404, statusMessage: 'Tenant not found.' })
  }

  event.context.tenantHost = resolution.domain
  event.context.tenant = resolution.tenant
})