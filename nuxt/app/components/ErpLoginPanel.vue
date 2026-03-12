<script setup lang="ts">
const emit = defineEmits<{ success: [] }>()

const credentials = reactive({
  email: '',
  password: ''
})

const loading = ref(false)
const errorMessage = ref('')

const { signIn } = useErpSession()

async function onSubmit() {
  errorMessage.value = ''
  loading.value = true

  try {
    await signIn({
      email: credentials.email,
      password: credentials.password
    })

    credentials.password = ''
    emit('success')
  } catch (error: any) {
    errorMessage.value = error?.data?.detail ?? error?.statusMessage ?? 'Unable to sign in with the current credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="erp-surface p-6 lg:p-7" @submit.prevent="onSubmit">
    <div class="space-y-2">
      <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
        Staff Access
      </p>

      <div>
        <h2 class="text-2xl font-semibold text-slate-950">
          Sign in to the ERP cockpit
        </h2>

        <p class="mt-2 text-sm leading-6 text-slate-600">
          This Nuxt app talks to the Django REST Framework backend through secure server routes and cookie-backed JWT tokens.
        </p>
      </div>
    </div>

    <div class="mt-6 grid gap-4">
      <label class="grid gap-2 text-sm font-medium text-slate-700">
        Email
        <input
          v-model="credentials.email"
          type="email"
          autocomplete="email"
          required
          placeholder="staff@company.com"
          class="erp-input"
        >
      </label>

      <label class="grid gap-2 text-sm font-medium text-slate-700">
        Password
        <input
          v-model="credentials.password"
          type="password"
          autocomplete="current-password"
          required
          placeholder="Enter your password"
          class="erp-input"
        >
      </label>
    </div>

    <p v-if="errorMessage" class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </p>

    <div class="mt-6 flex flex-wrap items-center gap-3">
      <button type="submit" class="erp-button" :disabled="loading">
        {{ loading ? 'Signing in...' : 'Sign in' }}
      </button>

      <span class="text-sm text-slate-500">
        Requests are proxied through <strong>/api/auth</strong> and <strong>/api/backend</strong>.
      </span>
    </div>
  </form>
</template>
