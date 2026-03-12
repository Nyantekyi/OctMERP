<script setup lang="ts">
definePageMeta({
  layout: 'default'
})

const stats = [
  {
    label: 'Open Sales Orders',
    value: '148',
    icon: 'i-lucide-shopping-cart',
    tone: 'text-emerald-600'
  },
  {
    label: 'Warehouse Fill Rate',
    value: '92%',
    icon: 'i-lucide-package-check',
    tone: 'text-cyan-600'
  },
  {
    label: 'Pending QA Batches',
    value: '17',
    icon: 'i-lucide-flask-conical',
    tone: 'text-amber-600'
  },
  {
    label: 'Payroll Cycle Status',
    value: 'In Review',
    icon: 'i-lucide-briefcase-business',
    tone: 'text-indigo-600'
  }
]
</script>

<template>
  <div class="space-y-6">
    <UCard class="relative overflow-hidden">
      <div class="absolute inset-0 bg-[radial-gradient(65%_120%_at_0%_0%,rgba(20,184,166,0.22),transparent_60%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(55%_80%_at_100%_100%,rgba(14,116,144,0.2),transparent_60%)]" />
      <div class="relative space-y-2">
        <p class="text-sm text-muted">Control Tower</p>
        <h1 class="text-2xl font-semibold tracking-tight sm:text-3xl">
          Pharmaceutical ERP Dashboard
        </h1>
        <p class="max-w-2xl text-sm text-muted sm:text-base">
          Monitor inventory, logistics, quality control, payroll, and customer activity in one operational view.
        </p>
      </div>
    </UCard>

    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <UCard
        v-for="stat in stats"
        :key="stat.label"
        class="group"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-wide text-muted">
              {{ stat.label }}
            </p>
            <p class="mt-2 text-2xl font-semibold">
              {{ stat.value }}
            </p>
          </div>
          <UIcon
            :name="stat.icon"
            class="h-5 w-5 transition-transform duration-200 group-hover:scale-110"
            :class="stat.tone"
          />
        </div>
      </UCard>
    </div>

    <UCard>
      <template #header>
        <div class="flex items-center justify-between gap-4">
          <p class="text-base font-semibold">Quick Actions</p>
          <UBadge color="primary" variant="soft">Live</UBadge>
        </div>
      </template>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <UButton to="/sign-in" icon="i-lucide-lock-keyhole" variant="soft" color="primary">
          Open Auth Flow
        </UButton>
        <UButton icon="i-lucide-package-plus" variant="soft" color="neutral">
          Create Inventory Item
        </UButton>
        <UButton icon="i-lucide-user-plus" variant="soft" color="neutral">
          Add Employee
        </UButton>
      </div>
    </UCard>
  </div>
 </template>
