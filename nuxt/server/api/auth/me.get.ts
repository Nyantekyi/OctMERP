import { callDjango } from '../../utils/backend'

export default defineEventHandler(async (event): Promise<Record<string, unknown>> => {
  return await callDjango<Record<string, unknown>>(event, 'auth/me')
})
