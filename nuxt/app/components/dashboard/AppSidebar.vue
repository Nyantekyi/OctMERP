<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const props = withDefaults(defineProps<{
  collapsed?: boolean
  items: NavigationMenuItem[][]
}>(), {
  collapsed: false
})

const emit = defineEmits<{
  toggle: [boolean]
}>()

const navigationItems = computed<NavigationMenuItem[][]>(() => {
  if (!props.collapsed) {
    return props.items
  }

  return props.items.map(group =>
    group.map(item => ({
      ...item,
      label: ''
    }))
  )
})
</script>

<template>
  <UCard
    class="m-2 h-[calc(100vh-1rem)] border-r border-default/80 bg-default/80 backdrop-blur-sm transition-all duration-200"
    :class="props.collapsed ? 'w-20' : 'w-72'"
    :ui="{
      body: 'p-2 sm:p-2 h-full flex flex-col',
      root: 'rounded-2xl'
    }"
  >
    <div class="mb-2 flex h-10 items-center justify-between gap-2 px-1">
      <NuxtLink
        to="/"
        class="inline-flex items-center gap-2 px-2 text-sm font-semibold tracking-tight"
      >
        <UIcon name="i-lucide-pill" class="h-4 w-4 text-primary" />
        <span v-if="!props.collapsed">Pharma ERP</span>
      </NuxtLink>

      <UButton
        variant="ghost"
        color="neutral"
        size="xs"
        icon="i-lucide-panel-left"
        :aria-label="props.collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="emit('toggle', !props.collapsed)"
      />
    </div>

    <USeparator class="mb-2" />

    <div class="min-h-0 flex-1 overflow-y-auto">
      <UNavigationMenu
        orientation="vertical"
        :items="navigationItems"
        :ui="{
          viewport: 'hidden',
          link: props.collapsed ? 'justify-center px-0' : undefined,
          linkLeadingIcon: 'size-5'
        }"
      />
    </div>

    <USeparator class="my-2" />

    <div class="flex items-center justify-between gap-2 px-1">
      <UBadge
        v-if="!props.collapsed"
        color="primary"
        variant="subtle"
      >
        Live
      </UBadge>
      <UButton
        to="/sign-in"
        color="neutral"
        variant="soft"
        icon="i-lucide-log-in"
        :label="props.collapsed ? undefined : 'Sign In'"
        class="w-full"
      />
    </div>
  </UCard>
</template>

<style scoped></style>
