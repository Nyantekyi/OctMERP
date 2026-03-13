import type {
  AccountingEntry,
  Company,
  Lead,
  SharedAnnouncement,
  TenantFeatures,
  WorkOrder,
} from "~/types/api"

export const useTenantApi = () => {
  const config = useRuntimeConfig()
  const apiBaseUrl = config.public.apiBaseUrl

  const getCompanies = () =>
    $fetch<Company[]>(`${apiBaseUrl}/api/public/companies/`)

  const getSharedAnnouncements = () =>
    $fetch<SharedAnnouncement[]>(`${apiBaseUrl}/api/public/shared-announcements/`)

  const getTenantFeatures = () =>
    $fetch<TenantFeatures>(`${apiBaseUrl}/api/tenant/features/`)

  const getAccountingEntries = () =>
    $fetch<AccountingEntry[]>(`${apiBaseUrl}/api/accounting/entries/`)

  const getLeads = () =>
    $fetch<Lead[]>(`${apiBaseUrl}/api/crm/leads/`)

  const getWorkOrders = () =>
    $fetch<WorkOrder[]>(`${apiBaseUrl}/api/manufacturing/work-orders/`)

  return {
    getCompanies,
    getSharedAnnouncements,
    getTenantFeatures,
    getAccountingEntries,
    getLeads,
    getWorkOrders,
  }
}
