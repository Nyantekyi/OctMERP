# Enterprise Resource Planning (ERP) System — Master Plan

> **Tech Stack:** Django 5.x + Django REST Framework (Backend) · Nuxt 3 + Nuxt UI / Reka UI (Frontend)
> **Date:** March 2026 · *Unified & reconciled with ref_models.md*

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Types & Permission Model](#2-user-types--permission-model)
3. [System Architecture](#3-system-architecture)
4. [Multi-Tenancy — Company Model](#4-multi-tenancy--company-model)
5. [Organisational Hierarchy — Department & Branch](#5-organisational-hierarchy--department--branch)
6. [Contact & Address System](#6-contact--address-system)
7. [Django Backend — Project Structure](#7-django-backend--project-structure)
8. [Django Apps & Models (Module by Module)](#8-django-apps--models-module-by-module)
   - 8.1 `apps/party` — Users & Profiles
   - 8.2 `apps/hr` — Human Resources & Payroll
   - 8.3 `apps/accounting` — Accounting, AR, AP, Budgeting
   - 8.4 `apps/inventory` — Inventory & Warehouse
   - 8.5 `apps/invplan` — Inventory Planning, PO Documents & Carriers
   - 8.6 `apps/procurement` — Purchasing & Vendor Management
   - 8.7 `apps/sales` — Sales Orders & Quotations
   - 8.8 `apps/crm` — CRM Module
   - 8.9 `apps/workflow` — Tasks & Workflows
   - 8.10 `apps/ecommerce` — E-Commerce Storefront
   - 8.11 `apps/pos` — Point of Sale
   - 8.12 `apps/manufacturing` — Manufacturing & MRP
   - 8.13 `apps/logistics` — Shipping & Delivery
   - 8.14 `apps/assets` — Fixed Asset Management
   - 8.15 `apps/projects` — Project Management
   - 8.16 `apps/reporting` — Reports, Dashboards & KPIs
   - 8.17 `apps/notifications` — Notification Centre
   - 8.18 `apps/agents` — AI Agent Core
9. [REST API Design Standards](#9-rest-api-design-standards)
10. [NuxtJS Frontend — Project Structure](#10-nuxtjs-frontend--project-structure)
11. [Frontend Pages & Routes (Module by Module)](#11-frontend-pages--routes-module-by-module)
12. [UI Component Architecture](#12-ui-component-architecture)
13. [State Management (Pinia)](#13-state-management-pinia)
14. [AI Agent Architecture](#14-ai-agent-architecture)
15. [Development Phases / Roadmap](#15-development-phases--roadmap)
16. [Infrastructure & DevOps](#16-infrastructure--devops)
17. [Security Considerations](#17-security-considerations)

---

## 1. Project Overview

A full-featured, **multi-tenant** ERP system serving four distinct actor types across modules spanning accounting, HR, inventory, procurement, sales, manufacturing, logistics, e-commerce, point-of-sale, CRM, asset management, project management, and AI-driven automation.

### Core Goals
- **Multi-tenancy via `django-tenants`** — each `Company` is a fully isolated tenant (separate PostgreSQL schema)
- Organisational hierarchy: **Company → Department → Branch** — all users, stock, transactions, and reports are scoped within this structure
- Unified backend API consumed by multiple frontend surfaces (staff portal, client portal, supplier portal, agent interface)
- Real-time updates (WebSockets / Django Channels) for dashboards, POS, and agent activity
- **Django built-in `Group` + `Permission` model** for RBAC; admin/superusers manage groups; `is_manager` flag on StaffProfile for manager elevation
- Autonomous AI agents that monitor, alert, draft, and act on behalf of staff
- Supplier visibility portal: product performance, stockout alerts, expiry warnings, demand forecasting
- Client-facing e-commerce store and order tracking
- Full offline-capable POS with sync-on-reconnect
- **Generic Contact system** (Phone, Email, Website, Address) linked to any model via ContentType
- **Signal-driven COA auto-seeding** on Company creation; account auto-creation on key model saves
- **Pharmacy / clinic readiness**: Ghana Card verification, expiry tracking, controlled substance handling

---

## 2. User Types & Permission Model

### 2.1 User Type Definitions

| Type | Description | Branch/Dept Assignment | Primary Surfaces |
|------|-------------|----------------------|----------------|
| **Staff** | Internal employees — regular staff, managers, admins, superusers | One or more **Branches** | Staff ERP Portal (all modules) |
| **Client** | Customers placing orders via e-commerce or POS | One **Department** only | Client Portal + E-Commerce Storefront |
| **Supplier** | Vendors, wholesalers, distributors, manufacturers | One **Department** only | Supplier Portal (read + collaboration) |
| **Agent** | Autonomous AI entities operating on the system | Not assigned | Agent Dashboard (staff-supervised) |

### 2.2 Django Groups — Predefined Permission Groups

```
Predefined Groups (seeded via data migration):
┌────────────────────────┬────────────────────────────────────────────────┐
│ Group Name             │ Typical Module Permissions                     │
├────────────────────────┼────────────────────────────────────────────────┤
│ Accountants            │ accounting.*  (full), all others read          │
│ HR Officers            │ hr.*  (full), party.* read                     │
│ Inventory Officers     │ inventory.* + procurement.*  (full)            │
│ Sales Representatives  │ sales.* + crm.* + pos.*  (full)               │
│ Warehouse Staff        │ inventory.* (update), logistics.*  (update)    │
│ IT Support             │ system logs, integrations, audit log           │
│ Viewers                │ read-only across all assigned modules          │
│ Procurement Officers   │ procurement.*  (full)                          │
│ Project Managers       │ projects.*  (full)                             │
│ Manufacturing Staff    │ manufacturing.*  (full)                        │
└────────────────────────┴────────────────────────────────────────────────┘
```

### 2.3 Manager Elevation (`is_manager`)

- `StaffProfile.is_manager = True` grants manager-level privilege **within the user's assigned branches**
- Managers can approve leave requests, purchase requisitions, payroll periods, budget requests, and quotations for their branches
- This augments (not replaces) the user's Group memberships

### 2.4 DRF Permission Classes

```python
# common/permissions.py

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == UserType.STAFF

class IsAdminOrSuperuser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser

class IsManagerOfBranch(BasePermission):
    def has_object_permission(self, request, view, obj):
        profile = request.user.staffprofile
        return profile.is_manager and obj.branch in profile.branches.all()

class BelongsToTenant(BasePermission):
    def has_object_permission(self, request, view, obj):
        return True  # django-tenants schema routing handles this
```

### 2.5 JWT Claims on Login

```json
{
  "user_id": "uuid",
  "email": "user@company.com",
  "user_type": "staff",
  "is_manager": true,
  "is_staff": false,
  "is_superuser": false,
  "groups": ["Accountants"],
  "permissions": ["accounting.add_invoice", "accounting.view_invoice"],
  "tenant_slug": "acme-corp",
  "branch_ids": ["uuid1", "uuid2"]
}
```

### 2.6 Django Model Sketch — User (`apps/party`)

```python
# apps/party/models/user.py

class UserType(models.TextChoices):
    STAFF    = "staff",    "Staff"
    CLIENT   = "client",   "Client"
    SUPPLIER = "supplier", "Supplier"
    AGENT    = "agent",    "Agent"

class User(AbstractBaseUser, PermissionsMixin):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True)
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    user_type   = models.CharField(max_length=20, choices=UserType.choices)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login  = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "user_type"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
```

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Staff ERP  │  │Client Portal │  │ Supplier │  │  Agent   │  │
│  │  (Nuxt 3)  │  │  + Store     │  │  Portal  │  │Dashboard │  │
│  └─────┬──────┘  └──────┬───────┘  └────┬─────┘  └────┬─────┘  │
└────────┼────────────────┼───────────────┼──────────────┼────────┘
         └────────────────┴───────────────┴──────────────┘
                                  │ HTTPS / WSS
                          Nginx (API Gateway)
                 /api/v1/* → DRF   |  /ws/* → Django Channels
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
│  Django / DRF    │  │  Celery Workers      │  │  AI Agent       │
│  (Gunicorn/      │  │  (async tasks,       │  │  Runtime        │
│   Daphne ASGI)   │  │   scheduled jobs)    │  │  (LangChain)    │
└────────┬─────────┘  └──────────┬──────────┘  └────────┬────────┘
         └──────────────────────┬┘──────────────────────┘
                                │
         ┌──────────────────────┼───────────────────┐
         ▼                      ▼                   ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL      │  │  Redis           │  │  S3 / Minio      │
│  (Per-schema     │  │  (Cache, Queue,  │  │  (File Storage)  │
│   multi-tenant)  │  │   WebSocket)     │  │                  │
└─────────────────┘  └──────────────────┘  └──────────────────┘
```

### Key Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Auth tokens | `djangorestframework-simplejwt` | Stateless, refresh rotation |
| Async tasks | `Celery` + `Redis` broker | Background jobs, scheduled reports |
| Real-time | `Django Channels` + Redis channel layer | WebSocket for live dashboards, POS |
| Multi-tenancy | `django-tenants` | PostgreSQL schema isolation per Company |
| Money/currency | `django-money` (`MoneyField`, `CurrencyField`) | All monetary fields; GHS default |
| Search | `django-elasticsearch-dsl` or PostgreSQL FTS | Product/client search |
| File storage | `django-storages` + S3/MinIO | Invoices, documents, avatars |
| Email | `django-anymail` (SendGrid/Mailgun) | Transactional emails |
| PDF generation | `WeasyPrint` / `ReportLab` | Invoices, payslips, reports |
| Caching | Redis (`django-redis`) | API response caching |
| Audit log | `django-auditlog` | All model changes tracked |
| i18n | `Django i18n` + Nuxt i18n | Multi-language support |

---

## 4. Multi-Tenancy — Company Model

### 4.1 Strategy

Each `Company` is a **fully isolated PostgreSQL schema** managed by `django-tenants`. All business data lives inside the tenant schema. Only Company/Domain live in the `public` schema.

### 4.2 Supporting Models (public schema)

```python
# apps/party/models/company.py

class Industry(models.Model):
    name             = models.CharField(max_length=255, unique=True)
    description      = models.TextField(blank=True, null=True)
    additional_info  = models.JSONField(blank=True, null=True, default=dict)

class BusinessType(models.Model):
    # Pharmacy, Clinic, Hospital, Retail, Wholesale, Manufacturing, etc.
    name = models.CharField(max_length=50)

class PaymentClass(models.Model):
    # Controls payment method availability and validation per company tier
    name = models.CharField(max_length=50)

class Company(TenantMixin, models.Model):
    """One Company = one PostgreSQL schema = one tenant."""
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name             = models.CharField(max_length=200)
    slug             = models.SlugField(unique=True)           # used as schema_name
    logo             = models.CharField(max_length=200, blank=True, null=True)
    industry         = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    business_type    = models.ForeignKey(BusinessType, on_delete=models.SET_NULL, null=True, blank=True)
    payment          = models.ForeignKey(PaymentClass, on_delete=models.CASCADE)
    tradecountry     = models.ForeignKey('contact.Country', on_delete=models.CASCADE)
    default_currency = CurrencyField(default='GHS')
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    contact          = models.ManyToManyField('company.Contact', blank=True)

    # django-tenants required
    schema_name      = models.CharField(max_length=63, unique=True)
    auto_create_schema = True

class Domain(DomainMixin):
    """Maps subdomain/domain to a Company tenant."""
    pass
```

### 4.3 Post-Save Signal — Initial Data Seeding

When a `Company` is created, the following are auto-seeded via `post_save`:

```python
@receiver(post_save, sender=Company)
def load_initial_account_data(sender, instance, created, **kwargs):
    if created:
        # 1. Seed AddressTypes (Billing, Shipping, Contact)
        for a in ["Billing", "Shipping", "Contact"]:
            AddressType.objects.get_or_create(name=a)

        # 2. Bulk-create complete Charts of Account (5 type groups):
        #    Assets (10100000+), Liabilities (20100000+),
        #    Capital/Equity (30100000+), Revenues/Income (40100000+),
        #    Expenses (50100000+)
        # Accounts include: Cash, Accounts Receivables, Inventory,
        # Accounts Payable, Wages Payable, Taxes Payable, Capital,
        # Revenue/Income, Cost of Goods Sold, Payroll Expenses, etc.

        # 3. Bulk-load Occupations from ISCO-08 Excel file
        roles = pd.read_excel('./testdummy/ISCO-08 EN Structure and definitions.xlsx', ...)
        for row in roles:
            Occupation.objects.update_or_create(name=row["Title EN"], ...)
```

### 4.4 Account Number Auto-Generation (`Charts_of_account.save`)

```
Assets          → acc_number starts at 10100000, increments by 1000
Liabilities     → 20100000 (increments by 2000)
Capital/Equity  → 30100000 (increments by 1000)
Revenues/Income → 40100000 (increments by 1000)
Expenses        → 50100000 (increments by 2000)
```

Sub-accounts under a COA entry are numbered: `coa.acc_number + count_of_existing_sub_accounts + 1`

### 4.5 Tenant-Aware Abstract Base Model

```python
# common/models.py

class TenantAwareModel(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+"
    )
    class Meta:
        abstract = True
```

> **Note:** Existing code uses `createdtimestamp_uid` (adds `created_at`, UUID pk) and `activearchlockedMixin` (adds `is_active`, `is_archived`, `is_locked`) as mixins. These map to `TenantAwareModel` in the plan.

---

## 5. Organisational Hierarchy — Department & Branch

### 5.1 Hierarchy Overview

```
Company (Tenant)
  └── Department  (functional/sales unit, e.g. Retail Unit, Wholesale Unit)
        └── Branch  (physical location, e.g. Head Office, Kumasi Branch)
              └── Shift        (shift schedules per branch/dept)
              └── Room         (physical spaces — meeting rooms, storage)
              └── Shelfing     (shelf/bin locations within room or branch)
```

### 5.2 Department Model

```python
class Department(TenantAwareModel):
    choice = (
        ("Wholesale Unit",     "Wholesale Unit"),
        ("Retail Unit",        "Retail Unit"),
        ("Manufacturing Unit", "Manufacturing Unit"),
    )
    name                    = models.CharField(max_length=50)
    departmenttype          = models.CharField(max_length=50, choices=choice)
    description             = models.TextField(blank=True, null=True)
    staff                   = models.ForeignKey('party.Staff', on_delete=models.PROTECT)
    base_markup             = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_marked_up_from       = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT)

    # Sale configuration
    is_saledepartment       = models.BooleanField(default=False)
    is_onlinesaledepartment = models.BooleanField(default=False)
    defaultonlinedepartment = models.BooleanField(default=False)
    is_creditsale_allowed   = models.BooleanField(default=False)

    contact                 = models.ManyToManyField('company.Contact', blank=True)

    class Meta:
        unique_together = ("departmenttype", "name")

    # save() validates: markup self-reference, online→sale dependencies,
    # credit→sale dependency; ensures only one defaultonlinedepartment
```

### 5.3 Branch Model

```python
class Branch(TenantAwareModel):
    department      = models.ForeignKey(Department, on_delete=models.PROTECT)
    name            = models.CharField(max_length=50)
    staff           = models.ForeignKey('party.Staff', on_delete=models.PROTECT)
    address         = models.ForeignKey('contact.Address', on_delete=models.PROTECT)
    is_warehouse    = models.BooleanField(default=False)
    warehouse_unit  = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        limit_choices_to={"is_warehouse": True}
    )
    # Accounting: M2M ledger accounts (auto-assigned on create via signal)
    branchaccount   = models.ManyToManyField('accounting.Account', blank=True)
    sale_tax        = models.ManyToManyField('accounting.Tax', blank=True)#this is the default sale tax that when the selling rule is taxable for a selling price the taxes here are always applied
    contact         = models.ManyToManyField('company.Contact', blank=True)
    avatar          = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("name", "department")

# On Branch create, signal auto-creates accounts for:
# Inventory, Accounts Receivables, Cash, Accounts Payable,
# Wages Payable, Tips Payable, Capital, Revenue/Income,
# Operational Income, Regular Expense, Depreciation Expense,
# Marketing Expenses, Freight Expense, Cost of Goods Sold
```

### 5.4 Shift Model

```python
class Shift(TenantAwareModel):
    shift_types = models.CharField(max_length=50, choices=(
        ("Morning Shift", "Morning Shift"),
        ("Afternoon Shift", "Afternoon Shift"),
        ("Evening Shift", "Evening Shift"),
        ("Night Shift", "Night Shift"),
    ))
    start_time              = models.TimeField()
    end_time                = models.TimeField()
    department              = models.ForeignKey(Department, on_delete=models.CASCADE)
    staff                   = models.ForeignKey('party.Staff', on_delete=models.PROTECT)
    break_duration_minutes  = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("shift_types", "department")
    # save() validates: start_time < end_time
```

### 5.5 Room Model

```python
class Room(TenantAwareModel):
    name             = models.CharField(max_length=100, unique=True)
    description      = models.TextField(blank=True, null=True)
    cost_rate        = models.CharField(max_length=20, choices=[
        ('fixed','Fixed'), ('hourly','Hourly'), ('daily','Daily'),
        ('none','No Cost'), ('weekly','Weekly'), ('monthly','Monthly'),
    ], default='none')
    assigned_cost    = MoneyField(max_digits=10, decimal_places=2, default_currency='GHS', default=0)
    staff            = models.ForeignKey('party.Staff', on_delete=models.PROTECT)
    location         = models.ForeignKey('contact.Address', on_delete=models.PROTECT)
    floor_number     = models.CharField(max_length=10, null=True, blank=True, default="0")
    capacity         = models.PositiveIntegerField(default=0)
    restricted_access = models.BooleanField(default=False)
    activities       = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    status           = models.CharField(max_length=20,
                                        choices=[('available','Available'), ('unavailable','Unavailable')],
                                        default='available')
    assigned_branch  = models.ManyToManyField(Branch, blank=True)
    assigned_staff   = models.ManyToManyField('party.Staff', blank=True, related_name="roomassignedstaff")
```

### 5.6 Shelfing Model

```python
class Shelfing(TenantAwareModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='branchshelf')
    room   = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    shelf  = models.CharField(max_length=50)

    class Meta:
        unique_together = ("branch", "shelf")
```

### 5.7 User ↔ Branch/Department Assignment

| User Type | Assignment | Model Field |
|-----------|-----------|-------------|
| **Staff** | One or more Branches | `StaffProfile.branches` (M2M → Branch) |
| **Client** | One Department | `ClientProfile.department` (FK → Department) |
| **Supplier** | One Department | `SupplierProfile.department` (FK → Department) |
| **Agent** | Not assigned | — |

---

## 6. Contact & Address System

### 6.1 Geography Models (loaded from CSV on `post_migrate`)

```python
class Country(models.Model):
    name, iso3, iso2, numeric_code, phone_code
    currency, currency_name, lat, lon

class State(models.Model):
    country FK, name, state_code, lat, lon

class City(models.Model):
    name, state FK, lat, lon
```

### 6.2 Type Models

```python
class AddressType(TenantAwareModel): name   # Billing, Shipping, Office, Warehouse
class PhoneType(TenantAwareModel):   name   # Mobile, Work, Landline
class EmailType(TenantAwareModel):   name   # Personal, Company
class webType(TenantAwareModel):     name   # Website, Social Media, Blog
```

### 6.3 Contact Data Models

```python
class Phone(TenantAwareModel):
    phonetype   = models.ForeignKey(PhoneType, null=True, blank=True, on_delete=models.CASCADE)
    phone       = models.CharField(max_length=50)
    is_whatsapp = models.BooleanField(default=False)

class Address(TenantAwareModel):
    addresstype = models.ForeignKey(AddressType, null=True, blank=True, on_delete=models.CASCADE)
    line        = models.CharField(max_length=50)
    city        = models.ForeignKey(City, on_delete=models.CASCADE)
    # postal_code, landmark via custom_fields

class Email(TenantAwareModel):
    email       = models.EmailField()
    emailType   = models.ForeignKey(EmailType, null=True, blank=True, on_delete=models.CASCADE)

class Website(TenantAwareModel):
    website     = models.URLField()
    webtype     = models.ForeignKey(webType, null=True, blank=True, on_delete=models.CASCADE)
```

### 6.4 Contact Wrapper (Generic Link)

```python
class Contact(TenantAwareModel):
    """Wraps any Phone/Email/Website/Address via ContentType."""
    ALLOWED_MODELS = ['Phone', 'Address', 'Website', 'Email']
    content_type     = models.ForeignKey(ContentType, on_delete=models.CASCADE, editable=False)
    contact_id       = models.UUIDField(editable=False)
    contactobject    = GenericForeignKey("content_type", "contact_id")
    is_verified      = models.BooleanField(default=False)
    related_contacts = models.ManyToManyField("self", blank=True)

# Post-save signals auto-create Contact wrappers for every new Phone/Email/Website/Address
```

### 6.5 Document Management

```python
class DocumentType(TenantAwareModel):
    name    = models.CharField(max_length=50, unique=True)

class Document(TenantAwareModel):
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, null=True)
    document_file = models.FileField(upload_to="documents/")
    description   = models.TextField(blank=True, null=True)
    custom_fields = models.JSONField(blank=True, null=True, default=dict)
```

---

## 7. Django Backend — Project Structure

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── party/          # Users, Profiles, Occupations — core identity
│   ├── contact/        # Country, State, City, Phone, Email, Address, Website
│   ├── company/        # Company (Tenant), Industry, BusinessType, Contact wrapper, Document
│   ├── department/     # Department, Branch, Shift, Room, Shelfing
│   ├── hr/             # Employee management, Payroll, Attendance, Leave, Loans
│   ├── accounting/     # COA, Ledger, Tax, Bank, Budget, Expense, Transactions
│   ├── inventory/      # Items, Units, Variants, Pricing, Stock Lots
│   ├── invplan/        # order_document, Carrier, Bill, TransferInventoryDocument
│   ├── workflow/       # Workflow (task templates / checklists)
│   ├── procurement/    # PR, RFQ, PO, GRN, Vendor contracts
│   ├── sales/          # Quotations, Sales Orders, Deliveries, Returns
│   ├── crm/            # Territory, Pipeline, Prospect, Deal, Campaign
│   ├── ecommerce/      # Store, Cart, Order, Reviews, Coupons
│   ├── pos/            # POS sessions, orders, payments, cash movements
│   ├── manufacturing/  # BOM, Work Orders, Routing, MRP
│   ├── logistics/      # Shipments, Routes, Vehicles, Tracking
│   ├── assets/         # Fixed assets, depreciation, maintenance
│   ├── projects/       # Projects, Tasks, Time logs, Milestones
│   ├── reporting/      # Reports, Dashboards, KPI snapshots
│   ├── notifications/  # Notification templates, delivery, preferences
│   ├── integrations/   # Third-party API connections
│   └── agents/         # AI agent definitions, tasks, actions, memory
│
├── common/
│   ├── models.py       # TenantAwareModel abstract base
│   ├── permissions.py
│   ├── pagination.py
│   ├── exceptions.py
│   ├── filters.py
│   └── utils/
│       ├── pdf.py
│       ├── email.py
│       └── currency.py
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── manage.py
├── pytest.ini
└── docker-compose.yml
```

### Core `requirements/base.txt`

```
Django>=5.0
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-tenants>=3.6
django-money>=3.4          # MoneyField, CurrencyField
django-cors-headers>=4.3
django-filter>=23.5
django-auditlog>=2.3
django-redis>=5.4
django-storages[s3]>=1.14
django-anymail[sendgrid]>=10.2
django-channels>=4.0
channels-redis>=4.2
channels[daphne]>=4.0
celery>=5.3
django-celery-beat>=2.5
Pillow>=10.0
WeasyPrint>=60.0
psycopg2-binary>=2.9
redis>=5.0
boto3>=1.34
python-decouple>=3.8
drf-spectacular>=0.27
langchain>=0.2
openai>=1.0
pandas>=2.0             # for data seeding (ISCO-08, countries CSV)
openpyxl>=3.1           # for Excel seeding
```

---

## 8. Django Apps & Models (Module by Module)

---

### 8.1 `apps/party` — Users, Profiles & Occupations

#### Models

```
Occupation              (from ISCO-08 Excel, auto-seeded on Company create via signal)
  - name, definition TextField, task TextField, is_active

User                    (extends AbstractUser — see §2.6)
  - UUID pk (via createdtimestamp_uid mixin)
  - is_admin, is_client, is_vendor, is_verified BooleanField
  - auth_provider (facebook/google/twitter/email/base_auth)
  - company FK → Company (required for non-superuser)
  - On superuser create: auto-loads Ghana geo data + creates Test Company

PasswordReset
  - email, token (unique), is_active

Profile                 (OneToOne → User, pk = user)
  - profile_picture, bioimage CharField (URL)
  - gender, marital_status, employment_status, education_level choices
  - birth_date, date_of_death DateField
  - occupation M2M → Occupation
  - religion FK → religion
  - contact M2M → Contact
  - Custom permissions: can_view_other_profile, can_edit_other_profile
  # Auto-created on User post_save signal

id_type                 (e.g. National ID, Passport, Driver's License)
  - name

national                (user national ID records)
  - user FK, id_type FK, national_id
  - unique_together: (user, id_type, national_id)

religion                (name unique)

ClientGroup
  - company FK, name; unique_together (company, name)

StaffGroup
  - company FK, name, is_an_associate_group_of FK self
  - unique_together (company, name)

Staff                   (pk = user OneToOne, limit: is_staff=True)
  - user OneToOne → User (primary_key=True)
  - staffgroup FK → StaffGroup (nullable)
  - status (active/archived/locked/deleted)
  - departments M2M → Department (auto-set from branches via save())
  - branch M2M → Branch
  - managerial_status BooleanField (is_manager)
  - managed_by FK self (limit: managerial_status=True)
  - staffaccount FK → Account (Payroll Expenses, auto-created via signal)
  - credit_sale_account FK → Account (Accounts Receivables, auto-created via signal)
  - contact M2M → Contact
  - Custom permission: can_switch_branch

Client                  (pk = user OneToOne, limit: is_client=True)
  - user OneToOne → User (primary_key=True)
  - department FK → Department (limit: is_saledepartment=True)
  - is_organization BooleanField
  - client_group FK → ClientGroup (nullable)
  - status (active/archived/locked/deleted)
  - expiration_date DateField
  - client_account FK → Account (Accounts Receivables, auto-created via signal)
  - contact M2M → Contact
  - is_creditsale_allowed BooleanField
  - preferences M2M → preference
  - parents M2M self (family relationships for medical/contact)

Vendor
  - vendorname CharField unique (per company)
  - vendortype (ServiceProvider/Manufacturer/Supplier)
  - company FK → Company
  - user OneToOne → User (optional, limit: is_vendor=True)
  - vendoraccount OneToOne → Account (Accounts Payable, auto-created via signal)
  - contact M2M → Contact
  - status (active/archived/locked/deleted)
  - unique_together: (company, vendorname)

preference              (GenericFK — links client preferences to inventory objects)
  - ALLOWED_MODELS: ['itemvariant', 'VariantAttribute', 'Manufacturer', 'Category']
  - content_type FK, object_id UUID, preference_object GenericForeignKey
  # Auto-created on itemvariant/VariantAttribute/Manufacturer/Category post_save

AgentProfile
  - user FK → User (OneToOne)
  - agent_type (monitor/executor/analyst/assistant)
  - capabilities JSONField, assigned_modules JSONField
  - status (active/paused/error), api_key unique
```

#### API Endpoints

```
POST   /api/v1/auth/register/staff/
POST   /api/v1/auth/register/client/
POST   /api/v1/auth/register/supplier/
POST   /api/v1/auth/login/
POST   /api/v1/auth/refresh/
POST   /api/v1/auth/logout/
GET    /api/v1/auth/me/
PATCH  /api/v1/auth/me/
GET|POST       /api/v1/party/users/
GET|PATCH|DEL  /api/v1/party/users/{id}/
GET|POST       /api/v1/party/departments/
GET|PATCH|DEL  /api/v1/party/departments/{id}/
GET|POST       /api/v1/party/branches/
GET|PATCH|DEL  /api/v1/party/branches/{id}/
GET|POST       /api/v1/party/occupations/
```

---

### 8.2 `apps/hr` — Human Resources & Payroll

#### Models

```
Skill
  - name CharField unique, description TextField
  - skillset M2M self (skill sets / groupings)

Certification
  - name CharField unique, description TextField

Holiday
  - name, date, is_public, is_recurring, description
  - country FK → Country

Vacancy  (activearchlockedMixin)
  - title, department FK, description, requirements
  - posted_date, closing_date, is_filled

Deduction  (activearchlockedMixin)
  - name, description, deduction_type (insurance/social_security/retirement)
  - deduction_rate_type (percent/fixed), deduction DecimalField
  - frequency (monthly/weekly/biweekly/quarterly/annually)
  - currency, min_deduction_amount, max_deduction_amount MoneyField
  - unique_together: (name, currency)
  - clean() validates percent 0-100, fixed >= 0

Benefit  (activearchlockedMixin)
  - name, description, benefit_rate_type (percent/fixed)
  - benefit DecimalField, frequency
  - is_tax_deductable, currency
  - min_benefit_amount, max_benefit_amount MoneyField

MeetingSubject
  - purpose_type ArrayField (Project Discussion, Budget Meeting, etc.)
  - subject CharField unique, description, staff FK

Meeting
  - room FK → Room, subject FK → MeetingSubject
  - date, start_time, end_time (scheduled)
  - actual_date, actual_start_time, actual_end_time
  - assigned_branch M2M, assigned_department M2M
  - attendees M2M User, participants M2M User
  - status (pending/in_progress/completed/canceled/rescheduled)
  - agenda ArrayField, action_items ArrayField
  - minutes, adjourned, follow_up_date
  - rescheduled_from FK self

EmployeeManagementRule
  - name CharField unique, description

EmployeeManagement    (pk = staff OneToOne)
  - staff OneToOne → Staff (primary_key=True)
  - is_employed, works_weekends
  - position FK → Occupation
  - date_hired, date_terminated
  - leave_days_allocated
  - taxes M2M → Tax
  - net_salary, overtime_rate MoneyField
  - salary_rate_period (monthly/biweekly/weekly/daily/hourly)
  - weekend_days_salary_rate, maximum_overtime_hours_per_session
  - preferred_payment_method (bank_transfer/cheque/cash/mobile_money)
  - last_payment_date
  - vacancy FK → Vacancy
  - save() auto-sets date_hired on creation, date_terminated on termination

EmployeeSalaryRule    (OneToOne → EmployeeManagement)
  - salary calculation rules per employee

EmployeeSeverancePackage  (OneToOne → EmployeeManagement)
  - severance package details on termination

Employee_Deduction
  - employee FK → EmployeeManagement, deduction FK → Deduction
  - end_date, recurring BooleanField
  - account FK → Account (auto-assigned "Other Liabilities" account via signal)
  - amount property (computed: percent × net_salary or fixed, capped at max)
  - unique_together: (employee, deduction)

Employee_Benefit
  - employee FK, benefit FK
  - end_date, recurring
  - amount property (computed)
  - unique_together: (employee, benefit)

EmployeeSkill
  - employee FK, skill FK → Skill
  - proficiency_level (beginner/intermediate/advanced/expert)
  - years_of_experience
  - certificates M2M → Certification
  - unique_together: (employee, skill)

EmployeeBankDetails
  - employee FK, bank FK → Bank
  - account_number, account_name, swift_code
  - unique_together: (employee, bank, account_number)

DocumentType          (HR-specific)
  - name CharField unique, description
Document              (HR files)
  - name, file FileField, uploaded_at
EmployeeDocument
  - document_type FK, employee FK, document FK, description

LeaveType  (activearchlockedMixin)
  - name, description, is_paid, rollover_allowed
  - requires_medical_certificate, requires_notice_days, required_hr_approval
  - max_days_allowed, department FK
  - approval_by M2M → Staff

Leave
  - staff FK → EmployeeManagement, leave_type FK → LeaveType
  - start_date, end_date, requested_days, days (computed)
  - reason, status (pending/approved/rejected/cancelled)
  - approved_rejected_by FK → Staff

ScheduledShifts
  - employee FK → EmployeeManagement, shift FK → Shift
  - branch FK, start_date, end_date
  - is_onleave, leave FK → Leave (approved only)
  - holiday FK → Holiday, notes, additional_info JSONField
  - staff FK (created by)
  - clean() validates leave ↔ is_onleave consistency

Attendance
  - employee FK → EmployeeManagement, branch FK
  - scheduled_shift FK → ScheduledShifts (nullable)
  - date, check_in, check_out
  - break_start, break_end
  - status (present/absent/late/excused)

OverTime
  - attendance FK → Attendance
  - requested_hours, planned_activities ArrayField
  - status (pending/approved/in_progress/completed/canceled/rejected)
  - requested_by FK → EmployeeManagement
  - approved_rejected_by FK → Staff
  - start_time, end_time, total_hours (computed)
  - est_overtime_amount MoneyField

LoanType
  - name, description
  - interest_rate_type (fixed/variable)
  - interest_rate_scheme (simple/compound)
  - interest_rate_calculation_period (monthly/quarterly/annually)
  - interest_rate, max_loan_amount, max_repayment_period_months
  - min_monthly_deduction, max_salary_deduction_percentage
  - max_loan_percentage_of_salary

StaffLoans
  - employee FK → EmployeeManagement, loan_type FK → LoanType
  - loan_amount, reason, approval_status (pending/approved/rejected)
  - is_disbursed, est_repayment_period_months
  - start_date, end_date
  - outstanding_balance, deduction MoneyField
  - status (pending/active/completed)
  - staff FK (created by)

Payroll
  - date DateField (normalized to first of month)
  - total_benefits, total_gross_salary, total_taxed_income MoneyField
  - total_deductions, total_net_salary, total_loan_deductions MoneyField
  - staff FK (created by), status (pending/approved/paid/rejected/canceled)
  - Custom permissions: can_process_payroll, can_approve_payroll, etc.

Payrolldetails
  - payroll FK, employee FK → EmployeeManagement
  - status (pending/approved/paid/rejected)
  - Attendance summary: total_days_worked, total_hours_worked,
    total_overtime_hours, total_leave_days, total_absent_days,
    total_late_days, total_weekend_days, total_worked_holiday_days
  - gross_salary, taxed_income, deduction, loandeduction, net_salary MoneyField
  - staffloans M2M → StaffLoans
  - approved_rejected_by FK → Staff
  - unique_together: (employee, payroll)

PerformanceEvaluation
  - employee FK, evaluator FK → Staff
  - skills_assessed M2M → Skill
  - date, score PositiveIntegerField, feedback
```

#### API Endpoints

```
/api/v1/hr/employees/
/api/v1/hr/employees/{id}/attendance/
/api/v1/hr/employees/{id}/payslips/
/api/v1/hr/employees/{id}/leaves/
/api/v1/hr/employees/{id}/skills/
/api/v1/hr/employees/{id}/loans/
/api/v1/hr/leave-types/
/api/v1/hr/leave-requests/
/api/v1/hr/shifts/
/api/v1/hr/scheduled-shifts/
/api/v1/hr/attendance/
/api/v1/hr/overtime/
/api/v1/hr/deductions/
/api/v1/hr/benefits/
/api/v1/hr/vacancies/
/api/v1/hr/payroll/
/api/v1/hr/payroll/{id}/approve/
/api/v1/hr/payroll/{id}/process/
/api/v1/hr/payroll/run/        POST → triggers Celery task
/api/v1/hr/loans/
/api/v1/hr/performance-reviews/
/api/v1/hr/meetings/
```

---

### 8.3 `apps/accounting` — Accounting, Ledger, Tax, Budget

#### Core Design Patterns

1. **`Charts_of_account` (COA)** — the master account template (type + numbering)
2. **`Account`** — a sub-account linked to a specific model instance via ContentType GenericFK
3. **`TransactionDoc`** — a document record linking a business action to its accounting entries
4. **`Transaction`** — individual debit or credit line against an Account
5. **Signal-driven auto-account creation** — key models trigger account creation on save

#### Models

```python
default_currency  = 'GHS'
allowed_currencies = ['GHS', 'USD', 'EUR', 'GBP', 'JPY']

class Charts_of_account  (activearchlockedMixin)
  acc_number          = PositiveIntegerField  (editable=False, auto-assigned by type)
  name                = CharField unique
  description         = TextField
  account_type        = CharField  choices: Assets/Expenses/Liabilities/Revenues_Income/Capital_Equity
  account_balance_type = CharField  choices: Debit/Credit  (auto-set from account_type)
  # save() auto-numbers by type range; sets balance_type from account_type

class Account  (activearchlockedMixin)
  accounttype   = FK → Charts_of_account
  acc_number    = PositiveIntegerField(editable=False, unique)
                  # = coa.acc_number + count_of_existing_sub_accounts + 1
  content_type  = FK → ContentType
  object_id     = UUIDField
  account_object = GenericForeignKey
  unique_together = (object_id, accounttype)
  running_balance  property  # sum(debits) - sum(credits) or inverse per balance_type

class TransactionDoc
  datetimestamp   = DateTimeField(auto_now=True)
  description     = TextField
  content_type    = FK → ContentType
  object_id       = UUIDField
  transaction_object = GenericForeignKey
  ALLOWED_MODELS  = []  # validated in clean()

class Transaction
  notes          = FK → TransactionDoc
  amount         = MoneyField  (original currency)
  account        = FK → Account
  COA            = FK → Charts_of_account  (auto-set from account.accounttype on save)
  transaction_type = CharField  choices: Debit/Credit
  conversion_rate  = DecimalField(default=1)
  # amount_default   = MoneyField  (= amount / conversion_rate)
  # Debit-normal accounts: Assets, Expenses
  # Credit-normal accounts: Liabilities, Revenues/Income, Capital/Equity

class paymentbase  (abstract)
  paymentmethod   = CharField  choices: cash/cheque/banktransfer/mobilemoney
  reference       = CharField
  paymentnotes    = TextField
  Transaction     = FK → TransactionDoc
  amount          = DecimalField
  paymentdate     = DateTimeField

class Bank
  name            = CharField unique
  ismainbranch    = BooleanField
  location        = FK → Contact(Address)
  branchof        = FK self (nullable)
  contact         = M2M → Contact
  notes_account   = FK → Account (Notes Payable, auto-assigned via signal)
  notes_interest_account = FK → Account (Interest Payable, auto-assigned via signal)

class BankAccount  (activearchlockedMixin) #this model handles company bank accounts
  bank            = FK → Bank
  name            = CharField
  account_number  = CharField (digits only)
  routing_number  = CharField (digits only)
  swift_number    = CharField
  account_type    = CharField  choices: savings/checking
  cash_account    = FK → Account (Current Asset, auto-assigned via signal) 
  unique_together = (bank, account_number)

class Tax  (activearchlockedMixin)
  name               = CharField unique
  description        = TextField
  effectivedate      = DateField
  is_tax_recoverable = BooleanField
  tax_type           = CharField  choices: percent/amount
  tax                = DecimalField
  mintaxable_amount  = MoneyField  (0 = always applies)
  maxtaxable_amount  = MoneyField  (0 = no ceiling)
  tax_payable_account  = FK → Account (Taxes Payable, auto-assigned via signal)
  tax_expense_account  = FK → Account (Tax Expense, auto-assigned via signal)
  clean() validates: percent 0-100; min < max if both set

def calculate_tax_amount(amount: Money, tax_id) -> (Money, Tax):
  # Applies min/max rules then computes percent or fixed tax amount

class TransactionRequestType
  name           = CharField unique
  description    = TextField
  transaction_type choices: Expense/Revenue/Transfer/Adjustment/Payroll/
                            Credit Note/Debit Note/Loan/Investment
  

class TransactionRequest
  transaction_type    = FK → TransactionRequestType
  increase_direction  = CharField  choices: debit/credit
  status              = CharField  choices: pending/approved/rejected
  description         = TextField
  amount              = MoneyField
  approving_staff     = FK → Staff
  debit_account       = FK → Account
  credit_account      = FK → Account
  transactiondoc      = FK → TransactionDoc (nullable)
  content_type/object_id/source_object  (GenericFK — source of the request)

class BudgetType
  name                      = CharField
  description               = TextField
  department                = FK → Department
  assigned_approving_manager = M2M → Staff
  unique_together = (name, department)

class BudgetRequest
  budget_type          = FK → BudgetType
  content_type/object/source = GenericFK (what/who requested it)
  amount               = MoneyField
  reason               = TextField
  requested_by         = FK → Staff
  date_requested       = DateField(auto_now_add)
  status               = CharField  choices: pending/needs_revision/cancelled/approved/rejected
  approving_staff      = FK → Staff (nullable)
  date_approved        = DateTimeField (nullable)
  # save() validates approving_staff == budget_type manager when approved

class BudgetAllocation
  budget_request = FK → BudgetRequest
  transaction    = FK → TransactionDoc (nullable)
  amount         = MoneyField
  status         = CharField  choices: allocated/pending/cancelled
  description    = TextField
  allocated_to   = FK → Staff
  allocated_by   = FK → Staff

# class ExpenseType
#   name        = CharField unique
#   description = TextField
#   department  = FK → Department

class ExpenseReport
  # expense_type       = FK → ExpenseType
  budget_allocation  = FK → BudgetAllocation (limit: status=allocated)
  amount             = MoneyField
  returned_amount    = MoneyField
  status             = CharField  choices: draft/completed/locked
  transaction        = FK → TransactionDoc (nullable)
  description        = TextField
  staff              = FK → Staff
  incurred_on        = DateTimeField
```

#### Signal: Auto-Account Creation on Key Model Save

```python
# Triggers: Tax, Bank, BankAccount, Branch, Staff, Tender_Repository,
#           Client, Vendor, Carrier, Employee_Deduction

@receiver(post_save, sender=...)
def create_account_instance(sender, instance, created, **kwargs):
    if created:
        # Bank → Notes Payable + Interest Payable accounts
        # BankAccount → Current Asset account
        # Tax → Taxes Payable + Tax Expense accounts
        # Branch → full set of accounts (see §5.3)
        # Staff → Payroll Expenses + Accounts Receivables accounts
        # Tender_Repository (POS cash drawer) → Cash account
        # Client → Accounts Receivables account
        # Vendor → Accounts Payable account
        # Carrier → Accounts Payable account
        # Employee_Deduction → Other Liabilities account
```

#### API Endpoints

```
/api/v1/accounting/coa/
/api/v1/accounting/accounts/
/api/v1/accounting/transaction-docs/
/api/v1/accounting/transactions/
/api/v1/accounting/banks/
/api/v1/accounting/bank-accounts/
/api/v1/accounting/taxes/
/api/v1/accounting/transaction-requests/
/api/v1/accounting/budget-types/
/api/v1/accounting/budget-requests/
/api/v1/accounting/budget-allocations/
/api/v1/accounting/expense-types/
/api/v1/accounting/expense-reports/
/api/v1/accounting/invoices/
/api/v1/accounting/invoices/{id}/send/
/api/v1/accounting/invoices/{id}/record-payment/
/api/v1/accounting/bills/
/api/v1/accounting/payments/
/api/v1/accounting/currencies/
/api/v1/accounting/exchange-rates/
/api/v1/accounting/reports/profit-loss/
/api/v1/accounting/reports/balance-sheet/
/api/v1/accounting/reports/cash-flow/
/api/v1/accounting/reports/trial-balance/
/api/v1/accounting/reports/ar-aging/
/api/v1/accounting/reports/ap-aging/
```

---

### 8.4 `apps/inventory` — Inventory, Items & Pricing

#### Models

```python
class unit
  name        = CharField unique   # tablet, capsule, bottle, strip
  is_base_unit = BooleanField
  abr         = CharField
  # post_save: if is_base_unit, auto-creates unitofmeasure(1:1 self-conversion)

class unitofmeasure
  converts_to   = FK → unit (base unit)
  converts_from = FK → unit
  conversion_rate = PositiveIntegerField(default=1)
  unique_together = (converts_to, converts_from, conversion_rate)

class Manufacturer
  name           = CharField unique
  description    = CharField
  brand_category = CharField  choices: Premium/Superior/Regular/ValuePackage/LowEnd

class VariantType
  name        = CharField unique (capitalized on save)
  description = CharField
  multiselect = BooleanField  (can product have multiple of this variant?)
  # Examples: Size(Alpha), Size(Number), Color, Flavor, Capacity

class VariantAttribute
  variant_type = FK → VariantType
  name         = CharField
  description  = CharField
  unique_together = (variant_type, name)

class Category
  name        = CharField unique
  description = CharField

class selling_rules
  department             = FK → Department
  name                   = CharField
  # Sale permissions:
  variant_prices_allowed, discount_allowed, service_item_included
  coupon_restricted, price_entry_required, weight_entry_required
  employee_discount_allowed, allow_food_stamp, tax_exempt
  tax_excluded_in_prices, prohibit_repeat_key
  frequent_shopper_eligibility, frequent_shopper_points
  age_restrictions, return_allowed, as_product_discount
  credit_sales_allowed
  unique_together = (name, department)

class Item
  status       = CharField  choices: active/archived/locked/deleted
  category     = FK → Category (nullable)
  name         = CharField
  namestrip    = SlugField (unique, auto-set from name on save)
  brandname    = CharField
  description  = TextField
  manufacturer = FK → Manufacturer (nullable)
  unit         = FK → unit
  pictures     = ArrayField(CharField)
  barcodes     = ArrayField(CharField)  # unique across all items; validated in clean()
  # Variant settings:
  has_variants            = BooleanField
  item_variants_types     = M2M → VariantType
  variants_price_allowed  = BooleanField
  # Product type flags:
  is_manufactured        = BooleanField
  is_raw_material        = BooleanField
  is_internaluseonly     = BooleanField
  is_serviceitem         = BooleanField
  is_expiry_tracked      = BooleanField
  substitutebrands       = M2M self
  service_added          = M2M self
  indexes: [name, namestrip, brandname, barcodes]
  # clean() validates: no barcodes on service items; variants and service_item mutual exclusion

class item_pricing_department  (discount mixin)
  sale_department = FK → Department
  item            = FK → Item
  selling_rules   = FK → selling_rules (nullable)
  selling_price   = MoneyField
  employee_discount = DecimalField
  uom             = FK → unitofmeasure
  # This drives per-department / per-role pricing and discount rules

class itemvariant
  name CharField, item FK → Item (limit: has_variants=True)
  variant M2M → VariantAttribute
  pictures ArrayField
  unique_together: (name, item)

class itemvariantprices
  variant_item FK → itemvariant
  itempricingdepartment FK → item_pricing_department
  selling_price MoneyField
  unique_together: (variant_item, itempricingdepartment)

class ItemLot
  status (active/inactive)
  item FK → Item (limit: not service item)
  lot_number CharField
  manufacturing_date DateField (nullable)
  expiry_date DateField (nullable)
  uom FK → unitofmeasure (pack details)
  unique_together: (item, lot_number)
  is_expired property (expiry_date <= today)
  days_to_expiry, months_to_expiry properties
  can_expire property (= item.is_expiry_tracked)
  # clean() validates: manufacturing_date < expiry_date;
  #          if is_expiry_tracked, both dates required

class StockLotCostValuation
  # AVCO (Average Cost) per lot per department
  itemlot FK → ItemLot
  cost_department FK → Department
  uom FK → unitofmeasure (must be base unit, conversion_rate=1)
  cost_price MoneyField (always in company base currency GHS)
  unique_together: (itemlot, cost_department)
  # Formula: (QtyOnHand × CurrentCost + QtyReceived × ReceiptCost)
  #          ÷ (QtyOnHand + QtyReceived)

class ItemInventoryLot
  item FK → Item (auto-set from itemlot on save)
  itemlot FK → ItemLot
  location FK → Branch
  qty PositiveIntegerField
  shelfnumber FK → Shelfing (nullable)
  inventory_state (OnHand/OnOrder/OnLayaway/Damaged/OnHold) # onhand means stock can be sold or transfered, onorder means the stock is pending delivery, OnLayaway represents stocks currently kept in the branch because of either partial or full payment has been made(sale invoice/ecommerce order),damaged represents products that are either expired or damaged, onhold are products pending complete transfer between branches 
  unique_together: (itemlot, location, inventory_state)
  packsizing property (= itemlot.uom.conversion_rate)
  packname property (= itemlot.uom.converts_from)
  is_itemlot_expired property

class ItemInventoryLotVariant
  lot FK → ItemInventoryLot
  variant FK → itemvariant
  qty PositiveIntegerField
  unique_together: (lot, variant)

class StockLedgerEntry
  branch FK → Branch
  transaction FK → Transaction
  stockvaluation MoneyField (in base currency)
  transaction_type (Debit/Credit)
  inventorytransacttype (Increase/Decrease)
  # GenericFK to source document:
  ALLOWED_MODELS: ReturnDocumentBranch, InventoryTransaction,
                  Bill, TransferInventoryDocument, AdjustmentDocumentBranch
  content_type FK, object_id UUID, transaction_object GenericForeignKey
  unique_together: (branch, transaction)

class itemInvJournalEntry
  # Per-lot-per-branch-per-state detailed inventory movement record
  stockledger FK → StockLedgerEntry
  itemlot FK → ItemLot, location FK → Branch
  inventory_state (OnHand/OnOrder/OnLayaway/Damaged/OnHold)
  uom FK → unitofmeasure, uom_qty PositiveIntegerField
  qty = uom.conversion_rate × uom_qty (auto-computed on save)
  stock_valuation_unit, stock_valuation_line MoneyField
  # Movement counters (base unit):
  beginning_unit_count_base, gross_sales_unit_count_base
  return_unit_count_base, received_unit_count_base
  received_from_vendor_unit_count_base, return_to_vendor_unit_count_base
  transfer_in_unit_count_base, transfer_out_unit_count_base
  increase_adjustment_unit_count_base, decrease_adjustment_unit_count_base
  # GenericFK to source detail:
  ALLOWED_MODELS: ReturnDocumentBranch, InventoryTransaction,
                  BillDetails, TransferDocumentBranch, AdjustmentDocumentBranch, Sale_Return
  unique_together: (itemlot, location, inventory_state, stockledger, uom)
  # post_save signal: updates ItemInventoryLot.qty (increase or decrease)

class SupplierItem          (see §8.5 invplan)
```

#### Signal: Inventory Journal → ItemInventoryLot

```python
@receiver(post_save, sender=itemInvJournalEntry)
def update_itemlotinventory(sender, instance, created, **kwargs):
    if created:
        lot, _ = ItemInventoryLot.objects.get_or_create(
            itemlot=instance.itemlot, location=instance.location,
            inventory_state=instance.inventory_state
        )
        if instance.stockledger.inventorytransacttype == 'Increase':
            lot.qty += instance.qty
        elif instance.stockledger.inventorytransacttype == 'Decrease':
            if lot.qty < instance.qty:
                raise ValidationError("Insufficient stock")
            lot.qty -= instance.qty
        lot.save()
```
```

#### API Endpoints

```
/api/v1/inventory/categories/
/api/v1/inventory/items/
/api/v1/inventory/items/{id}/stock/
/api/v1/inventory/items/{id}/lots/
/api/v1/inventory/items/{id}/moves/
/api/v1/inventory/units/
/api/v1/inventory/uoms/
/api/v1/inventory/manufacturers/
/api/v1/inventory/variant-types/
/api/v1/inventory/stock-lots/
/api/v1/inventory/stock-moves/
/api/v1/inventory/adjustments/
/api/v1/inventory/adjustments/{id}/validate/
/api/v1/inventory/reorder-rules/
/api/v1/inventory/alerts/
/api/v1/inventory/selling-rules/
/api/v1/inventory/item-pricing/
```

---

### 8.5 `apps/invplan` — Inventory Planning, Order Documents & Transfers

#### Design Note

`invplan` is the central hub for all inventory movement documents. Every purchase, transfer, adjustment, return, and sale traces back to an `order_document`. Bills and ASNs live here too. The `Tender_Repository` (POS till) and `WorkStation` are in `apps/sales`.

#### Models

```python
class TermsAndCondition
  code CharField unique (auto-generated from options flags)
  exchangeable, warranty_included, defective_returns_allowed
  delivery_insurance_provided, cod_allowed, cancellation_policy_available
  free_shipping_available, return_window_days PositiveIntegerField

class InventoryCondition
  name CharField unique   # good, broken, damaged, partial shipment, overage

class Carrier
  name, description
  contact M2M → Contact
  carrieraccount FK → Account (Accounts Payable, auto-created via signal)

class order_document
  # Base document for ALL inventory movements
  ordertype = CharField choices:
    order_document / purchase_order / sales_order /
    transfer_order / adjustment_order / return_order
  title = CharField (auto-generated: PO_0001, SO_0001, TR_0001, etc.)
  source_document FK self (nullable — child/split document)
  status (pending/approved/fulfilled/canceled)
  branch FK → Branch, staff FK → Staff
  vendor FK → Vendor (required for purchase_order / return_order)
  client FK → Client (required for sales_order)
  sourcebranch FK → Branch (required for transfer_order)
  order_amount MoneyField
  expected_delivery_date DateTimeField
  notes TextField
  unique_together: (title, branch, ordertype)
  # clean() validates: vendor/client/sourcebranch presence by ordertype
  # save() auto-generates title from type prefix + branch count + date

class order_document_attachment
  order_document FK, file FileField

class order_document_detail
  order FK, item FK, uom FK
  unit_cost_price MoneyField
  qty, qty_base (auto = qty × uom.conversion_rate)
  line_total MoneyField (auto = unit_cost_price × qty)

class TransferInventoryDocument
  transfer_number CharField (auto: TR_YYYYMMDD_HHMMSS_NNNN)
  line_number PositiveIntegerField
  strict BooleanField (strict: in qty must match out qty exactly)
  order_document M2M → order_document
  in_branch FK → Branch (destination), out_branch FK → Branch (source)
  return_inventory_document FK self (for return transfers)
  is_return BooleanField
  status (pending/transit/cancel/accepted/partial_accept/rejected)
  in_staff FK, out_staff FK, delivery_staff FK → Staff
  outcartoncount, incartoncount
  transfer_in_stockvaluation, transfer_out_stockvaluation MoneyField
  unique_together: (transfer_number, in_branch, out_branch)
  Custom permissions: can_reverse_transfer, can_cancel_transfer,
                      can_receive_transfer, can_reject_transfer

class Transfer_Line_Item
  transferdoc FK → TransferInventoryDocument
  item FK, line_number
  transfer_order_details M2M → order_document_detail
  in_amount_valuation, out_amount_valuation MoneyField
  unique_together: (transferdoc, item)

class OutTransfer
  transfer_line_item FK, item_lot FK → ItemLot
  condition FK → InventoryCondition
  uom FK → unitofmeasure, qty, base_qty (auto = qty × uom.conversion_rate)
  base_stock_valuation MoneyField
  unique_together: (transfer_line_item, item_lot, uom)

class OutTransferDetailVariant
  out_transfer FK, variant FK → itemvariant, qty
  unique_together: (out_transfer, variant)

class InTransfer                  (OneToOne → OutTransfer)
  condition FK, uom FK, qty, base_qty (auto)

class InTransferDetailVariant
  in_transfer FK, variant FK → itemvariant, in_qty
  unique_together: (in_transfer, variant)

class AdvancedShipNotice (ASN)
  purchaseorders M2M → order_document (limit: purchase_order)
  vendor FK, termscondition FK
  supplierexpectedshipdate, supplieractualshipdate DateTimeField
  expecteddeliverydate DateField
  serial_form_id CharField
  unique_together: (vendor, serial_form_id)

class packing_slip
  asn FK → AdvancedShipNotice
  purchaseorderdetails M2M → order_document_detail
  supplieritemname, supplieritemcode, supplierlotnumber
  supplierexpirydate, supplierquantity
  supplieruom FK → unitofmeasure
  supplierprice MoneyField, suppliertaxed M2M → Tax
  supplierprice_taxincluded MoneyField

class Bill                 (discount mixin)
  #  Vendor invoice received — tracks payment lifecycle
  billnumber = auto: INV_NNNNN_YYYYMMDD (unique per branch)
  line_number, status (draft/in_review/canceled/approved/void/received)
  order_document M2M → order_document (limit: purchase_order)
  vendor FK, branch FK, staff FK
  paymentterms (on_receipt/net_15/net_30/net_60/net_90/net_90+)
  paymenttermdate DateField
  conversion_rate, billrecieptdate DateTimeField
  tax M2M → Tax
  amount, subtotal_amount, discounted_amount, tax_amount, total_amount MoneyField
  Custom permissions: can_receive_bill, can_void_bill

class FreightBill         (Bill of Lading)
  carrier FK, bill FK
  invoicepicture, storecartoncount, shippedcartoncount
  conversion_rate, cost MoneyField
  unique_together: (carrier, bill)

class Bill_Item
  bill FK, item FK, line_number
  purchase_order_details M2M → order_document_detail
  line_price MoneyField
  unique_together: (bill, item)

class BillDetail           (discount mixin)
  detail FK → Bill_Item, item_lot FK → ItemLot
  uom FK → unitofmeasure, condition FK → InventoryCondition
  unit_cost_price, unit_cost_price_base, line_total MoneyField (auto)
  qty, qty_base (auto = qty × uom.conversion_rate)
  unique_together: (detail, item_lot, uom)
  # save() computes discounted line_total and unit_cost_price_base

class BillDetailVariant
  billdetail FK, variant FK → itemvariant, qty
  unique_together: (billdetail, variant)

class BillPayment
  bill FK, vendor FK, staff FK
  cash_account FK → Account, vendoraccount FK → Account
  payment_amount, notes, date DateTimeField
  transaction FK → TransactionDoc

class ReturnReason
  name, description

class ReturnDocumentsupplier
  status (pending/approved/rejected/returned)
  staff FK, supplier FK → Vendor, bill FK → Bill
  sourcebranch FK, returndate, reason FK → ReturnReason
  source_document FK → order_document (limit: approved return_order)

class ReturnDocumentsupplierDetails
  billdets FK → BillDetail, document FK → ReturnDocumentsupplier
  item FK, lot FK → ItemLot, uom FK, qty, qty_base

class InventoryReconcilationEvent
  name, description

class InventoryReconcilation
  eventreason FK, branch FK
  source_document FK → order_document (limit: approved adjustment_order)
  updatestock BooleanField, transactcount, notes
  unique_together: (eventreason, branch)

class InventoryReconcilationItem
  item FK, document FK → InventoryReconcilation, line_number
  unique_together: (item, document)

class InventoryReconcilationDetails
  invreconitem FK, item_lot FK → ItemLot
  direction (increase/decrease/update)
  uom FK, qty
  unique_together: (invreconitem, item_lot, uom)

class InventoryReconcilationItemVariant
  recondetail FK, variant FK → itemvariant, qty

class SupplierItem
  supplier FK → Vendor, item FK → Item
  name (supplier's item name)
  moq PositiveIntegerField (minimum order qty in packs)
  uom FK → unitofmeasure
```

#### Signal Integration

`Carrier` is in `create_account_instance` signal — auto-assigns an Accounts Payable `Account` on creation.

---

### 8.6 `apps/procurement` — Purchasing & Vendor Management

#### Models

```
PurchaseRequisition (PR)
  - reference, requested_by FK User, department FK
  - status (draft/submitted/approved/rejected/converted)
  - lines M2M → PRLine, urgency (low/normal/high/critical)

PRLine
  - requisition FK, item FK, qty
  - preferred_supplier FK → Vendor
  - estimated_unit_cost, notes

RequestForQuotation (RFQ)
  - reference, pr FK (nullable), created_by FK
  - status (draft/sent/received/expired)
  - suppliers M2M → Vendor, deadline

RFQResponse
  - rfq FK, supplier FK → Vendor
  - status (pending/submitted/accepted/rejected)
  - lines M2M → RFQResponseLine, valid_until, notes

RFQResponseLine
  - response FK, item FK, qty, unit_price, currency
  - lead_time_days, terms

PurchaseOrder (PO)
  - po_number, supplier FK → Vendor, created_by FK
  - rfq_response FK (nullable), pr FK (nullable)
  - status (draft/confirmed/partially_received/received/cancelled)
  - currency, exchange_rate, payment_terms
  - expected_delivery, shipping_address FK
  - lines M2M → POLine, notes
  - subtotal, tax, total

POLine
  - po FK, item FK, description
  - ordered_qty, received_qty, billed_qty
  - unit_price, tax rate, line_total
  - discount, discount_type

GoodsReceiptNote (GRN)
  - reference, po FK, received_by FK, received_at
  - warehouse FK → Branch, status (draft/confirmed)
  - lines M2M → GRNLine

GRNLine
  - grn FK, po_line FK, item FK
  - lot FK (created or linked), quantity, location FK → Shelfing
  - condition (good/damaged/rejected), notes

SupplierEvaluation
  - supplier FK → Vendor, period, evaluator FK
  - on_time_delivery_score, quality_score, price_score, comm_score
  - overall_score, comments

VendorContract
  - supplier FK, title, start_date, end_date
  - contract_value, currency, terms_document
  - status (draft/active/expired/terminated)
  - auto_renew, renewal_notice_days
```

#### API Endpoints

```
/api/v1/procurement/requisitions/
/api/v1/procurement/requisitions/{id}/approve/
/api/v1/procurement/rfqs/
/api/v1/procurement/rfqs/{id}/send/
/api/v1/procurement/rfq-responses/
/api/v1/procurement/purchase-orders/
/api/v1/procurement/purchase-orders/{id}/confirm/
/api/v1/procurement/purchase-orders/{id}/receive/
/api/v1/procurement/grns/
/api/v1/procurement/grns/{id}/confirm/
/api/v1/procurement/supplier-evaluations/
/api/v1/procurement/vendor-contracts/
```

---

### 8.7 `apps/sales` — Sales Orders & Quotations

#### Models

```
PriceList
  - name, currency, is_default
  - lines M2M → PriceListLine, valid_from, valid_to

PriceListLine
  - pricelist FK, item FK (or category FK)
  - price, min_qty, discount_pct

Discount / PromotionRule
  - name, discount_type (pct/fixed/buy_x_get_y)
  - value, min_order_amount, max_uses
  - applicable_to (all/category/item/client_tier)
  - start_date, end_date, is_active

Quotation
  - quote_number, client FK → ClientProfile (or prospect FK)
  - issued_by FK User, issue_date, expiry_date
  - status (draft/sent/viewed/accepted/rejected/expired)
  - currency, pricelist FK
  - lines M2M → QuotationLine
  - notes, terms, discount, tax, subtotal, total

QuotationLine
  - quotation FK, item FK, description
  - qty, unit_price, discount, tax_rate, line_total

SalesOrder (SO)  ← extends order_document
  - so_number, client FK, quotation FK (nullable)
  - issued_by FK, status (draft/confirmed/picking/shipped/delivered/invoiced/cancelled)
  - currency, pricelist FK, payment_terms
  - shipping_address FK, billing_address FK
  - lines M2M → SOLine, priority
  - discount, tax, subtotal, total, commission_rate
  - branch FK

SOLine
  - so FK, item FK, qty, delivered_qty, invoiced_qty
  - unit_price, discount, tax_rate, line_total
  - warehouse FK → Branch, lot FK (nullable)

Delivery
  - reference, so FK, warehouse FK → Branch
  - status (draft/ready/done/cancelled)
  - scheduled_date, done_date, carrier FK → Carrier
  - tracking_number, lines M2M → DeliveryLine

DeliveryLine
  - delivery FK, so_line FK, item FK
  - lot FK, qty_to_deliver, qty_done, location FK → Shelfing

Return / ReturnLine (RMA)
  - so FK or invoice FK, reason, return_date
  - lines M2M → ReturnLine
  - refund_method (credit_note/replacement/cash)
  - status (pending/approved/received/processed)

Commission
  - sales_rep FK, so FK, rate, amount, status (pending/paid)

Tender_Repository   (see §8.5 — POS cash till tied to branch)
```

---

### 8.8 `apps/crm` — CRM Module

#### Design Note: Prospect-Pipeline-Deal Pattern

The CRM uses a **Prospect → ProspectPipelineStage → Deal** flow (not a simple Lead → Opportunity model). Pipelines are fully configurable with stages, transitions, and probability tracking.

#### Models

```python
class Territory
  name        = CharField unique
  description = TextField
  staff       = FK → Staff
  city        = M2M → City

class SaleMember  (pk = staff OneToOne)
  staff              = OneToOne → Staff (primary_key=True)
  team_lead          = BooleanField
  assigned_territories = M2M → Territory
  creator            = FK → Staff
  assistants         = M2M self
  status             = CharField  choices: active/inactive

class SaleTeam
  name                 = CharField unique
  description          = TextField
  team_leads           = M2M → SaleMember (limit: team_lead=True)
  members              = M2M → SaleMember
  staff                = FK → Staff (created by)
  assigned_territories = M2M → Territory

class Pipeline
  name        = CharField unique
  description = TextField
  staff       = FK → Staff
  # Has many Stages and PipelineTransitions

class stage
  pipeline    = FK → Pipeline
  sequence    = IntegerField
  name        = CharField unique
  description = TextField
  probability = IntegerField (%)
  is_won      = BooleanField
  is_lost     = BooleanField
  tasks       = M2M → Workflow

class PipelineTransition
  pipeline   = FK → Pipeline
  from_stage = FK → stage
  to_stage   = FK → stage
  unique_together = (pipeline, from_stage, to_stage)

class Campaign
  name                = CharField unique
  description         = TextField
  status              = CharField  choices: planned/in_progress/postponed/completed/cancelled
  approval_status     = CharField  choices: pending/needs_revision/approved/rejected
  approval_staff      = FK → Staff (nullable)
  start_date          = DateTimeField
  end_date            = DateTimeField
  budget              = MoneyField
  projected_revenue   = MoneyField
  projected_reach     = IntegerField
  progress            = IntegerField (%)
  staff               = FK → Staff (created by)
  targetted_territories = M2M → Territory
  assigned_tasks      = M2M → Workflow
  assigned_sales_team = M2M → SaleTeam
  assigned_sales_rep  = M2M → SaleMember

class Prospect_Company
  name               = CharField unique
  description        = TextField
  industry           = FK → Industry (nullable)
  contact            = M2M → Contact
  additional_info    = JSONField
  size               = CharField  choices: x_small/small/medium/large
  assigned_sales_team = M2M → SaleTeam
  assigned_sales_rep = M2M → SaleMember
  staff              = FK → Staff
  territory          = M2M → Territory
  campaign           = M2M → Campaign

class Prospect
  # Pre-customer individual or contact showing interest
  staff              = FK → Staff
  company            = FK → Prospect_Company (nullable)
  username           = CharField unique
  first_name, last_name = CharField
  role               = FK → Occupation (nullable)
  territory          = FK → Territory (nullable)
  assigned_sales_team = M2M → SaleTeam
  assigned_sales_rep = M2M → Staff
  contact            = M2M → Contact
  client_user        = FK → ClientProfile (nullable — after conversion)
  status             = CharField  choices: new/contacted/qualified/unqualified/converted/lost
  additional_info    = JSONField
  campaign           = FK → Campaign (nullable)
  assigned_departments = M2M → Department
  tasks              = M2M → Workflow

class ProspectPipelineStage
  prospect   = FK → Prospect
  pipeline   = FK → Pipeline
  stage      = FK → stage
  status     = CharField  choices: in_progress/completed/on_hold/cancelled/failed
  start_date = DateTimeField(auto_now_add)
  end_date   = DateTimeField (nullable)
  sales_rep  = FK → SaleMember (nullable)

class Deal
  prospect      = FK → Prospect
  deal_valuation = MoneyField
  status        = CharField  choices: prospecting/negotiation/won/lost
  close_date    = DateField (nullable)
  metadata      = JSONField
  order         = FK → order_document  # becomes SO when deal won
  tasks         = M2M → Workflow
  # When won: order transitions to full SalesOrder
```

#### API Endpoints

```
/api/v1/crm/territories/
/api/v1/crm/sale-members/
/api/v1/crm/sale-teams/
/api/v1/crm/pipelines/
/api/v1/crm/stages/
/api/v1/crm/campaigns/
/api/v1/crm/prospect-companies/
/api/v1/crm/prospects/
/api/v1/crm/prospects/{id}/pipeline-stages/
/api/v1/crm/deals/
/api/v1/crm/deals/{id}/won/
/api/v1/crm/deals/{id}/lost/
```

---

### 8.9 `apps/workflow` — Workflow Automation Engine

#### Purpose

A node-based, configurable workflow engine. Used throughout the system for CRM stage tasks, campaign tasks, deal tasks, approvals, scheduled jobs, and AI agent orchestration. Every `Workflow` is a directed graph of `node` objects connected by `WorkflowTransition` edges.

#### Models

```python
class configuration
  # Defines a typed input/output parameter for a node
  name, description
  required BooleanField
  field_type (text/number/date/boolean/select/object/array/file)
  parser CharField (e.g. text_parser, email_parser, decimal_parser, date_parser)
  options JSONField (required for 'select' type)
  sub_fields M2M self (required for 'object' type)
  array_item_type FK self (required for 'array' type; must be 'object')
  max_size IntegerField
  # clean() validates parser ↔ field_type compatibility; options/sub_fields/array_item_type presence
  # parser_function(value) → typed Python value

class node                    (activearchlockedMixin)
  name, description, version
  x_position, y_position IntegerField (canvas position for UI)
  node_type choices:
    trigger/time_based, trigger/event_based, trigger/manual
    action/parse_data, action/send_email, action/http_request
    action/database_query, action/ai_model_call, action/notify_user
    action/condition_check
    human_activity           # requires: input_conf, output_conf, assigned_to
    add
  assigned_to M2M → Staff
  input_conf M2M → configuration
  output_conf M2M → configuration
  staff FK → Staff (created by)

class Workflow                (activearchlockedMixin)
  name CharField unique, description
  start_date, end_date DateTimeField
  staff FK → Staff (created by)
  trigger_node FK → node (limit: node_type starts with 'trigger')
  nodes M2M → node

class WorkflowTransition
  workflow FK, from_node FK → node, to_node FK → node
  from_node_default, to_node_default JSONField (pass-through data)
  action_on_error (retry/fail/skip/restart/call_node)
  action_on_timeout (retry/fail/skip/restart/call_node)
  action_on_timeout_timeout IntegerField (minutes)
  timeout_action_count, error_retry_count, error_retry_interval (seconds)
  error_threshold IntegerField
  onError_node FK → node (nullable — called if action_on_error='call_node')
  error_node_default JSONField
  review_required BooleanField, review_deadline DateTimeField
  staff FK → Staff
  # save() validates: from_node/to_node belong to workflow.nodes;
  #          onError_node set when action_on_error='call_node'

class Assigned_Task
  workflowtransition FK → WorkflowTransition
  exc_node FK → node (limit: human_activity)
  assigned_to FK → Staff
  priority (low/medium/high)
  deadline_response IntegerField (hours)
  reviewers M2M → Staff

class WorkflowExecution
  workflow FK, transition FK → WorkflowTransition
  execution_node FK → node
  # GenericFK — source object that triggered execution
  content_type FK, object_id UUID, source_object GenericForeignKey
  status (pending/in_progress/cancelled/completed/failed)
  input_data, output_data JSONField
  error_count, errored_at, started_at, completed_at DateTimeField
  assigned_to FK → Staff (nullable)

class Review
  workflow_execution FK, reviewer FK → Staff
  rating IntegerField, remarks TextField
  reviewed_at DateTimeField
  review_status (pending/completed/rejected)
  review_score IntegerField
```

#### Workflow Usage Across Modules

| Module | Usage |
|--------|-------|
| CRM stages | `stage.tasks M2M → Workflow` |
| CRM campaigns | `Campaign.assigned_tasks M2M → Workflow` |
| CRM deals | `Deal.tasks M2M → Workflow` |
| CRM prospects | `Prospect.tasks M2M → Workflow` |
| AI agents | `AgentTask` triggers WorkflowExecution |
| Approvals | `human_activity` nodes for budget/leave/PO/payroll approval |
| Reporting | `trigger/time_based` nodes drive scheduled reports |

---

### 8.10 `apps/ecommerce` — E-Commerce Storefront

#### Models

```
Store
  - name, domain, logo, banner
  - currency, default_language, is_active
  - seo_title, seo_description

ProductListing
  - item FK → Item, store FK
  - is_published, published_at
  - ecommerce_price, description_html (rich text)
  - gallery M2M, featured_until
  - meta_title, meta_description, slug

Cart
  - session_id (guests), client FK (nullable)
  - currency, expires_at

CartItem
  - cart FK, item FK, qty, unit_price, discount, line_total, notes

Wishlist
  - client FK, name, is_public
  - items M2M → Item

Order  (maps to SalesOrder)
  - order_number, client FK, cart FK, so FK
  - billing_address FK, shipping_address FK
  - status (pending/payment_pending/paid/processing/shipped/delivered/cancelled/refunded)
  - payment_method, payment_ref, coupon_code FK (nullable)
  - subtotal, discount, shipping_cost, tax, total
  - ip_address (security logging)

OrderTracking
  - order FK, status, message, location, timestamp, notified

Review
  - item FK, client FK
  - rating (1-5), title, body
  - is_verified_purchase, is_approved, helpful_count

Coupon / VoucherCode
  - code, discount_type (pct/fixed/free_shipping)
  - value, min_order, max_uses, used_count
  - valid_from, valid_to, is_active
  - applicable_items M2M, applicable_categories M2M

ShippingZone
  - name, countries JSONField

ShippingMethod
  - name, zone FK, carrier
  - price_type (fixed/weight_based/value_based/free_over)
  - rate, max_weight, min_order_for_free, estimated_days

PaymentGateway
  - name, provider (stripe/paystack/flutterwave)
  - is_active, config JSONField (encrypted), currencies JSONField
```

---

### 8.11 `apps/sales` — Point of Sale & Sales

> **Note:** The POS and retail sales logic lives in the `sales/` app — **not** a separate `pos/` app.  
> The `Tender_Repository` model (POS till/safe) is also defined here.

#### Models

```python
class Tender_Repository
  # createdtimestamp_uid mixin (UUID pk, created_at)
  name          = CharField
  branch        = FK → Branch
  repo_type     = CharField choices: Safe / MobileMoney / Till / LockBox
  lockoutamount        = MoneyField  # max balance before lockout triggers
  lockoutwarningamount = MoneyField  # warning threshold
  account       = FK → Account (Cash account; auto-created by create_account_instance)
  unique_together: (name, branch, repo_type)

class WorkStation
  # POS workstation — sits at a single branch till
  branch        = FK → Branch (auto-set from tender_till.branch on save)
  name          = CharField unique  # auto-generated: BranchName_TillName_NNN
  tender_till   = FK → Tender_Repository (limit: repo_type=Till)
  intraining    = BooleanField  # training mode (timer active)
  key           = CharField unique (nullable)  # hardware key
  allowedstaff  = M2M → Staff  # must belong to branch
  unique_together: (branch, tender_till)
  # Custom permissions: can_retrain_workstation, can_endtraining_workstation
  #                     can_change_workstation_staff

class SaleReturnReason
  name, description

class Sale_Return
  # createdtimestamp_uid + activearchlockedMixin
  sale_number   = CharField auto  # INV_YYYYMMDD_NNNNN
  branch        = FK → Branch
  workstation   = FK → WorkStation
  sale_return_reason = FK → SaleReturnReason
  status        = CharField choices: pending / approved / void
  client        = FK → Client (nullable)
  tax           = M2M → Tax
  # Financial
  subtotal, discount_amount, tax_amount, total_amount  = MoneyField ×4
  amount_tendered, change_given, amount_due            = MoneyField ×3
  refund_amount, restocking_fee                        = MoneyField ×2
  voided_by     = FK → Staff (nullable)
  unique_together: (sale_number, branch)
  # Custom permissions: can_reverse_sale_return, can_void_sale_return

class Sale_Return_Item
  sale_return FK → Sale_Return
  item FK → Item
  itemlot FK → ItemLot (nullable)

class Sale_Return_Detail
  # discount mixin
  sale_return  FK → Sale_Return
  item_detail  FK → Sale_Return_Item
  selling_price_department FK → item_pricing_department
  uom          (auto-set from pricing department)
  uom_qty      PositiveIntegerField
  line_total   MoneyField (auto = selling_price × uom_qty)

# ── Payment Methods ──────────────────────────────────────────────────────────
class cashpayment
  sale_return FK, tender_repository FK (limit: Till only)
  amount MoneyField

class momopayment
  sale_return FK, tender_repository FK (limit: MobileMoney)
  network = CharField choices: MTN / VODAFONE / AIRTELTIGO
  amount MoneyField, reference CharField

class creditpayment
  sale_return FK, client FK → Client
  amount MoneyField

# ── Client Orders ─────────────────────────────────────────────────────────────
class ClientOrder
  # createdtimestamp_uid + activearchlockedMixin
  client FK → Client
  branch FK → Branch
  order_document FK → order_document (type: sales_order; nullable)
  status CharField choices: draft / confirmed / processing / shipped / delivered / cancelled
  notes TextField

class RecurrentCustOrder   # stub — to be implemented
  pass

class ClientOrderLineitem
  client_order FK → ClientOrder
  item FK → Item
  itemlot FK → ItemLot (nullable)
  uom FK → unitofmeasure
  qty PositiveIntegerField
  selling_price MoneyField
```

#### Signal Notes
- `Tender_Repository.post_save` → `create_account_instance` auto-creates a **Cash** account in `accounts/`
- `WorkStation.name` is auto-generated as `{Branch.name}_{TenderRepo.name}_{NNN}` on save

---

### 8.12 `apps/manufacturing` — Manufacturing & MRP

> **Implementation Status:** Partially implemented.  
> `BillOfMaterials`, `BillOfMaterialsItems`, and `Machinery` have real fields.  
> All other classes are **empty `pass` stubs** and require full implementation.

#### Implemented Models

```python
class BillOfMaterials
  # createdtimestamp_uid + activearchlockedMixin
  items        = FK → Item (finished good)
  quantity     = PositiveIntegerField
  uom          = FK → unitofmeasure
  department   = FK → Department
  is_default   = BooleanField
  service_charge = MoneyField
  # save() ensures only one default BOM per item per department

class BillOfMaterialsItems
  bom          = FK → BillOfMaterials
  items        = FK → Item (component / raw material)
  quantity     = PositiveIntegerField
  uom          = FK → unitofmeasure
  service_charge = MoneyField

class Machinery
  name         = CharField
  department   = FK → Department
  status       = CharField choices: operational / under_maintenance / out_of_order
```

#### Stub Classes (not yet implemented)

The following classes exist in `manufacturing/models.py` as empty `pass` bodies:

```
ProductionLine, ManufacturingBatch, MaintenanceSchedule, QualityCheck,
Shift, Labor, RawMaterialRequirement, FinishedProduct, ProductionSchedule,
InventoryAdjustment, ScrapRecord, ManufacturingCost
```

#### Planned Fields (future implementation)

```
ProductionLine    — item FK, BOM FK, WorkOrder reference, machinery M2M, shift FK
ManufacturingBatch — production_line FK, planned_start/end, actual_start/end, qty,
                     status (draft/in_progress/done/cancelled)
QualityCheck      — batch FK, inspector FK Staff, passed BooleanField, notes
MaintenanceSchedule — machinery FK, scheduled_date, done BooleanField, technician FK
Labor             — batch FK, staff FK, hours_worked, cost MoneyField
RawMaterialRequirement — batch FK, item FK, qty_required, qty_consumed, lot FK
FinishedProduct   — batch FK, item FK, lot FK (new lot), qty_produced
ProductionSchedule — date, batch FK, sequence, notes
InventoryAdjustment — branch FK, item FK, delta_qty, reason, done_by FK Staff
ScrapRecord       — batch FK, item FK, qty_scrapped, reason
ManufacturingCost — batch FK, labour/materials/overhead MoneyField
```

---

### 8.13 `apps/logistics` — Shipping & Delivery

#### Models

```
Carrier  (see §8.5 invplan — shared model referenced here)

ShipmentRoute
  - name, origin_address FK, destination_address FK
  - carrier FK, estimated_days, cost

Shipment
  - reference, carrier FK, tracking_number
  - origin FK → Address, destination FK → Address
  - status (pending/dispatched/in_transit/out_for_delivery/delivered/failed/returned)
  - shipped_at, estimated_delivery, actual_delivery
  - weight, dimensions JSONField, declared_value
  - related_so FK (nullable), related_po FK (nullable)

ShipmentEvent  (tracking timeline)
  - shipment FK, status, location, message, timestamp, source

DeliveryRoute  (owned fleet)
  - date, driver FK User, vehicle FK
  - stops M2M → RouteStop, status (planned/in_progress/done)

RouteStop
  - route FK, shipment FK, sort_order
  - address FK, eta, actual_arrival, status, notes

Vehicle
  - plate_number, type, capacity, driver FK (default)
  - last_service_date, next_service_date, is_active

CustomsClearance
  - shipment FK, hs_codes JSONField
  - status, duty_amount, cleared_at, broker
```

---

### 8.14 `apps/assets` — Fixed Asset Management

#### Models

```
AssetCategory
  - name
  - depreciation_method (straight_line/declining_balance/units_of_production)
  - useful_life_years, salvage_value_pct
  - asset_account FK → Charts_of_account
  - depreciation_account FK → Charts_of_account
  - accumulated_account FK → Charts_of_account

FixedAsset
  - asset_number, name, category FK
  - purchase_date, in_service_date, purchase_price, currency
  - supplier FK → Vendor, purchase_order FK (nullable)
  - location FK → Department, assigned_to FK User
  - status (active/idle/under_maintenance/disposed/sold)
  - serial_number, barcode, image
  - current_book_value (auto-computed)

AssetDepreciation
  - asset FK, period_date, depreciation_amount, accumulated_depreciation
  - book_value_after, journal_entry FK → TransactionDoc (auto-posted)

AssetMaintenance
  - asset FK, maintenance_type (preventive/corrective)
  - scheduled_date, done_date, cost, technician
  - description, vendor, next_due_date

AssetDisposal
  - asset FK, disposal_date, disposal_method (sold/scrapped/donated)
  - sale_price (if sold), proceeds_account FK → Charts_of_account
  - gain_or_loss (computed), journal_entry FK → TransactionDoc
```

---

### 8.15 `apps/projects` — Project Management

#### Models

```
Project
  - name, code, client FK (nullable)
  - manager FK User, team M2M User
  - status (planning/active/on_hold/completed/cancelled)
  - start_date, end_date, budget, currency
  - progress_pct (auto-computed), priority
  - branch FK

ProjectMilestone
  - project FK, name, due_date, is_completed, completed_at

Task
  - project FK, parent FK self (subtasks)
  - title, description, assigned_to FK User, created_by FK
  - status (todo/in_progress/in_review/done/blocked)
  - priority (low/medium/high/critical)
  - due_date, estimated_hours
  - tags M2M, attachments M2M

TimeLog
  - task FK, employee FK User
  - start_time, end_time, duration_minutes
  - description, billable, hourly_rate

ProjectExpense
  - project FK, category, amount, currency, date
  - description, receipt, approved_by FK

Issue / Bug
  - project FK, title, description, reporter FK
  - assigned_to FK, status, priority, type (bug/feature/improvement)
  - linked_task FK (nullable)
```

---

### 8.16 `apps/reporting` — Reports, Dashboards & KPIs

#### Models

```python
SavedReport
  - name, module, query_params JSONField
  - created_by FK, is_shared, schedule (cron)
  - last_run_at, output_format (pdf/excel/csv)

ScheduledReport
  - saved_report FK, recipients M2M User
  - cron_expression, next_run_at
  - last_status (success/failed)

KPISnapshot  (persisted)
  - kpi_key, value, dimension JSONField, snapshot_date
  # keys: revenue, cogs, gross_profit, inventory_value,
  #       outstanding_ar, overdue_ar, low_stock_count,
  #       expiry_within_30d, new_orders_today, pos_sales_today, etc.

Dashboard
  - name, owner FK User, is_default, layout JSONField
  - widgets M2M → DashboardWidget

DashboardWidget
  - dashboard FK, widget_type (chart/table/metric/map)
  - title, config JSONField (data source, filters, chart type)
  - position JSONField (grid x/y/w/h)
```

#### Report Catalogue

```
Finance:       P&L, Balance Sheet, Cash Flow, Trial Balance, AR/AP Aging,
               Budget vs Actual
Inventory:     Stock Valuation, Stock Movement, Expiry Report, Reorder Report,
               Dead Stock, FIFO/AVCO Costing
Procurement:   PO Status, Supplier Performance, Spend Analysis
Sales:         Sales by Item/Category/Rep/Period, Pipeline Kanban,
               Customer Lifetime Value, Returns Analysis, Commission Summary
HR:            Headcount, Attendance Summary, Leave Summary, Payroll Summary,
               Overtime, Loan Repayment
POS:           Daily/Weekly/Monthly Sales, Session Summary, Top Items
Manufacturing: Production vs Plan, Scrap Rate, Work Centre Utilisation
Projects:      Project Status, Time & Cost, Resource Utilisation
Supplier:      Product Sales Velocity, Stockout History, Expiry Forecast,
               Revenue Share by Product
```

---

### 8.17 `apps/notifications` — Notification Centre

#### Models

```
NotificationTemplate
  - key, subject_template, body_template (Jinja2)
  - channels (email/sms/in_app/push)

Notification
  - recipient FK User, notification_type
  - title, body, data JSONField
  - channel, is_read, read_at
  - created_at, sent_at, delivery_status

NotificationPreference
  - user FK, notification_type, channels_enabled JSONField
  - quiet_hours_start, quiet_hours_end
```

#### Key Notification Events

```
- New order placed (staff alert)
- Order status changed (client)
- Low stock / stockout (staff + supplier)
- Expiry warning / overdue (staff + supplier)
- Leave request status change (employee)
- Invoice overdue (finance team)
- Bill payment due (finance team)
- New GRN received (procurement)
- PO awaiting approval
- New prospect/deal (assigned sales rep)
- Budget request status change (requester)
- Payroll processed (employee)
- Agent action completed / requires approval (staff)
- New product review submitted
- Overtime request status (employee)
```

---

### 8.18 `apps/agents` — AI Agent Core

#### Models

```
AgentDefinition
  - name, slug, description, agent_type
  - capabilities JSONField, model_config JSONField
  - system_prompt, tools_manifest JSONField
  - is_active

AgentTask
  - agent FK, triggered_by FK User (nullable)
  - task_type, input_data JSONField
  - status (pending/running/completed/failed/requires_approval)
  - output_data JSONField, error_message
  - started_at, completed_at
  - requires_human_approval, approved_by FK, approved_at

AgentAction (step-level log)
  - task FK, step_number, action_type
  - tool_called, tool_input JSONField, tool_output JSONField
  - timestamp, duration_ms

AgentMemory
  - agent FK, key, value JSONField, updated_at

AgentAlert
  - agent FK, alert_type, severity (low/medium/high/critical)
  - title, body, data JSONField, resolved_at
  - target_user FK (or broadcast to role)
```

#### Built-in Agents

```
1. InventoryMonitorAgent    (every 15 min via Celery beat)
   - Watches stock levels, fires stockout/low-stock alerts
   - Drafts PRs for items below reorder point
   - Notifies suppliers of stockout events

2. ExpiryWatcherAgent       (daily)
   - Scans lots for expiry within 7 / 14 / 30 days
   - Reports to suppliers with affected items
   - Suggests markdown pricing or clearance transfer

3. FinanceAnalystAgent      (daily)
   - Reconciles AR/AP, flags overdue invoices
   - Weekly P&L summary for management
   - Alerts on cash flow anomalies

4. SalesAssistantAgent
   - Auto-qualifies new prospects from web form
   - Suggests upsell/cross-sell from order history
   - Drafts quotations from chat input

5. ProcurementAgent
   - Auto-sends RFQs when PRs are approved
   - Compares RFQ responses and recommends vendor
   - Drafts POs pending staff approval

6. ReportBotAgent
   - Accepts natural language report requests
   - Generates and emails scheduled reports

7. FraudDetectionAgent
   - Monitors POS and e-commerce transactions
   - Flags unusual patterns (large discounts, after-hours, bulk returns)
```

---

## 9. REST API Design Standards

### Response Envelope

```json
{
  "success": true,
  "data": { "...": "..." },
  "meta": { "page": 1, "page_size": 20, "count": 150, "total_pages": 8 },
  "errors": null
}
```

### Error Envelope

```json
{
  "success": false,
  "data": null,
  "errors": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "fields": { "email": ["Enter a valid email address."] }
  }
}
```

### Conventions

- `GET /resources/` — list (paginated, filterable, searchable)
- `POST /resources/` — create
- `GET /resources/{id}/` — detail
- `PATCH /resources/{id}/` — partial update
- `DELETE /resources/{id}/` — soft delete (`is_active=False`)
- `POST /resources/{id}/{action}/` — state transitions (e.g., `/confirm/`, `/approve/`, `/won/`)
- Versioning: `/api/v1/` prefix
- Pagination: `?page=1&page_size=20`
- Filtering: `django-filter` — `?status=active&category=5`
- Ordering: `?ordering=-created_at`
- Search: `?search=keyword`
- Date range: `?date_after=2025-01-01&date_before=2025-12-31`
- OpenAPI: `/api/v1/schema/` (drf-spectacular), UI at `/api/v1/docs/`
- WebSocket: `ws://host/ws/notifications/`, `ws://host/ws/pos/{session_id}/`, `ws://host/ws/agents/`

---

## 10. NuxtJS Frontend — Project Structure

```
frontend/
├── app.vue
├── nuxt.config.ts
├── tailwind.config.ts
├── tsconfig.json
│
├── assets/
│   ├── css/
│   │   ├── main.css
│   │   └── themes/
│   └── icons/
│
├── components/
│   ├── ui/
│   │   ├── DataTable/
│   │   │   ├── DataTable.vue
│   │   │   ├── DataTableColumn.vue
│   │   │   └── DataTableFilters.vue
│   │   ├── Charts/
│   │   │   ├── BarChart.vue
│   │   │   ├── LineChart.vue
│   │   │   ├── PieChart.vue
│   │   │   ├── AreaChart.vue
│   │   │   └── KpiCard.vue
│   │   ├── Form/
│   │   │   ├── FormField.vue
│   │   │   ├── SearchSelect.vue
│   │   │   ├── DateRangePicker.vue
│   │   │   ├── FileUpload.vue
│   │   │   ├── RichTextEditor.vue
│   │   │   ├── CurrencyInput.vue
│   │   │   └── BarcodeScanner.vue
│   │   ├── Layout/
│   │   │   ├── PageHeader.vue
│   │   │   ├── SectionCard.vue
│   │   │   ├── SplitPane.vue
│   │   │   └── StatCard.vue
│   │   ├── Feedback/
│   │   │   ├── EmptyState.vue
│   │   │   ├── LoadingOverlay.vue
│   │   │   └── ConfirmDialog.vue
│   │   ├── Navigation/
│   │   │   ├── Breadcrumbs.vue
│   │   │   ├── TabNavigation.vue
│   │   │   └── CommandPalette.vue
│   │   ├── Timeline.vue
│   │   ├── StatusBadge.vue
│   │   ├── AvatarGroup.vue
│   │   └── PrintFrame.vue
│   │
│   ├── modules/
│   │   ├── inventory/
│   │   ├── accounting/
│   │   ├── hr/
│   │   ├── sales/
│   │   ├── pos/
│   │   ├── procurement/
│   │   ├── ecommerce/
│   │   ├── crm/
│   │   ├── agents/
│   │   └── ...
│   │
│   └── shared/
│       ├── NotificationBell.vue
│       ├── UserAvatarMenu.vue
│       ├── BranchSelector.vue
│       ├── TenantSwitcher.vue
│       ├── ThemeToggle.vue
│       └── LanguageSwitcher.vue
│
├── composables/
│   ├── useApi.ts
│   ├── useAuth.ts
│   ├── useCurrentUser.ts
│   ├── usePagination.ts
│   ├── useFilters.ts
│   ├── useWebSocket.ts
│   ├── useNotifications.ts
│   ├── usePermissions.ts
│   ├── useBranch.ts
│   ├── usePrint.ts
│   ├── useCurrency.ts
│   ├── useToast.ts
│   ├── modules/
│   │   ├── useInventory.ts
│   │   ├── useAccounting.ts
│   │   ├── useSales.ts
│   │   ├── useCRM.ts
│   │   └── ...
│   └── useAgent.ts
│
├── layouts/
│   ├── default.vue       # Staff ERP (sidebar + topbar)
│   ├── client.vue
│   ├── supplier.vue
│   ├── agent.vue
│   ├── storefront.vue
│   ├── pos.vue           # Full-screen touch-optimized
│   ├── auth.vue
│   └── print.vue
│
├── middleware/
│   ├── auth.ts
│   ├── requireStaff.ts
│   ├── requireClient.ts
│   ├── requireSupplier.ts
│   ├── requirePermission.ts
│   ├── requireManager.ts
│   └── portal-router.ts
│
├── pages/
│   ├── auth/
│   │   ├── login.vue
│   │   ├── register.vue
│   │   ├── forgot-password.vue
│   │   └── reset-password.vue
│   │
│   ├── (staff)/
│   │   ├── index.vue
│   │   ├── dashboard/
│   │   ├── hr/
│   │   ├── accounting/
│   │   ├── inventory/
│   │   ├── procurement/
│   │   ├── sales/
│   │   ├── crm/
│   │   ├── manufacturing/
│   │   ├── logistics/
│   │   ├── assets/
│   │   ├── projects/
│   │   ├── reports/
│   │   ├── agents/
│   │   ├── settings/
│   │   │   ├── groups/
│   │   │   ├── branches/
│   │   │   └── departments/
│   │   └── notifications/
│   │
│   ├── (client)/
│   │   ├── index.vue
│   │   ├── orders/
│   │   ├── invoices/
│   │   ├── quotes/
│   │   ├── wishlist.vue
│   │   ├── addresses.vue
│   │   └── profile.vue
│   │
│   ├── (supplier)/
│   │   ├── index.vue
│   │   ├── products/
│   │   ├── stock-alerts/
│   │   ├── expiry-reports/
│   │   ├── purchase-orders/
│   │   ├── invoices/
│   │   └── performance/
│   │
│   ├── store/
│   │   ├── index.vue
│   │   ├── products/
│   │   │   ├── index.vue
│   │   │   └── [slug].vue
│   │   ├── categories/[slug].vue
│   │   ├── cart.vue
│   │   ├── checkout/
│   │   │   ├── index.vue
│   │   │   ├── shipping.vue
│   │   │   ├── payment.vue
│   │   │   └── confirmation.vue
│   │   └── orders/[id]/track.vue
│   │
│   └── pos/
│       ├── index.vue
│       ├── [session_id].vue
│       └── close.vue
│
├── plugins/
│   ├── api.ts
│   ├── auth.client.ts
│   ├── websocket.client.ts
│   ├── charts.client.ts
│   └── i18n.ts
│
├── stores/
│   ├── auth.ts
│   ├── ui.ts
│   ├── notifications.ts
│   ├── branch.ts
│   ├── tenant.ts
│   ├── cart.ts
│   ├── pos.ts
│   ├── inventory.ts
│   ├── accounting.ts
│   └── agents.ts
│
├── types/
│   ├── api.ts
│   ├── user.ts
│   ├── inventory.ts
│   ├── accounting.ts
│   ├── sales.ts
│   └── ...
│
└── utils/
    ├── format.ts
    ├── validation.ts
    ├── permissions.ts
    └── constants.ts
```

### Key Frontend Dependencies

```json
{
  "dependencies": {
    "nuxt": "^3.12",
    "@nuxt/ui": "^3.0",
    "reka-ui": "^2.0",
    "@pinia/nuxt": "^0.7",
    "pinia": "^2.2",
    "pinia-plugin-persistedstate": "^3.2",
    "@vueuse/nuxt": "^11.0",
    "@vueuse/core": "^11.0",
    "ofetch": "^1.3",
    "zod": "^3.23",
    "@tiptap/vue-3": "^2.4",
    "@tiptap/starter-kit": "^2.4",
    "echarts": "^5.5",
    "vue-echarts": "^7.0",
    "dayjs": "^1.11",
    "@nuxtjs/i18n": "^8.5",
    "vue-draggable-plus": "^0.5",
    "html2canvas": "^1.4",
    "jspdf": "^2.5",
    "zxing-wasm": "^1.2"
  }
}
```

---

## 11. Frontend Pages & Routes (Module by Module)

### 11.1 Staff ERP Portal — Page Map

```
/(staff)/
  dashboard/
    index.vue                   → Executive KPI dashboard
    accounting.vue              → Accounting overview

  hr/
    index.vue                   → HR overview (headcount, attendance today)
    employees/
      index.vue
      new.vue
      [id]/
        index.vue               → Profile (overview, attendance, leave, payroll, docs, loans)
        edit.vue
    departments/index.vue
    attendance/
      index.vue
      calendar.vue
    leaves/
      requests.vue
      allocations.vue
      calendar.vue
    payroll/
      index.vue
      [period_id]/
        index.vue               → Period detail — run, review, approve, export
        payslip/[employee_id].vue
    overtime/index.vue
    loans/index.vue
    deductions/index.vue
    benefits/index.vue
    vacancies/index.vue
    meetings/index.vue
    performance/index.vue

  accounting/
    index.vue
    coa/index.vue
    journal-entries/
      index.vue
      new.vue
      [id].vue
    transactions/index.vue
    invoices/
      index.vue
      new.vue
      [id].vue
    bills/
      index.vue
      [id].vue
    payments/index.vue
    banks/index.vue
    taxes/index.vue
    budgets/
      index.vue
      requests/index.vue
      allocations/index.vue
    expenses/index.vue
    transaction-requests/index.vue
    reports/
      profit-loss.vue
      balance-sheet.vue
      cash-flow.vue
      trial-balance.vue
      ar-aging.vue
      ap-aging.vue

  inventory/
    index.vue
    items/
      index.vue
      new.vue
      [id]/
        index.vue
        edit.vue
        variants.vue
        pricing.vue
    categories/index.vue
    units/index.vue
    manufacturers/index.vue
    stock-lots/
      index.vue
      expiry.vue
    stock-moves/index.vue
    adjustments/
      index.vue
      new.vue
      [id].vue
    reorder-rules/index.vue
    alerts/index.vue
    warehouses/
      index.vue
      [id]/index.vue            → Branch warehouse view with shelfing

  procurement/
    index.vue
    requisitions/
      index.vue
      new.vue
      [id].vue
    rfqs/
      index.vue
      [id].vue
    purchase-orders/
      index.vue
      new.vue
      [id].vue
    grns/
      index.vue
      [id].vue
    supplier-evaluations/index.vue
    vendor-contracts/index.vue

  sales/
    index.vue
    quotations/
      index.vue
      new.vue
      [id].vue
    orders/
      index.vue
      new.vue
      [id].vue
    deliveries/index.vue
    returns/index.vue
    pricelists/index.vue
    commissions/index.vue

  crm/
    index.vue                   → Pipeline kanban / prospect board
    territories/index.vue
    sale-teams/index.vue
    prospects/
      index.vue
      new.vue
      [id]/
        index.vue
        pipeline.vue
    companies/index.vue
    deals/
      index.vue
      [id].vue
    campaigns/
      index.vue
      new.vue
      [id].vue

  manufacturing/
    index.vue
    boms/
      index.vue
      [id].vue
    work-orders/
      index.vue
      new.vue
      [id].vue
    workcenters/index.vue
    mrp/index.vue

  logistics/
    shipments/index.vue
    delivery-routes/index.vue
    carriers/index.vue
    vehicles/index.vue

  assets/
    index.vue
    [id].vue
    depreciation.vue
    maintenance/index.vue
    disposals/index.vue

  projects/
    index.vue
    new.vue
    [id]/
      index.vue
      timeline.vue
      budget.vue
      team.vue
      timelogs.vue

  reports/
    index.vue
    [report_key].vue
    scheduled.vue
    dashboards/
      index.vue
      [id].vue

  agents/
    index.vue
    [id]/
      index.vue
      configure.vue
    tasks/index.vue
    alerts/index.vue

  settings/
    company.vue
    users/index.vue
    roles.vue
    notifications.vue
    integrations.vue
    pos-config.vue
    email-templates.vue
    audit-log.vue
```

### 11.2 Client Portal

```
/(client)/
  index.vue
  orders/
    index.vue
    [id]/
      index.vue
      track.vue
  invoices/
    index.vue
    [id].vue
  quotes/
    index.vue
    [id].vue
  wishlist.vue
  addresses.vue
  profile.vue
  notifications.vue
```

### 11.3 Supplier Portal

```
/(supplier)/
  index.vue
  products/
    index.vue
    [id].vue
  stock-alerts/index.vue
  expiry-reports/
    index.vue
    [item_id].vue
  purchase-orders/
    index.vue
    [id].vue
  invoices/index.vue
  performance/
    index.vue
    trends.vue
  profile.vue
  notifications.vue
```

### 11.4 E-Commerce Storefront

```
/store/
  index.vue
  products/
    index.vue
    [slug].vue
  categories/[slug].vue
  search.vue
  cart.vue
  checkout/
    index.vue
    payment.vue
    confirmation.vue
  orders/[id]/track.vue
```

---

## 12. UI Component Architecture

### 12.1 Design Tokens

```ts
// nuxt.config.ts
ui: {
  primary: 'indigo',
  gray: 'zinc',
  // POS module: override to dark theme
}
```

### 12.2 Key Custom Components

| Component | Reka Primitive(s) | Purpose |
|-----------|------------------|---------|
| `DataTable` | `Table`, `Separator` | Sortable, filterable, paginated table |
| `SearchSelect` | `Combobox` | Async remote search dropdown |
| `DateRangePicker` | `Popover` + `RangeCalendar` | Date range selection |
| `CommandPalette` | `Dialog` + `Combobox` | Global search (Cmd+K) |
| `ConfirmDialog` | `AlertDialog` | Destructive action confirmation |
| `Timeline` | custom + `Separator` | Activity/audit timeline |
| `Kanban` | `Draggable` + `ScrollArea` | CRM pipeline, project board |
| `GanttChart` | custom SVG + `ScrollArea` | Project milestones |
| `POSNumpad` | `Dialog` + custom grid | POS quantity/price input |
| `BarcodeScanner` | `Dialog` + ZXing WASM | Camera barcode scanning |
| `WidgetGrid` | `Draggable` (vue-draggable-plus) | Dashboard builder |
| `PrintPreview` | `Dialog` + iframe | Print-ready documents |
| `FileUpload` | Reka headless + dropzone | Attachment with preview |
| `RichTextEditor` | Tiptap + custom toolbar | Long-form text |
| `SignaturePad` | Canvas API + `Dialog` | Document signing |

### 12.3 Layout Structure (Staff Portal)

```vue
<!-- layouts/default.vue -->
<template>
  <div class="flex h-screen overflow-hidden bg-gray-950">
    <AppSidebar :collapsed="ui.sidebarCollapsed" />
    <div class="flex flex-col flex-1 overflow-hidden">
      <AppTopbar />
      <main class="flex-1 overflow-y-auto p-6">
        <Breadcrumbs />
        <slot />
      </main>
    </div>
    <NotificationDrawer />
    <CommandPalette />
  </div>
</template>
```

### 12.4 POS Layout

```vue
<!-- layouts/pos.vue -->
<template>
  <div class="flex h-screen bg-gray-900 text-white select-none">
    <POSProductPanel class="flex-1" />
    <POSOrderPanel class="w-96" />
  </div>
</template>
```

---

## 13. State Management (Pinia)

### `stores/auth.ts`

```ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isStaff     = computed(() => user.value?.user_type === 'staff')
  const isClient    = computed(() => user.value?.user_type === 'client')
  const isSupplier  = computed(() => user.value?.user_type === 'supplier')
  const isManager   = computed(() => user.value?.is_manager === true)
  const hasGroup    = (group: string) => user.value?.groups?.includes(group) ?? false
  const hasPerm     = (perm: string)  => user.value?.permissions?.includes(perm) ?? false

  async function login(credentials) { ... }
  async function logout() { ... }
  async function refreshAccessToken() { ... }
  async function fetchCurrentUser() { ... }

  return { user, accessToken, isAuthenticated, isStaff, isManager, hasGroup, hasPerm, login, logout }
})
```

### `stores/pos.ts`

```ts
export const usePOSStore = defineStore('pos', () => {
  const currentSession     = ref<POSSession | null>(null)
  const currentOrder       = ref<POSOrder | null>(null)
  const heldOrders         = ref<HeldOrder[]>([])
  const products           = ref<Item[]>([])
  const isOffline          = ref(false)
  const pendingSync        = ref<POSOrder[]>([])  // offline queue → IndexedDB

  async function addToOrder(item, qty) { ... }
  async function processPayment(paymentLines) { ... }
  async function syncOfflineOrders() { ... }
})
```

### `stores/cart.ts`

```ts
export const useCartStore = defineStore('cart', {
  persist: true,
  state: () => ({ items: [], couponCode: null, sessionId: uuid() }),
})
```

---

## 14. AI Agent Architecture

### 14.1 Agent Framework

- **LangChain** (Python) — orchestration layer
- **OpenAI GPT-4o** (configurable: Anthropic, Gemini, Ollama)
- Each agent is a `LangChain ReAct Agent` with a defined tool set
- Tools are Python functions calling ERP internal APIs / Django ORM directly
- Agents run as **Celery tasks** — triggered by schedule, events (signals), or staff/API requests
- All actions logged to `AgentAction` and `AgentTask`
- Human-in-the-loop: tasks with `requires_human_approval=True` pause for staff review

### 14.2 Sample Agent Tools (InventoryMonitorAgent)

```python
@tool
def get_low_stock_items(threshold: int = 10) -> list:
    """Returns items with qty_on_hand <= threshold"""
    ...

@tool
def create_purchase_requisition(item_id: str, qty: int, reason: str) -> dict:
    """Drafts a PR; sets requires_human_approval=True"""
    ...

@tool
def notify_supplier(supplier_id: str, item_id: str, message: str) -> dict:
    """Sends a notification to the supplier portal"""
    ...
```

### 14.3 Agent → Staff Communication Flow

```
Agent runs task
  → determines action needed
  → if low-confidence / destructive: sets requires_human_approval=True
  → sends Notification to assigned staff (in-app + email)
  → staff opens /agents/tasks page
  → reviews agent reasoning + proposed action
  → approves / rejects / modifies
  → agent executes (or discards)
```

---

## 15. Development Phases / Roadmap

### Phase 0 — Foundation (Weeks 1–2)

- [ ] Django project scaffold with all apps listed in §7
- [ ] PostgreSQL + Redis + Celery setup (`docker-compose.yml`)
- [ ] `django-tenants` multi-tenancy wired up
- [ ] Custom User model + JWT auth (all 4 user types)
- [ ] `django-money` installed; `default_currency='GHS'`
- [ ] Nuxt project scaffold + Nuxt UI + Reka UI + Pinia
- [ ] Auth pages (login/register/password reset)
- [ ] Portal router middleware (`user_type` → correct portal)
- [ ] Base layout components (sidebar, topbar, breadcrumbs)
- [ ] API response/error envelope standard

### Phase 1 — Core Data & Accounting Foundation (Weeks 3–5)

- [ ] Contact app: Country/State/City from CSV; Phone/Email/Address/Website models
- [ ] Company app: Company, Industry, BusinessType, Contact wrapper
- [ ] Department app: Department, Branch, Shift, Room, Shelfing
- [ ] Accounting app: Charts_of_account with auto-numbering
- [ ] Account model with ContentType GenericFK
- [ ] Company post_save signal — full COA seeding
- [ ] Branch post_save signal — account auto-creation
- [ ] Tax, Bank, BankAccount models + their signals
- [ ] Nuxt: Company settings, Branch/Department management UI

### Phase 2 — Inventory & Procurement (Weeks 6–9)

- [ ] Item, Unit, UOM, VariantType, VariantAttribute, Category models
- [ ] StockLot, StockMove, ReorderRule, InventoryAdjustment
- [ ] item_pricing_department + selling_rules
- [ ] invplan: order_document, Tender_Repository, Carrier + signals
- [ ] Procurement: PR → RFQ → PO → GRN workflow
- [ ] Nuxt: Product catalog, warehouse/stock views, procurement pages
- [ ] Reorder rule engine (Celery beat)
- [ ] InventoryMonitorAgent + ExpiryWatcherAgent (basic)
- [ ] Supplier portal: product/stock views

### Phase 3 — Finance & HR (Weeks 10–14)

- [ ] Full accounting: TransactionDoc, Transaction, paymentbase
- [ ] Budget: BudgetType, BudgetRequest, BudgetAllocation
- [ ] ExpenseType, ExpenseReport, TransactionRequest
- [ ] HR: EmployeeManagement, Skill, Certification, Vacancy
- [ ] Deduction, Benefit, Employee_Deduction, Employee_Benefit signals
- [ ] LoanType, StaffLoans
- [ ] Payroll, Payrolldetails engines (Celery task)
- [ ] Leave, ScheduledShifts, Attendance, OverTime
- [ ] Meeting, MeetingSubject scheduling
- [ ] PerformanceEvaluation
- [ ] Auto-journal posting from payroll, GRNs, invoices, payments
- [ ] Nuxt: Finance pages (COA, transactions, invoices, bills, budgets)
- [ ] Nuxt: HR pages (employees, attendance, leave, payroll, meetings)
- [ ] PDF: invoices, payslips
- [ ] FinanceAnalystAgent (AR/AP monitoring)

### Phase 4 — Sales, CRM & E-Commerce (Weeks 15–20)

- [ ] Sales: Quotation, SalesOrder, Delivery, Return, Commission
- [ ] CRM: Territory, SaleMember, SaleTeam, Pipeline, stage, PipelineTransition
- [ ] CRM: Campaign, Prospect_Company, Prospect, ProspectPipelineStage, Deal
- [ ] Workflow app: Workflow, WorkflowStep models
- [ ] E-Commerce: Store, ProductListing, Cart, Order, Review, Coupon
- [ ] Payment gateway integration (Stripe + Paystack)
- [ ] Nuxt: Sales pipeline pages + CRM kanban/prospect board
- [ ] Nuxt: E-Commerce storefront (full public-facing store)
- [ ] Nuxt: Client portal
- [ ] SalesAssistantAgent + ProcurementAgent

### Phase 5 — POS (Weeks 21–23)

- [ ] POSConfiguration, POSSession, POSOrder, POSOrderLine, POSPaymentLine
- [ ] POSCashMovement, HeldOrder
- [ ] Nuxt: Full-screen POS interface (touch-optimized)
- [ ] Offline mode (IndexedDB + sync queue)
- [ ] Barcode scanner integration
- [ ] Receipt printing (thermal + PDF)
- [ ] Z-report generation
- [ ] FraudDetectionAgent

### Phase 6 — Manufacturing, Logistics, Assets & Projects (Weeks 24–29)

- [ ] Manufacturing: BOM, WorkOrder, WorkCenter, Routing, MRP
- [ ] Logistics: Shipment, DeliveryRoute, Vehicle, CustomsClearance
- [ ] Assets: FixedAsset, AssetDepreciation (Celery), AssetMaintenance, AssetDisposal
- [ ] Projects: Project, Task, TimeLog, Milestone, ProjectExpense
- [ ] Nuxt: Manufacturing pages (BOM editor, WO board)
- [ ] Nuxt: Shipment tracking, asset registry, project kanban + Gantt

### Phase 7 — Reporting, Dashboards & AI Agents (Weeks 30–34)

- [ ] Report engine (all catalogue types from §8.16)
- [ ] KPI snapshot Celery task
- [ ] Nuxt: Dynamic report viewer
- [ ] Nuxt: Dashboard builder (drag-drop widgets)
- [ ] All AI agents fully built and tested
- [ ] Nuxt: Full agent dashboard + approval workflow
- [ ] Supplier portal: performance analytics + report subscriptions
- [ ] ReportBotAgent

### Phase 8 — Notifications, Integrations & Polish (Weeks 35–38)

- [ ] Django Channels: WebSocket notifications
- [ ] Nuxt: Real-time notification bell + drawer
- [ ] Email/SMS events (all from §8.17)
- [ ] Third-party integrations (shipping APIs, accounting exports)
- [ ] i18n (English + French at minimum)
- [ ] Comprehensive audit log viewer
- [ ] Performance tuning + Redis caching layer
- [ ] OpenAPI documentation + user manual

---

## 16. Infrastructure & DevOps

### Local Development (`docker-compose.yml`)

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: erp_db
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: erp_pass

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes: [./backend:/app]
    ports: ["8000:8000"]
    depends_on: [db, redis]
    env_file: .env

  celery:
    build: ./backend
    command: celery -A config worker -l info
    depends_on: [backend, redis]

  celery-beat:
    build: ./backend
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on: [celery]

  frontend:
    build: ./frontend
    command: npm run dev
    volumes: [./frontend:/app]
    ports: ["3000:3000"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
```

### Production Stack

```
Nginx (reverse proxy + SSL termination)
  ├── /api/* + /ws/*  → Daphne (ASGI — HTTP + WebSocket)
  ├── /admin/*        → Daphne
  └── /*              → Nuxt SSR (Node.js / CDN static)

Managed Services:
  - Database: Supabase PostgreSQL / AWS RDS
  - Redis:    Upstash / ElastiCache
  - Storage:  AWS S3 / Cloudflare R2
  - Email:    SendGrid / Mailgun
  - Monitoring: Sentry (errors) + Prometheus/Grafana (metrics)
```

---

## 17. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Auth | JWT with 15 min access / 7 day refresh rotation; HTTPS enforced |
| RBAC | `user_type` + Django `Group` memberships checked on every endpoint |
| Object-level | Branch/department queryset filtering; `is_manager` flag for approvals |
| SQL Injection | Django ORM only; raw queries forbidden (or fully parameterized) |
| XSS | DRF JSON responses; Nuxt auto-escapes bindings; CSP headers |
| CSRF | DRF exempt for JWT; Django CSRF for session-based admin |
| Sensitive data | Bank details, API keys encrypted (`django-encrypted-model-fields`) |
| Rate limiting | `django-ratelimit` on auth; Nginx rate limits on API |
| Audit trail | `django-auditlog` on all models; immutable `AgentAction` logs |
| File uploads | Type validation, size limits, virus scan hook (ClamAV optional) |
| Supplier portal | Suppliers see only data scoped to their own products/POs |
| Client portal | Clients see only their own orders/invoices |
| Agent permissions | Agent JWT has explicit module permission list; whitelisted endpoints only |
| POS offline sync | Orders signed with session token; replayed with idempotency keys |
| Pharmacy | Ghana Card verification for pharmaceutical purchases (online shop) |
| Money fields | All monetary values use `django-money` `MoneyField`; no raw floats |
| Signal safety | All `create_account_instance` exceptions re-raise as `ValidationError` |

---

*This document is the living specification, unified from `ref_models.md` (working code) and the original plan. All model names, field types, and patterns reflect the actual implementation. New sections and features should be documented here before or alongside their implementation.*
