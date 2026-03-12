<script setup lang="ts">
import { erpModules } from '~/utils/erp'

const route = useRoute()

function isActive(moduleKey: string) {
  return route.path.startsWith(`/module/${moduleKey}`)
}
</script>

<template>
  <nav class="flex items-center gap-2 overflow-x-auto pb-1">
    <NuxtLink to="/" class="erp-menu-link" :class="route.path === '/' ? 'erp-menu-link--active' : ''">
      Overview
    </NuxtLink>

    <NuxtLink
      v-for="module in erpModules"
      :key="module.key"
      :to="`/module/${module.key}`"
      class="erp-menu-link"
      :class="isActive(module.key) ? 'erp-menu-link--active' : ''"
    >
      {{ module.label }}
    </NuxtLink>
  </nav>
</template>
