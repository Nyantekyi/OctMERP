<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

import { getMainNavigation } from '~/layouts/urls/main'

const route = useRoute()
const { isSidebarCollapsed, toggleSidebar } = useDashboard()

const navigation = computed<NavigationMenuItem[][]>(() => {
  return getMainNavigation(route.path)
})

defineShortcuts({
  'g-h': () => navigateTo('/'),
  alt_shift_b: () => toggleSidebar()
})
</script>

<template>
  <div class="min-h-screen bg-grid">
    <div class="flex min-h-screen">
      <DashboardAppSidebar
        :collapsed="isSidebarCollapsed"
        :items="navigation"
        @toggle="toggleSidebar"
      />

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 border-b border-default bg-default/90 px-4 py-3 backdrop-blur">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-wide text-muted">
                Operations Center
              </p>
              <h1 class="text-base font-semibold">
                Pharma ERP
              </h1>
            </div>

            <div class="flex items-center gap-2">
              <UColorModeButton />
              <UButton
                to="/sign-in"
                icon="i-lucide-log-in"
                color="neutral"
                variant="outline"
              >
                Sign In
              </UButton>
            </div>
          </div>
        </header>

        <main class="p-4 sm:p-6">
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
