export interface ErpEntityConfig {
  key: string
  label: string
  path: string
  description: string
  columns: string[]
}

export interface ErpModuleConfig {
  key: string
  label: string
  icon: string
  accent: string
  description: string
  entities: ErpEntityConfig[]
}

const makeEntity = (
  key: string,
  label: string,
  path: string,
  description: string,
  columns: string[]
): ErpEntityConfig => ({
  key,
  label,
  path,
  description,
  columns
})

export const erpModules: ErpModuleConfig[] = [
  {
    key: 'company',
    label: 'Company',
    icon: 'i-lucide-building-2',
    accent: 'from-emerald-500/25 via-emerald-400/10 to-transparent',
    description: 'Tenant bootstrap, company setup, subscription classes and domain routing.',
    entities: [
      makeEntity('industries', 'Industries', 'company/industries', 'Classify companies by industry.', ['name', 'description', 'is_active']),
      makeEntity('payment-classes', 'Payment Classes', 'company/payment-classes', 'Subscription and payment tiers.', ['name', 'is_active', 'created_at']),
      makeEntity('business-types', 'Business Types', 'company/business-types', 'Retail, wholesale, manufacturing and related types.', ['name', 'is_active', 'created_at']),
      makeEntity('companies', 'Companies', 'company/companies', 'Main tenant companies connected to users and contacts.', ['name', 'slug', 'default_currency', 'industry']),
      makeEntity('domains', 'Domains', 'company/domains', 'Custom domains assigned to companies.', ['domain', 'company', 'is_primary'])
    ]
  },
  {
    key: 'contact',
    label: 'Contact',
    icon: 'i-lucide-map-pinned',
    accent: 'from-sky-500/25 via-cyan-400/10 to-transparent',
    description: 'Geographic reference data and reusable contact channels for the ERP.',
    entities: [
      makeEntity('countries', 'Countries', 'contact/countries', 'Country master data.', ['name', 'iso2', 'iso3', 'currency']),
      makeEntity('states', 'States', 'contact/states', 'States and provinces grouped by country.', ['name', 'country', 'state_code']),
      makeEntity('cities', 'Cities', 'contact/cities', 'City directory for addresses.', ['name', 'state', 'created_at']),
      makeEntity('address-types', 'Address Types', 'contact/address-types', 'Address purpose taxonomy.', ['name', 'is_active', 'created_at']),
      makeEntity('phone-types', 'Phone Types', 'contact/phone-types', 'Phone type taxonomy.', ['name', 'is_active', 'created_at']),
      makeEntity('email-types', 'Email Types', 'contact/email-types', 'Email type taxonomy.', ['name', 'is_active', 'created_at']),
      makeEntity('web-types', 'Web Types', 'contact/web-types', 'Website and web handle taxonomy.', ['name', 'is_active', 'created_at']),
      makeEntity('phones', 'Phones', 'contact/phones', 'Phone numbers attached to business objects.', ['phone', 'phonetype', 'is_whatsapp']),
      makeEntity('addresses', 'Addresses', 'contact/addresses', 'Structured addresses for branches and contacts.', ['line', 'city', 'postal_code', 'addresstype']),
      makeEntity('emails', 'Emails', 'contact/emails', 'Email addresses attached to business objects.', ['email', 'emailType', 'created_at']),
      makeEntity('websites', 'Websites', 'contact/websites', 'Website and social links.', ['website', 'webtype', 'created_at']),
      makeEntity('contacts', 'Contacts', 'contact/contacts', 'Generic contact wrappers used throughout the ERP.', ['content_type', 'contact_id', 'is_verified']),
      makeEntity('document-types', 'Document Types', 'contact/document-types', 'Typed document buckets.', ['name', 'description', 'created_at']),
      makeEntity('documents', 'Documents', 'contact/documents', 'Stored documents and uploaded references.', ['document_type', 'document_url', 'description'])
    ]
  },
  {
    key: 'party',
    label: 'Party',
    icon: 'i-lucide-users-round',
    accent: 'from-orange-500/25 via-amber-400/10 to-transparent',
    description: 'Users, occupations, staff, clients and vendors authenticated through JWT.',
    entities: [
      makeEntity('users', 'Users', 'party/users', 'Core ERP users with company and role assignments.', ['email', 'first_name', 'last_name', 'user_type']),
      makeEntity('occupations', 'Occupations', 'party/occupations', 'Occupation lookup used by staff profiles.', ['name', 'definition', 'created_at']),
      makeEntity('staff', 'Staff', 'party/staff', 'Staff profiles linked to users and branches.', ['user', 'occupation', 'is_manager', 'employee_id']),
      makeEntity('clients', 'Clients', 'party/clients', 'Client profiles linked to departments.', ['user', 'department', 'loyalty_points']),
      makeEntity('vendors', 'Vendors', 'party/vendors', 'Vendor profiles and department assignments.', ['vendorname', 'user', 'department'])
    ]
  },
  {
    key: 'department',
    label: 'Department',
    icon: 'i-lucide-network',
    accent: 'from-fuchsia-500/20 via-pink-400/10 to-transparent',
    description: 'Department, branch and facility management for operational structure.',
    entities: [
      makeEntity('departments', 'Departments', 'department/departments', 'Commercial and operational departments.', ['name', 'departmenttype', 'is_saledepartment', 'staff']),
      makeEntity('branches', 'Branches', 'department/branches', 'Branches and warehouses under departments.', ['name', 'department', 'is_warehouse', 'staff']),
      makeEntity('shifts', 'Shifts', 'department/shifts', 'Shift templates used by scheduling.', ['shift_types', 'department', 'start_time', 'end_time']),
      makeEntity('rooms', 'Rooms', 'department/rooms', 'Rooms, meeting spaces and controlled areas.', ['name', 'status', 'capacity', 'location']),
      makeEntity('shelves', 'Shelves', 'department/shelves', 'Shelf and storage locations.', ['shelf', 'branch', 'room'])
    ]
  },
  {
    key: 'accounts',
    label: 'Accounts',
    icon: 'i-lucide-landmark',
    accent: 'from-violet-500/20 via-indigo-400/10 to-transparent',
    description: 'Double-entry accounting, banks, budgets, taxes and transaction requests.',
    entities: [
      makeEntity('charts-of-account', 'Charts of Account', 'accounts/charts-of-account', 'Account families for the chart of accounts.', ['name', 'acc_number', 'account_type']),
      makeEntity('accounts', 'Accounts', 'accounts/accounts', 'Operational accounts attached to ERP objects.', ['name', 'accounttype', 'created_at']),
      makeEntity('transaction-docs', 'Transaction Docs', 'accounts/transaction-docs', 'Transaction document headers.', ['title', 'description', 'created_at']),
      makeEntity('transactions', 'Transactions', 'accounts/transactions', 'Debit and credit ledger entries.', ['notes', 'account', 'entry_type', 'amount']),
      makeEntity('banks', 'Banks', 'accounts/banks', 'Bank master data.', ['name', 'is_active', 'created_at']),
      makeEntity('bank-accounts', 'Bank Accounts', 'accounts/bank-accounts', 'Company and staff bank accounts.', ['bank', 'account_number', 'account_name']),
      makeEntity('taxes', 'Taxes', 'accounts/taxes', 'Tax rates used across sales and payroll.', ['name', 'rate', 'description']),
      makeEntity('budget-types', 'Budget Types', 'accounts/budget-types', 'Budget categories by department.', ['name', 'department', 'created_at']),
      makeEntity('budget-requests', 'Budget Requests', 'accounts/budget-requests', 'Budget requests raised by staff.', ['budget_type', 'requested_by', 'amount', 'status']),
      makeEntity('budget-allocations', 'Budget Allocations', 'accounts/budget-allocations', 'Approved budget allocations.', ['budget_request', 'allocated_by', 'amount']),
      makeEntity('expense-types', 'Expense Types', 'accounts/expense-types', 'Expense categories for branch reporting.', ['name', 'created_at', 'is_active']),
      makeEntity('expense-reports', 'Expense Reports', 'accounts/expense-reports', 'Recorded branch expenses.', ['expense_type', 'branch', 'amount', 'incurred_on']),
      makeEntity('transaction-request-types', 'Transaction Request Types', 'accounts/transaction-request-types', 'Workflow categories for finance requests.', ['name', 'created_at', 'is_active']),
      makeEntity('transaction-requests', 'Transaction Requests', 'accounts/transaction-requests', 'Requested financial operations awaiting processing.', ['transaction_type', 'amount', 'status'])
    ]
  },
  {
    key: 'hrm',
    label: 'HRM',
    icon: 'i-lucide-briefcase-business',
    accent: 'from-rose-500/20 via-red-400/10 to-transparent',
    description: 'Human resources, scheduling, payroll, leave and performance tracking.',
    entities: [
      makeEntity('skills', 'Skills', 'hrm/skills', 'Employee skill library.', ['name', 'description', 'created_at']),
      makeEntity('holidays', 'Holidays', 'hrm/holidays', 'Public and internal holiday calendar.', ['name', 'date', 'is_public', 'country']),
      makeEntity('meeting-subjects', 'Meeting Subjects', 'hrm/meeting-subjects', 'Meeting subject definitions.', ['subject', 'staff', 'created_at']),
      makeEntity('meetings', 'Meetings', 'hrm/meetings', 'Scheduled internal meetings.', ['subject', 'room', 'date', 'status']),
      makeEntity('vacancies', 'Vacancies', 'hrm/vacancies', 'Open vacancy records.', ['title', 'department', 'closing_date', 'is_filled']),
      makeEntity('deductions', 'Deductions', 'hrm/deductions', 'Payroll deduction rules.', ['name', 'deduction_type', 'deduction', 'frequency']),
      makeEntity('benefits', 'Benefits', 'hrm/benefits', 'Payroll benefit rules.', ['name', 'benefit_rate_type', 'benefit', 'frequency']),
      makeEntity('employees', 'Employees', 'hrm/employees', 'Employee management records.', ['staff', 'position', 'date_hired', 'is_employed']),
      makeEntity('employee-salary-rules', 'Salary Rules', 'hrm/employee-salary-rules', 'Per-employee salary rules.', ['employee', 'notes', 'created_at']),
      makeEntity('employee-severance-packages', 'Severance Packages', 'hrm/employee-severance-packages', 'Employee severance setup.', ['employee', 'amount', 'created_at']),
      makeEntity('employee-deductions', 'Employee Deductions', 'hrm/employee-deductions', 'Assigned deductions per employee.', ['employee', 'deduction', 'created_at']),
      makeEntity('employee-benefits', 'Employee Benefits', 'hrm/employee-benefits', 'Assigned benefits per employee.', ['employee', 'benefit', 'created_at']),
      makeEntity('employee-skills', 'Employee Skills', 'hrm/employee-skills', 'Mapped employee skills and proficiency.', ['employee', 'skill', 'proficiency_level', 'years_of_experience']),
      makeEntity('employee-bank-details', 'Bank Details', 'hrm/employee-bank-details', 'Bank details for salary payments.', ['employee', 'bank', 'account_number', 'account_name']),
      makeEntity('leave-types', 'Leave Types', 'hrm/leave-types', 'Leave policy setup.', ['name', 'is_paid', 'department', 'max_days_allowed']),
      makeEntity('leaves', 'Leaves', 'hrm/leaves', 'Submitted leave requests.', ['staff', 'leave_type', 'start_date', 'status']),
      makeEntity('leave-balances', 'Leave Balances', 'hrm/leave-balances', 'Remaining leave balances by year.', ['employee', 'leave_type', 'year', 'remaining_days']),
      makeEntity('scheduled-shifts', 'Scheduled Shifts', 'hrm/scheduled-shifts', 'Scheduled employee shifts.', ['employee', 'shift', 'branch', 'start_date']),
      makeEntity('attendance', 'Attendance', 'hrm/attendance', 'Attendance records by day.', ['employee', 'branch', 'date', 'status']),
      makeEntity('overtime', 'Overtime', 'hrm/overtime', 'Overtime requests and approvals.', ['attendance', 'requested_hours', 'status', 'requested_by']),
      makeEntity('loan-types', 'Loan Types', 'hrm/loan-types', 'Employee loan policy types.', ['name', 'interest_rate', 'max_loan_amount', 'max_repayment_period_months']),
      makeEntity('staff-loans', 'Staff Loans', 'hrm/staff-loans', 'Granted staff loans.', ['employee', 'loan_type', 'loan_amount', 'status']),
      makeEntity('payrolls', 'Payrolls', 'hrm/payrolls', 'Payroll runs and status.', ['date', 'staff', 'status', 'total_net_salary']),
      makeEntity('payroll-details', 'Payroll Details', 'hrm/payroll-details', 'Per-employee payroll lines.', ['payroll', 'employee', 'status', 'net_salary']),
      makeEntity('performance-evaluations', 'Performance Evaluations', 'hrm/performance-evaluations', 'Employee performance reviews.', ['employee', 'evaluator', 'date', 'score'])
    ]
  },
  {
    key: 'crm',
    label: 'CRM',
    icon: 'i-lucide-chart-column-big',
    accent: 'from-cyan-500/20 via-sky-400/10 to-transparent',
    description: 'Sales pipeline, campaigns, prospects and deal tracking.',
    entities: [
      makeEntity('territories', 'Territories', 'crm/territories', 'Geographic or market territories.', ['name', 'branch', 'parent_territory']),
      makeEntity('sale-teams', 'Sale Teams', 'crm/sale-teams', 'Sales teams aligned to territories.', ['name', 'territory', 'department', 'monthly_target']),
      makeEntity('sale-members', 'Sale Members', 'crm/sale-members', 'Staff assigned into sales teams.', ['team', 'staff', 'role']),
      makeEntity('pipelines', 'Pipelines', 'crm/pipelines', 'Named sales pipelines.', ['name', 'department', 'created_at']),
      makeEntity('stages', 'Stages', 'crm/stages', 'Stages within each pipeline.', ['pipeline', 'name', 'order', 'probability']),
      makeEntity('pipeline-transitions', 'Pipeline Transitions', 'crm/pipeline-transitions', 'Allowed stage transitions.', ['from_stage', 'to_stage', 'requires_approval']),
      makeEntity('campaigns', 'Campaigns', 'crm/campaigns', 'Marketing and outbound campaigns.', ['name', 'campaign_type', 'status', 'team']),
      makeEntity('prospect-companies', 'Prospect Companies', 'crm/prospect-companies', 'Prospect organizations.', ['name', 'industry', 'country', 'assigned_team']),
      makeEntity('prospects', 'Prospects', 'crm/prospects', 'Individual leads and contacts.', ['first_name', 'last_name', 'source', 'assigned_to']),
      makeEntity('prospect-pipeline-stages', 'Prospect Pipeline Stages', 'crm/prospect-pipeline-stages', 'Prospect placement in the pipeline.', ['prospect', 'pipeline', 'current_stage', 'entered_stage_on']),
      makeEntity('deals', 'Deals', 'crm/deals', 'Revenue opportunities and forecasted deals.', ['name', 'pipeline', 'current_stage', 'expected_revenue'])
    ]
  }
]

export const dashboardSnapshots = [
  { moduleKey: 'company', entityKey: 'companies', title: 'Tenant companies' },
  { moduleKey: 'party', entityKey: 'users', title: 'Platform users' },
  { moduleKey: 'department', entityKey: 'branches', title: 'Operational branches' },
  { moduleKey: 'accounts', entityKey: 'transactions', title: 'Recent transactions' },
  { moduleKey: 'hrm', entityKey: 'employees', title: 'Employee records' },
  { moduleKey: 'crm', entityKey: 'deals', title: 'CRM deals' }
]

export function findModuleConfig(moduleKey: string) {
  return erpModules.find(module => module.key === moduleKey) ?? null
}

export function findEntityConfig(moduleKey: string, entityKey: string) {
  return findModuleConfig(moduleKey)?.entities.find(entity => entity.key === entityKey) ?? null
}

export function getEntityPath(moduleKey: string, entityKey: string) {
  return findEntityConfig(moduleKey, entityKey)?.path ?? ''
}
