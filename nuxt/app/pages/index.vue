<script setup lang="ts">
import { dashboardSnapshots, erpModules, getEntityPath } from '~/utils/erp'

interface SnapshotResponse {
  count: number
  results: Record<string, unknown>[]
}

interface SnapshotState {
  title: string
  count: number | null
  items: Record<string, unknown>[]
  error: string
}

const { user, isAuthenticated } = useErpSession()

const snapshotState = ref<Record<string, SnapshotState>>({})
const snapshotsPending = ref(false)

const totalEntities = computed(() => erpModules.reduce((sum, module) => sum + module.entities.length, 0))
const userName = computed(() => {
  const fullName = [user.value?.first_name, user.value?.last_name].filter(Boolean).join(' ')
  return fullName || user.value?.email || 'ERP operator'
})

function snapshotId(moduleKey: string, entityKey: string) {
  return `${moduleKey}:${entityKey}`
}

async function loadSnapshots() {
  if (!isAuthenticated.value) {
    snapshotState.value = {}
    return
  }

  snapshotsPending.value = true

  try {
    const results = await Promise.all(dashboardSnapshots.map(async snapshot => {
      const id = snapshotId(snapshot.moduleKey, snapshot.entityKey)
      const path = getEntityPath(snapshot.moduleKey, snapshot.entityKey)

      try {
        const response = await $fetch<SnapshotResponse>(`/api/backend/${path}/`, {
          query: { page_size: 5 }
        })

        return [id, {
          title: snapshot.title,
          count: response.count,
          items: response.results,
          error: ''
        } satisfies SnapshotState] as const
      } catch (error: any) {
        return [id, {
          title: snapshot.title,
          count: null,
          items: [],
          error: error?.data?.detail ?? error?.statusMessage ?? 'Unable to load this endpoint.'
        } satisfies SnapshotState] as const
      }
    }))

    snapshotState.value = Object.fromEntries(results)
  } finally {
    snapshotsPending.value = false
  }
}

watch(() => isAuthenticated.value, async authenticated => {
  if (authenticated) {
    await loadSnapshots()
    return
  }

  snapshotState.value = {}
}, { immediate: true })

useSeoMeta({
  title: 'ERP Overview',
  description: 'Dashboard overview for the ERP Django REST backend.'
})
</script>

<template>
  <div class="space-y-6">
    <section class="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
      <div class="erp-surface overflow-hidden p-7 lg:p-9">
        <div class="absolute inset-x-0 top-0 h-40 bg-gradient-to-r from-emerald-400/30 via-cyan-300/10 to-amber-300/20 blur-3xl" />

        <div class="relative space-y-6">
          <div class="space-y-3">
            <p class="text-sm font-semibold uppercase tracking-[0.3em] text-emerald-700">
              DRF-driven frontend
            </p>

            <h1 class="max-w-3xl text-4xl font-semibold leading-tight text-slate-950 sm:text-5xl">
              Nuxt control surface for the live ERP backend.
            </h1>

            <p class="max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
              The frontend is wired against the mounted Django REST apps for company, contact, party, department, accounts, HRM and CRM. Sign in to browse paginated records through Nuxt server routes.
            </p>
          </div>

          <div class="grid gap-4 sm:grid-cols-3">
            <div class="rounded-3xl border border-white/70 bg-white/70 p-5 shadow-sm">
              <p class="text-sm text-slate-500">Mounted modules</p>
              <p class="mt-2 text-3xl font-semibold text-slate-950">{{ erpModules.length }}</p>
            </div>

            <div class="rounded-3xl border border-white/70 bg-white/70 p-5 shadow-sm">
              <p class="text-sm text-slate-500">Mapped endpoints</p>
              <p class="mt-2 text-3xl font-semibold text-slate-950">{{ totalEntities }}</p>
            </div>

            <div class="rounded-3xl border border-white/70 bg-white/70 p-5 shadow-sm">
              <p class="text-sm text-slate-500">Session state</p>
              <p class="mt-2 text-3xl font-semibold text-slate-950">{{ isAuthenticated ? 'Live' : 'Guest' }}</p>
            </div>
          </div>

          <div class="flex flex-wrap gap-3">
            <NuxtLink to="/module/company" class="erp-button text-center no-underline">
              Browse modules
            </NuxtLink>

            <a href="http://127.0.0.1:8000/api/v1/docs/" target="_blank" rel="noreferrer" class="erp-button erp-button--secondary text-center no-underline">
              Open DRF docs
            </a>
          </div>
        </div>
      </div>

      <ErpLoginPanel v-if="!isAuthenticated" @success="loadSnapshots" />

      <section v-else class="erp-surface p-6 lg:p-7">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
          Current session
        </p>

        <div class="mt-4 space-y-4">
          <div>
            <h2 class="text-2xl font-semibold text-slate-950">
              Welcome back, {{ userName }}
            </h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Your session is now backed by Django JWT cookies on the Nuxt server. Use the module explorer to inspect paginated resources and verify backend data quickly.
            </p>
          </div>

          <dl class="grid gap-3 text-sm text-slate-700">
            <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
              <dt>Email</dt>
              <dd class="font-medium">{{ user?.email }}</dd>
            </div>
            <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
              <dt>User type</dt>
              <dd class="font-medium capitalize">{{ user?.user_type }}</dd>
            </div>
            <div class="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
              <dt>Primary company</dt>
              <dd class="font-medium">{{ user?.company || 'Unassigned' }}</dd>
            </div>
          </dl>
        </div>
      </section>
    </section>

    <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <NuxtLink
        v-for="module in erpModules"
        :key="module.key"
        :to="`/module/${module.key}`"
        class="erp-surface group block overflow-hidden p-6 no-underline transition-transform duration-200 hover:-translate-y-1"
      >
        <div class="h-24 rounded-3xl bg-gradient-to-br" :class="module.accent" />

        <div class="mt-5 flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">{{ module.key }}</p>
            <h2 class="mt-2 text-2xl font-semibold text-slate-950">{{ module.label }}</h2>
          </div>

          <span class="rounded-2xl bg-slate-950 px-3 py-2 text-xs font-medium uppercase tracking-[0.2em] text-white">
            {{ module.entities.length }} endpoints
          </span>
        </div>

        <p class="mt-3 text-sm leading-6 text-slate-600">
          {{ module.description }}
        </p>
      </NuxtLink>
    </section>

    <section class="grid gap-6 xl:grid-cols-2">
      <ErpEntityTable
        v-for="snapshot in dashboardSnapshots"
        :key="snapshotId(snapshot.moduleKey, snapshot.entityKey)"
        :title="snapshot.title"
        :description="`Previewing ${snapshot.moduleKey}/${snapshot.entityKey}`"
        :columns="erpModules.find(module => module.key === snapshot.moduleKey)?.entities.find(entity => entity.key === snapshot.entityKey)?.columns || []"
        :items="snapshotState[snapshotId(snapshot.moduleKey, snapshot.entityKey)]?.items || []"
        :count="snapshotState[snapshotId(snapshot.moduleKey, snapshot.entityKey)]?.count ?? null"
        :pending="snapshotsPending && !snapshotState[snapshotId(snapshot.moduleKey, snapshot.entityKey)]"
        :error="snapshotState[snapshotId(snapshot.moduleKey, snapshot.entityKey)]?.error || (!isAuthenticated ? 'Sign in to preview live data.' : '')"
      />
    </section>
  </div>
</template>
