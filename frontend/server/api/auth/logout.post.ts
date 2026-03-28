import { clearCookie, defineEventHandler } from 'h3'

import { getAuthCookieName, getAuthToken, getBackendApiBase, getTenantHeaders } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  const token = getAuthToken(event)

  if (token) {
    await $fetch(`${getBackendApiBase(event)}/auth/logout/`, {
      headers: {
        accept: 'application/json',
        authorization: `Token ${token}`,
        ...getTenantHeaders(event),
      },
      method: 'POST',
      retry: 0,
    }).catch(() => undefined)
  }

  clearCookie(event, getAuthCookieName(event), { path: '/' })

  return { ok: true }
})