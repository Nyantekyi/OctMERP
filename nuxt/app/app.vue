<script setup lang="ts">
const { user, isAuthenticated, refreshUser, signOut } = useErpSession()
const route = useRoute()

await useAsyncData('erp-session-bootstrap', async () => {
  if (user.value) {
    return user.value
  }

  return await refreshUser()
})

const userName = computed(() => {
  const fullName = [user.value?.first_name, user.value?.last_name].filter(Boolean).join(' ')
  return fullName || user.value?.email || 'ERP user'
})

const signingOut = ref(false)

async function onSignOut() {
  signingOut.value = true

  try {
    await signOut()
    await navigateTo('/')
  } finally {
    signingOut.value = false
  }
}

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

useSeoMeta({
  title: 'Golderp Cockpit',
  description: 'Nuxt frontend for the ERP Django REST Framework backend.',
  ogTitle: 'Golderp Cockpit',
  ogDescription: 'Nuxt frontend for the ERP Django REST Framework backend.',
  twitterCard: 'summary_large_image'
})
</script>

<template>
  <div class="erp-shell">
    <div class="mx-auto flex min-h-screen max-w-[1440px] flex-col px-4 py-4 sm:px-6 lg:px-8">
      <header class="erp-surface px-5 py-4 sm:px-6 lg:px-7">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div class="flex min-w-0 flex-col gap-4 xl:flex-row xl:items-center">
            <NuxtLink to="/" class="min-w-0 text-inherit no-underline">
              <AppLogo />
            </NuxtLink>

            <TemplateMenu />
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <span class="erp-pill text-sm text-slate-600">
              {{ isAuthenticated ? 'Connected to Django API' : 'Signed out' }}
            </span>

            <span class="erp-pill text-sm text-slate-600">
              {{ route.path }}
            </span>

            <div v-if="isAuthenticated" class="flex items-center gap-3">
              <div class="rounded-2xl bg-slate-950 px-3 py-2 text-sm text-white">
                <strong>{{ userName }}</strong>
                <span class="ml-2 text-slate-300">{{ user?.user_type }}</span>
              </div>

              <button type="button" class="erp-button erp-button--secondary" :disabled="signingOut" @click="onSignOut">
                {{ signingOut ? 'Signing out...' : 'Sign out' }}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main class="flex-1 py-6">
        <NuxtPage />
      </main>

      <footer class="px-2 pb-4 text-sm text-slate-500 sm:px-4">
        Golderp Cockpit renders live data from the mounted DRF apps under <strong>/api/v1</strong> and keeps auth on the Nuxt server layer.
      </footer>
    </div>
  </div>
</template>
