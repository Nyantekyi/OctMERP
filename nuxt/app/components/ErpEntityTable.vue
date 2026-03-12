<script setup lang="ts">
interface Props {
  title: string
  description?: string
  columns: string[]
  items: Record<string, unknown>[]
  count?: number | null
  pending?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  count: null,
  pending: false,
  error: ''
})

function humanise(column: string) {
  return column
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase())
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return '—'
  }

  if (Array.isArray(value)) {
    return value.length
      ? value.slice(0, 3).map(item => formatValue(item)).join(', ')
      : '[]'
  }

  if (typeof value === 'object') {
    const record = value as Record<string, unknown>

    for (const key of ['name', 'title', 'email', 'username', 'id']) {
      if (typeof record[key] === 'string' && record[key]) {
        return record[key] as string
      }
    }

    return JSON.stringify(record)
  }

  return String(value)
}
</script>

<template>
  <section class="erp-surface p-6 lg:p-7">
    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div class="space-y-2">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
          Live DRF Records
        </p>

        <div>
          <h3 class="text-xl font-semibold text-slate-950">
            {{ props.title }}
          </h3>

          <p v-if="props.description" class="mt-1 max-w-2xl text-sm text-slate-600">
            {{ props.description }}
          </p>
        </div>
      </div>

      <div v-if="props.count !== null" class="erp-pill text-sm font-medium text-slate-700">
        {{ props.count }} records
      </div>
    </div>

    <div v-if="props.pending" class="mt-6 rounded-3xl border border-dashed border-slate-300/80 bg-white/60 px-4 py-8 text-sm text-slate-500">
      Loading data from Django REST Framework...
    </div>

    <div v-else-if="props.error" class="mt-6 rounded-3xl border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
      {{ props.error }}
    </div>

    <div v-else-if="!props.items.length" class="mt-6 rounded-3xl border border-dashed border-slate-300/80 bg-white/60 px-4 py-8 text-sm text-slate-500">
      No records returned yet for this endpoint.
    </div>

    <div v-else class="mt-6 overflow-x-auto rounded-3xl border border-slate-200/80 bg-white/75">
      <table class="min-w-full border-collapse text-left text-sm">
        <thead class="bg-slate-950 text-slate-100">
          <tr>
            <th v-for="column in props.columns" :key="column" class="px-4 py-3 font-medium">
              {{ humanise(column) }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(item, itemIndex) in props.items"
            :key="String(item.id ?? itemIndex)"
            class="border-t border-slate-200/80 align-top text-slate-700"
          >
            <td v-for="column in props.columns" :key="column" class="px-4 py-3">
              <span class="line-clamp-2">
                {{ formatValue(item[column]) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
