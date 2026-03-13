export type Company = {
  id: number
  name: string
  schema_name: string
  company_type: string
  enabled_modules: string[]
}

export type TenantFeatures = {
  schema_name: string
  company_name: string
  company_type: string
  enabled_modules: string[]
}

export type SharedAnnouncement = {
  id: number
  title: string
  body: string
  is_active: boolean
  created_at: string
}

export type AccountingEntry = {
  id: number
  description: string
  amount: string
  currency: string
  entry_date: string
  created_at: string
}

export type Lead = {
  id: number
  name: string
  email: string
  stage: string
  created_at: string
}

export type WorkOrder = {
  id: number
  title: string
  status: string
  quantity: number
  due_date: string | null
  created_at: string
}
