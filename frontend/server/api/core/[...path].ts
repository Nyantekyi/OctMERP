import { createError, defineEventHandler, getProxyRequestHeaders, getRouterParam, proxyRequest } from 'h3'

import { buildBackendUrl, getTenantHeaders, requireAuthToken } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  const routePath = getRouterParam(event, 'path') || ''
  if (!routePath) {
    throw createError({ statusCode: 400, statusMessage: 'Missing API route path.' })
  }

  const token = requireAuthToken(event)
  const requestHeaders = getProxyRequestHeaders(event)

  delete requestHeaders.host
  delete requestHeaders.cookie

  return proxyRequest(event, buildBackendUrl(event, routePath), {
    headers: {
      ...requestHeaders,
      authorization: `Token ${token}`,
      ...getTenantHeaders(event),
    },
  })
})