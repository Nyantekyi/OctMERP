import { createError, defineEventHandler, readBody, setCookie } from 'h3'

import { getAuthCookieName, getBackendApiBase, getTenantHeaders } from '../../utils/backend'

type LoginResponse = {
  expiry: string | null
  token: string
  user: {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    is_staff: boolean
  }
}

export default defineEventHandler(async (event) => {
  const body = await readBody<{ username: string; password: string }>(event)
  const endpoint = `${getBackendApiBase(event)}/auth/login/`

  let payload: LoginResponse

  try {
    payload = await $fetch<LoginResponse>(endpoint, {
      body,
      headers: {
        accept: 'application/json',
        ...getTenantHeaders(event),
      },
      method: 'POST',
      retry: 0,
    })
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Invalid login credentials.' })
  }

  if (!payload.token) {
    throw createError({ statusCode: 502, statusMessage: 'Login token missing from upstream response.' })
  }

  setCookie(event, getAuthCookieName(event), payload.token, {
    httpOnly: true,
    path: '/',
    sameSite: 'lax',
    secure: !import.meta.dev,
  })

  return {
    expiry: payload.expiry,
    tenant: event.context.tenant,
    user: payload.user,
  }
})