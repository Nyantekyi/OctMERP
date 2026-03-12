import { createError, readBody } from 'h3'
import { callDjango, clearTokens, getDjangoUrl, persistTokens } from '../../utils/backend'

interface LoginBody {
  email?: string
  password?: string
}

interface TokenPayload {
  access: string
  refresh: string
}

export default defineEventHandler(async (event): Promise<{ user: Record<string, unknown> }> => {
  const body = await readBody<LoginBody>(event)

  if (!body?.email || !body?.password) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Email and password are required.'
    })
  }

  try {
    const tokens = await $fetch<TokenPayload>(getDjangoUrl(event, 'auth/login'), {
      method: 'POST',
      body: {
        email: body.email,
        password: body.password
      }
    })

    persistTokens(event, tokens.access, tokens.refresh)

    const user: Record<string, unknown> = await callDjango<Record<string, unknown>>(event, 'auth/me', {
      accessToken: tokens.access
    })

    return { user }
  } catch (error) {
    clearTokens(event)
    throw error
  }
})
