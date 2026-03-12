import { createError } from 'h3'
import { callDjango, readRequestPayload } from '../../utils/backend'

export default defineEventHandler(async (event): Promise<unknown> => {
  const path = getRouterParam(event, 'path')

  if (!path) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Backend path is required.'
    })
  }

  const { method, query, body } = await readRequestPayload(event)

  return await callDjango(event, path, {
    method,
    query,
    body
  })
})
