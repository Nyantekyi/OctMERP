import { createError, getMethod, getQuery, getRouterParam, readBody } from 'h3'

import { routeContracts } from '~~/server/utils/all'
import { fetchApi } from '~~/server/utils/fetc'

export default defineEventHandler(async (event) => {
  const method = event.method
  const segments = getRouterParam(event, '...')
  const normalized = Array.isArray(segments) ? segments.join('/') : segments || ''
  const path = `/${normalized}` as keyof typeof routeContracts

  const contract = routeContracts[path]
  if (!contract) {
    throw createError({ statusCode: 404, statusMessage: 'Unknown API route' })
  }

  if (!contract.methods.includes(method as never)) {
    throw createError({ statusCode: 405, statusMessage: 'Method not allowed' })
  }

  const queryInput = getQuery(event)
  const bodyInput = ['POST', 'PUT', 'PATCH'].includes(method)
    ? await readBody(event)
    : undefined

  const query = contract.query ? contract.query.parse(queryInput) : undefined
  const body = contract.body ? contract.body.parse(bodyInput) : undefined

  const upstream = await fetchApi(path, {
    method: method as any,
    query,
    body
  }, event)

  return contract.response.parse(upstream)
})
