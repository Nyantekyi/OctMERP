import { defineEventHandler } from 'h3'

import { getBackendApiBase, getTenantHeaders, requireAuthToken } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  const token = requireAuthToken(event)

  return await $fetch(`${getBackendApiBase(event)}/auth/me/`, {
    headers: {
      accept: 'application/json',
      authorization: `Token ${token}`,
      ...getTenantHeaders(event),
    },
    retry: 0,
  })
})