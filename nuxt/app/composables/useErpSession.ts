export interface SessionUser {
  id: string
  email: string
  first_name: string
  last_name: string
  user_type: string
  company?: string | null
  [key: string]: unknown
}

interface LoginPayload {
  user: SessionUser
}

interface LoginCredentials {
  email: string
  password: string
}

export function useErpSession() {
  const user = useState<SessionUser | null>('erp-session-user', () => null)
  const ready = useState<boolean>('erp-session-ready', () => false)
  const isAuthenticated = computed(() => Boolean(user.value?.id))

  async function refreshUser() {
    try {
      user.value = await $fetch<SessionUser>('/api/auth/me')
      return user.value
    } catch {
      user.value = null
      return null
    } finally {
      ready.value = true
    }
  }

  async function signIn(credentials: LoginCredentials) {
    const payload = await $fetch<LoginPayload>('/api/auth/login', {
      method: 'POST',
      body: credentials
    })

    user.value = payload.user
    ready.value = true
    return payload.user
  }

  async function signOut() {
    await $fetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    ready.value = true
  }

  return {
    user,
    ready,
    isAuthenticated,
    refreshUser,
    signIn,
    signOut
  }
}
