import { defineEventHandler } from 'h3'

import { getBackendApiBase, getTenantHeaders } from '../utils/backend'

export default defineEventHandler(async (event) => {
  return await $fetch(`${getBackendApiBase(event)}/health/`, {
    headers: {
      accept: 'application/json',
      ...getTenantHeaders(event),
    },
    retry: 0,
  })
})