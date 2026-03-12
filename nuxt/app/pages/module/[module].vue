<script setup lang="ts">
import type { ErpEntityConfig } from '~/utils/erp'
import { findModuleConfig } from '~/utils/erp'

interface PaginatedResponse {
  count: number
  total_pages?: number
  next?: string | null
  previous?: string | null
  results: Record<string, unknown>[]
}

const route = useRoute()
const { isAuthenticated } = useErpSession()

const moduleKey = computed(() => String(route.params.module ?? ''))
const moduleConfig = computed(() => findModuleConfig(moduleKey.value))

if (!moduleConfig.value) {
  throw createError({
    statusCode: 404,
    statusMessage: 'ERP module not found.'
  })
}

const selectedEntityKey = computed(() => {
  const rawValue = route.query.entity

  if (typeof rawValue === 'string' && rawValue) {
    return rawValue
  }

  if (Array.isArray(rawValue) && rawValue[0]) {
    return rawValue[0]
  }

  return moduleConfig.value?.entities[0]?.key ?? ''
})

const selectedEntity = computed<ErpEntityConfig | null>(() => {
  return moduleConfig.value?.entities.find(entity => entity.key === selectedEntityKey.value) ?? null
})

const search = ref('')
const ordering = ref('')
const page = ref(1)
const pending = ref(false)
const errorMessage = ref('')
const response = ref<PaginatedResponse | null>(null)

const canLoad = computed(() => Boolean(isAuthenticated.value && selectedEntity.value))

async function loadEntity() {
  if (!canLoad.value || !selectedEntity.value) {
    response.value = null
    return
  }

  pending.value = true
  errorMessage.value = ''

  try {
    response.value = await $fetch<PaginatedResponse>(`/api/backend/${selectedEntity.value.path}/`, {
      query: {
        page: page.value,
        page_size: 10,
        search: search.value || undefined,
        ordering: ordering.value || undefined
      }
    })
  } catch (error: any) {
    response.value = null
    errorMessage.value = error?.data?.detail ?? error?.statusMessage ?? 'Unable to load records for this endpoint.'
  } finally {
    pending.value = false
  }
}

function selectEntity(entityKey: string) {
  page.value = 1

  navigateTo({
    path: route.path,
    query: { entity: entityKey }
  })
}

function runSearch() {
  page.value = 1
  loadEntity()
}

watch(() => selectedEntityKey.value, async () => {
  page.value = 1
  await loadEntity()
}, { immediate: true })

watch(() => page.value, async () => {
  await loadEntity()
})

useSeoMeta({
  title: `${moduleConfig.value.label} Module`,
  description: moduleConfig.value.description
})
</script>

<template>
  <div class="space-y-6">
    <section class="erp-surface p-7 lg:p-9">
      <div class="grid gap-8 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
        <div>
          <p class="text-sm font-semibold uppercase tracking-[0.3em] text-slate-500">
            ERP module
          </p>
          <h1 class="mt-3 text-4xl font-semibold text-slate-950">
            {{ moduleConfig?.label }}
          </h1>
          <p class="mt-3 max-w-3xl text-base leading-7 text-slate-600">
            {{ moduleConfig?.description }}
          </p>
        </div>

        <div class="rounded-[2rem] border border-slate-200/80 bg-white/70 p-5">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            Endpoint inventory
          </p>
          <p class="mt-2 text-3xl font-semibold text-slate-950">
            {{ moduleConfig?.entities.length }}
          </p>
          <p class="mt-2 text-sm text-slate-600">
            Each endpoint is proxied through Nuxt server routes and uses the DRF paginator shape from the backend.
          </p>
        </div>
      </div>
    </section>

    <div v-if="!isAuthenticated" class="erp-surface p-6 lg:p-7">
      <h2 class="text-2xl font-semibold text-slate-950">
        Sign in required
      </h2>
      <p class="mt-2 text-sm leading-6 text-slate-600">
        This module explorer queries authenticated DRF endpoints. Return to the overview page and sign in before browsing data.
      </p>
      <NuxtLink to="/" class="mt-5 inline-flex erp-button no-underline">
        Back to overview
      </NuxtLink>
    </div>

    <template v-else>
      <section class="grid gap-6 xl:grid-cols-[0.9fr_1.4fr]">
        <div class="erp-surface p-6 lg:p-7">
          <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            Endpoints
          </p>

          <div class="mt-5 grid gap-3">
            <button
              v-for="entity in moduleConfig?.entities"
              :key="entity.key"
              type="button"
              class="rounded-[1.5rem] border px-4 py-4 text-left transition-all duration-200"
              :class="selectedEntity?.key === entity.key ? 'border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-950/15' : 'border-slate-200 bg-white/70 text-slate-800 hover:border-slate-300'"
              @click="selectEntity(entity.key)"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-base font-semibold">
                    {{ entity.label }}
                  </p>
                  <p class="mt-1 text-sm leading-6" :class="selectedEntity?.key === entity.key ? 'text-slate-200' : 'text-slate-600'">
                    {{ entity.description }}
                  </p>
                </div>

                <span class="rounded-2xl px-3 py-2 text-xs font-medium uppercase tracking-[0.2em]" :class="selectedEntity?.key === entity.key ? 'bg-white/10 text-white' : 'bg-slate-100 text-slate-600'">
                  {{ entity.key }}
                </span>
              </div>
            </button>
          </div>
        </div>

        <div class="space-y-6">
          <section class="erp-surface p-6 lg:p-7">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                  Query endpoint
                </p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-950">
                  {{ selectedEntity?.label }}
                </h2>
                <p class="mt-2 text-sm leading-6 text-slate-600">
                  {{ selectedEntity?.description }}
                </p>
              </div>

              <div class="rounded-2xl bg-slate-950 px-4 py-3 text-sm text-white">
                /api/backend/{{ selectedEntity?.path }}/
              </div>
            </div>

            <form class="mt-6 grid gap-4 lg:grid-cols-[1fr_220px_auto]" @submit.prevent="runSearch">
              <input
                v-model="search"
                type="search"
                placeholder="Search endpoint data"
                class="erp-input"
              >

              <input
                v-model="ordering"
                type="text"
                placeholder="Ordering, e.g. name or -created_at"
                class="erp-input"
              >

              <button type="submit" class="erp-button">
                Apply
              </button>
            </form>
          </section>

          <ErpEntityTable
            :title="selectedEntity?.label || 'Entity preview'"
            :description="selectedEntity?.description || ''"
            :columns="selectedEntity?.columns || []"
            :items="response?.results || []"
            :count="response?.count ?? null"
            :pending="pending"
            :error="errorMessage"
          />

          <div class="erp-surface flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div class="text-sm text-slate-600">
              Page {{ page }}
              <span v-if="response?.total_pages"> of {{ response.total_pages }}</span>
            </div>

            <div class="flex gap-3">
              <button type="button" class="erp-button erp-button--secondary" :disabled="page <= 1 || pending" @click="page -= 1">
                Previous
              </button>

              <button
                type="button"
                class="erp-button erp-button--secondary"
                :disabled="!response?.next || pending"
                @click="page += 1"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
