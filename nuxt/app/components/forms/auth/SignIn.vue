<script setup lang="ts">
import { z } from 'zod'

import type { FormSubmitEvent } from '#ui/types'

import { signInSchema } from '~/schema/user'

type Schema = z.output<typeof signInSchema>

const form = useTemplateRef('form')
const loading = ref(false)
const toast = useToast()

const state = ref<Schema>({
  username: '',
  password: ''
})

async function onSubmit(event: FormSubmitEvent<Schema>) {
  loading.value = true
  try {
    await submit(event, signInSchema, '/auth/sign-in', 'Create')
    toast.add({
      title: 'Signed in',
      description: 'Welcome back to Pharma ERP.',
      color: 'success',
      icon: 'i-lucide-check-circle'
    })
    await navigateTo('/')
  }
  catch (error: any) {
    form.value?.setErrors(flattenErrors(error?.data?.errors || error?.data?.data || {}))
    toast.add({
      title: 'Sign in failed',
      description: error?.data?.message || error?.message || 'Please verify your credentials and try again.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  }
  finally {
    loading.value = false
  }
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="space-y-1">
        <h1 class="text-xl font-semibold tracking-tight">
          Sign In
        </h1>
        <p class="text-sm text-muted">
          Continue to your pharmaceutical ERP workspace.
        </p>
      </div>
    </template>

    <UForm
      ref="form"
      :schema="signInSchema"
      :state="state"
      class="space-y-4"
      @submit="onSubmit"
    >
      <UFormField
        name="username"
        label="Username"
      >
        <UInput
          v-model="state.username"
          placeholder="Enter username"
          autocomplete="username"
          icon="i-lucide-user"
        />
      </UFormField>

      <UFormField
        name="password"
        label="Password"
      >
        <UInput
          v-model="state.password"
          type="password"
          placeholder="Enter password"
          autocomplete="current-password"
          icon="i-lucide-lock"
        />
      </UFormField>

      <UButton
        type="submit"
        block
        :loading="loading"
        icon="i-lucide-log-in"
      >
        Sign In
      </UButton>
    </UForm>
  </UCard>
</template>

<style scoped></style>
