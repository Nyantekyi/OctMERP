<script setup lang="ts">
import type {
  AccountingEntry,
  Lead,
  SharedAnnouncement,
  TenantFeatures,
  WorkOrder,
} from "~/types/api"

const {
  getSharedAnnouncements,
  getTenantFeatures,
  getAccountingEntries,
  getLeads,
  getWorkOrders,
} = useTenantApi()

const sharedAnnouncements = ref<SharedAnnouncement[]>([])
const features = ref<TenantFeatures | null>(null)
const accountingEntries = ref<AccountingEntry[]>([])
const leads = ref<Lead[]>([])
const workOrders = ref<WorkOrder[]>([])
const errorMessage = ref("")

const enabled = computed(() => new Set(features.value?.enabled_modules ?? []))

const loadDashboard = async () => {
  errorMessage.value = ""

  try {
    sharedAnnouncements.value = await getSharedAnnouncements()
    features.value = await getTenantFeatures()
    accountingEntries.value = enabled.value.has("accounting") ? await getAccountingEntries() : []
    leads.value = enabled.value.has("crm") ? await getLeads() : []
    workOrders.value = enabled.value.has("manufacturing") ? await getWorkOrders() : []
  } catch (error) {
    errorMessage.value =
      "Could not load tenant data. Make sure this Nuxt app is using a tenant domain that exists in Django."
    console.error(error)
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <main class="page">
    <section class="card hero">
      <h1>Tenant Feature Dashboard</h1>
      <p>
        This UI follows tenant boundaries from Django: shared data is global, accounting is company-scoped,
        and specialized modules are enabled by company type.
      </p>
      <button @click="loadDashboard">Refresh</button>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </section>

    <section v-if="features" class="card">
      <h2>Active Tenant</h2>
      <p><strong>Company:</strong> {{ features.company_name }}</p>
      <p><strong>Schema:</strong> {{ features.schema_name }}</p>
      <p><strong>Type:</strong> {{ features.company_type }}</p>
      <p><strong>Enabled modules:</strong> {{ features.enabled_modules.join(", ") }}</p>
    </section>

    <section class="card">
      <h2>Shared Across Companies</h2>
      <ul>
        <li v-for="note in sharedAnnouncements" :key="note.id">
          <strong>{{ note.title }}</strong>: {{ note.body }}
        </li>
      </ul>
    </section>

    <section class="card" v-if="enabled.has('accounting')">
      <h2>Accounting (Tenant Scoped)</h2>
      <ul>
        <li v-for="entry in accountingEntries" :key="entry.id">
          {{ entry.entry_date }} - {{ entry.description }} - {{ entry.amount }} {{ entry.currency }}
        </li>
      </ul>
    </section>

    <section class="card" v-if="enabled.has('crm')">
      <h2>CRM (Specialized)</h2>
      <ul>
        <li v-for="lead in leads" :key="lead.id">
          {{ lead.name }} ({{ lead.stage }})
        </li>
      </ul>
    </section>

    <section class="card" v-if="enabled.has('manufacturing')">
      <h2>Manufacturing (Specialized)</h2>
      <ul>
        <li v-for="order in workOrders" :key="order.id">
          {{ order.title }} - qty {{ order.quantity }} - {{ order.status }}
        </li>
      </ul>
    </section>
  </main>
</template>
