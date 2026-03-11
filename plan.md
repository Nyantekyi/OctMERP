# Enterprise Resource Planning (ERP) System — Master Plan

> **Tech Stack:** Django 5.x + Django REST Framework (Backend) · Nuxt 3 + Nuxt UI / Reka UI (Frontend)
> **Date:** March 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Types & Permission Model](#2-user-types--permission-model)
3. [System Architecture](#3-system-architecture)
4. [Multi-Tenancy — Company Model](#4-multi-tenancy--company-model)
5. [Organisational Hierarchy — Department & Branch](#5-organisational-hierarchy--department--branch)
6. [Generic Contact Model](#6-generic-contact-model)
7. [Django Backend — Project Structure](#7-django-backend--project-structure)
8. [Django Apps & Models (Module by Module)](#8-django-apps--models-module-by-module)
   - 8.1 `apps/party` — Users & Profiles
   - 8.2 `apps/hr` — Human Resources & Payroll
   - 8.3 `apps/accounting` — Accounting, AR, AP, Budgeting
   - 8.4 `apps/inventory` — Inventory & Warehouse
   - 8.5 `apps/procurement` — Purchasing & Vendor Management
   - 8.6 `apps/sales` — Sales Orders & Quotations
   - 8.7 `apps/crm` — CRM Module
   - 8.8 `apps/ecommerce` — E-Commerce Storefront
   - 8.9 `apps/pos` — Point of Sale
   - 8.10 `apps/manufacturing` — Manufacturing & MRP
   - 8.11 `apps/logistics` — Shipping & Delivery
   - 8.12 `apps/assets` — Fixed Asset Management
   - 8.13 `apps/projects` — Project Management
   - 8.14 `apps/reporting` — Reports, Dashboards & KPIs
   - 8.15 `apps/notifications` — Notification Centre
   - 8.16 `apps/agents` — AI Agent Core
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

Permissions and groups are managed entirely through Django's built-in `Permission` and `Group` models. Admins and superusers create, modify, and assign groups via the Django admin or the Group Management API in the ERP frontend (`/(staff)/settings/groups`).

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

Admin/superusers manage all groups and permissions via Django admin or
the ERP frontend Group Management UI (/(staff)/settings/groups).
```

### 2.3 Manager Elevation (`is_manager`)

- `StaffProfile.is_manager = True` grants manager-level privilege **within the user's assigned branches**
- Managers can approve leave requests, purchase requisitions, payroll periods, and quotations for their branches
- This is a simple `BooleanField` on the profile — it **augments** (not replaces) the user's Group memberships
- Example: a user can be in `Inventory Officers` group **and** have `is_manager=True`, giving them full inventory access plus approval authority

### 2.4 DRF Permission Classes

```python
# common/permissions.py

class IsStaff(BasePermission):
    """User must be of type 'staff'."""
    def has_permission(self, request, view):
        return request.user.user_type == UserType.STAFF

class IsAdminOrSuperuser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or request.user.is_superuser


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser
class IsManagerOfBranch(BasePermission):
    """Staff user with is_manager=True, scoped to the resource's branch."""
    def has_object_permission(self, request, view, obj):
        profile = request.user.staffprofile
        return (
            profile.is_manager and
            obj.branch in profile.branches.all()
        )

class BelongsToTenant(BasePermission):
    """django-tenants schema routing guarantees isolation; explicit safety check."""
    def has_object_permission(self, request, view, obj):
        return True  # schema routing handles this
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

Frontend middleware uses `user_type` to route to the correct portal/layout after login.

### 2.6 Django Model Sketch — User (`apps/party`)

```python
# apps/party/models/user.py

class UserType(models.TextChoices):
    STAFF    = "staff",    "Staff"
    CLIENT   = "client",   "Client"
    SUPPLIER = "supplier", "Supplier"
    AGENT    = "agent",    "Agent"

class User(AbstractBaseUser, PermissionsMixin):
    """
    PermissionsMixin provides:
      - groups           (M2M → django.contrib.auth.Group)
      - user_permissions (M2M → django.contrib.auth.Permission)
      - has_perm(), has_module_perms()

    All group & permission management is done through Django's standard
    admin or the ERP Group Management API. Only admins (is_staff=True)
    and superusers can modify groups.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True)
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    user_type   = models.CharField(max_length=20, choices=UserType.choices)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)   # grants Django admin access
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login  = models.DateTimeField(null=True, blank=True)

    # Avatar / contact info live on the per-type profile model.
    # Profile sub-models created automatically via post_save signal:
    #   staffprofile / clientprofile / supplierprofile / agentprofile

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "user_type"]

    objects = UserManager()

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
         │                │               │              │
         └────────────────┴───────────────┴──────────────┘
                                  │ HTTPS / WSS
┌─────────────────────────────────▼───────────────────────────────┐
│                       API GATEWAY (Nginx)                        │
│            /api/v1/*  →  Django REST Framework                   │
│            /ws/*      →  Django Channels (WebSocket)             │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
│  Django / DRF    │  │  Celery Workers      │  │  AI Agent       │
│  (Gunicorn)      │  │  (async tasks,       │  │  Runtime        │
│                  │  │   scheduled jobs)    │  │  (LangChain /   │
│  - Auth          │  │                      │  │   custom agent) │
│  - CRUD APIs     │  │  - Email/SMS         │  │                 │
│  - Business      │  │  - Report gen        │  └────────┬────────┘
│    Logic         │  │  - AI task queue     │           │
└────────┬─────────┘  └──────────┬──────────┘           │
         │                       │              ←────────┘
         └───────────────────────┼─────────────────────────────────
                                 │
         ┌───────────────────────┼───────────────────┐
         ▼                       ▼                   ▼
┌─────────────────┐   ┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL      │   │  Redis           │  │  S3 / Minio      │
│  (Primary DB)    │   │  (Cache, Queue,  │  │  (File Storage)  │
│                  │   │   WebSocket)     │  │                  │
└─────────────────┘   └──────────────────┘  └──────────────────┘
```

### Key Technology Choices

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Auth tokens | `djangorestframework-simplejwt` | Stateless, refresh rotation |
| Async tasks | `Celery` + `Redis` broker | Background jobs, scheduled reports |
| Real-time | `Django Channels` + Redis channel layer | WebSocket for live dashboards, POS |
| Search | `django-elasticsearch-dsl` or PostgreSQL full-text | Product search, client search |
| File storage | `django-storages` + S3/MinIO | Invoices, documents, avatars |
| Email | `django-anymail` (SendGrid/Mailgun) | Transactional emails |
| PDF generation | `WeasyPrint` / `ReportLab` | Invoices, reports |
| Caching | Redis (`django-redis`) | API response caching |
| Audit log | `django-auditlog` | All model changes tracked |
| CORS | `django-cors-headers` | Nuxt frontend origin |
| i18n | `Django i18n` + Nuxt i18n | Multi-language support |

---

## 4. Multi-Tenancy — Company Model

### 4.1 Strategy

Each `Company` is a **fully isolated PostgreSQL schema** managed by `django-tenants`. All business data (users, transactions, stock, documents) lives inside the tenant schema. Only public/shared data (Company list, Domains) lives in the `public` schema.

```
public schema:
  - Company  (TenantMixin)
  - Domain   (DomainMixin)

Tenant schema (per Company):
  - User, StaffProfile, ClientProfile, SupplierProfile, AgentProfile
  - Department, Branch
  - All other ERP models (inventory, sales, accounting, etc.)


```

### 4.2 Company & Domain Models

```python
# apps/party/models/company.py
from django_tenants.models import TenantMixin, DomainMixin

class Company(TenantMixin):
    """One Company = one PostgreSQL schema = one tenant."""
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name             = models.CharField(max_length=200)
    slug             = models.SlugField(unique=True)               # used as schema_name
    logo             = models.ImageField(upload_to="logos/", blank=True)
    industry         = models.CharField(max_length=100, blank=True)
    base_currency    = models.CharField(max_length=3, default="USD")   # ISO 4217
    timezone         = models.CharField(max_length=63, default="UTC")
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    # django-tenants required fields
    schema_name      = models.CharField(max_length=63, unique=True)    # auto-set from slug
    auto_create_schema = True

    class Meta:
        app_label = "party"

class Domain(DomainMixin):
    """Maps subdomain/domain to a Company tenant."""
    # DomainMixin provides: domain, tenant FK, is_primary
    class Meta:
        app_label = "party"
```

### 4.3 Tenant-Aware Abstract Base Model

```python
# common/models.py

class TenantAwareModel(models.Model):
    """Abstract base for all tenant-scoped models.
    Audit fields are included on every model."""
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+"
    )


    class Meta:
        abstract = True
```

### 4.4 Django Settings — `django-tenants` Config

```python
# config/settings/base.py

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

TENANT_MODEL   = "party.Company"
TENANT_DOMAIN_MODEL = "party.Domain"

SHARED_APPS = [
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.party",        # Company + Domain live in public schema
]

TENANT_APPS = [
    "apps.hr",
    "apps.accounting",
    "apps.inventory",
    "apps.procurement",
    "apps.sales",
    "apps.ecommerce",
    "apps.pos",
    "apps.manufacturing",
    "apps.logistics",
    "apps.assets",
    "apps.projects",
    "apps.crm",
    "apps.reporting",
    "apps.notifications",
    "apps.integrations",
    "apps.agents",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]
```

---

## 5. Organisational Hierarchy — Department & Branch

### 5.1 Hierarchy Overview

```
Company (Tenant)
  └── Department  (functional division, e.g. Sales, Finance, Operations)
        └── Branch  (physical/operational location, e.g. Head Office, Kumasi Branch)
```

All transactional records (invoices, stock movements, leave requests, sales orders) carry a `branch` foreign key. Reports can be scoped to all branches, a single branch, or a department.

### 5.2 Models

```python
# apps/party/models/organisation.py

class Department(TenantAwareModel):
    name             = models.CharField(max_length=150,unique=True)
    parent           = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="children"
    )
    code             = models.CharField(max_length=4, unique=True)

    head             = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="led_departments"
    )
    cost_center_code = models.CharField(max_length=30, blank=True)
    is_active        = models.BooleanField(default=True)
    choice=(
        # ("B2B", "B2B"),
        # ("B2C", "B2C"),
        ("Wholesale Unit", "Wholesale Unit"),
        ("Retail Unit", "Retail Unit"),
        ("Manufacturing Unit", "Manufacturing Unit"),
    )
    departmenttype=models.CharField(_("Department Role"), max_length=50,choices=choice)
    

    class Meta:
        ordering = ["name"]
        unique_together=['name','code']


class Branch(TenantAwareModel):
    department       = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="branches"
    )
    name             = models.CharField(max_length=150)
    code             = models.CharField(max_length=4, unique=True)
    manager          = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="managed_branches"
    )
    is_headquarters  = models.BooleanField(default=False)
    is_active        = models.BooleanField(default=True)

    # Contact info attached via GenericRelation (see §6)
    contact_points   = GenericRelation("party.ContactPoint")
    addresses        = GenericRelation("party.Address")

    class Meta:
        verbose_name_plural = "branches"
        ordering = ["department__name", "name"]
        unique_together=['department','name']
```

### 5.3 User ↔ Branch/Department Assignment

| User Type | Assignment | Model Field |
|-----------|-----------|-------------|
| **Staff** | One or more Branches | `StaffProfile.branches` (M2M → Branch) |
| **Client** | One Department only | `ClientProfile.department` (FK → Department) |
| **Supplier** | One Department only | `SupplierProfile.department` (FK → Department) |
| **Agent** | Not assigned | — |

Staff can be re-assigned to additional branches by an admin. Clients and suppliers are scoped to a single department for focused portal access.

### 5.4 Profile Model Sketches

```python
# apps/party/models/profiles.py

class StaffProfile(TenantAwareModel):
    user         = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    branches     = models.ManyToManyField(Branch, related_name="staff")   # one or more
    employee_id  = models.CharField(max_length=30, unique=True)
    job_title    = models.CharField(max_length=100, blank=True)
    is_manager   = models.BooleanField(default=False)   # approval authority within branches
    hire_date    = models.DateField(null=True)
    avatar       = models.ImageField(upload_to="avatars/staff/", blank=True)

class ClientProfile(TenantAwareModel):
    user            = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department      = models.ForeignKey(Department, on_delete=models.PROTECT,
                                        related_name="clients")
    company_name    = models.CharField(max_length=200, blank=True)
    credit_limit    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_terms   = models.PositiveIntegerField(default=30)   # days
    loyalty_points  = models.PositiveIntegerField(default=0)
    tier            = models.CharField(max_length=20,
                                       choices=[("standard","Standard"),("silver","Silver"),
                                                ("gold","Gold"),("platinum","Platinum")],
                                       default="standard")

class SupplierProfile(TenantAwareModel):
    user                = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department          = models.ForeignKey(Department, on_delete=models.PROTECT,
                                            related_name="suppliers")
    company_name        = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=60, blank=True)
    payment_terms       = models.PositiveIntegerField(default=30)
    credit_limit        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bank_details        = models.JSONField(default=dict)   # encrypted at application layer
    rating              = models.DecimalField(max_digits=3, decimal_places=2, default=0)

class AgentProfile(TenantAwareModel):
    user             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    agent_type       = models.CharField(max_length=30,
                                        choices=[("monitor","Monitor"),("executor","Executor"),
                                                 ("analyst","Analyst"),("assistant","Assistant")])
    capabilities     = models.JSONField(default=list)
    assigned_modules = models.JSONField(default=list)
    status           = models.CharField(max_length=20,
                                        choices=[("active","Active"),("paused","Paused"),
                                                 ("error","Error")],
                                        default="active")
    api_key          = models.CharField(max_length=100, unique=True)
```

---

## 6. Generic Contact Model

### 6.1 Purpose

Any model in the ERP (Branch, ClientProfile, SupplierProfile, StaffProfile, Company) can have an arbitrary number of contact points (phone numbers, email addresses, websites) and physical addresses — attached via Django's `ContentType` framework without altering the target model's schema.

### 6.2 Models

```python
# apps/party/models/contact.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

CONTACT_TYPE_CHOICES = [
    ("phone",   "Phone"),
    ("email",   "Email"),
    ("website", "Website"),
    ("fax",     "Fax"),
    ("whatsapp","WhatsApp"),
]

ADDRESS_TYPE_CHOICES = [
    ("billing",  "Billing"),
    ("shipping", "Shipping"),
    ("office",   "Office"),
    ("warehouse","Warehouse"),
    ("other",    "Other"),
]

class ContactPoint(TenantAwareModel):
    """Phone numbers, email addresses, websites — attached to *any* model."""
    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id      = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    contact_type   = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    value          = models.CharField(max_length=255)    # the number/address/URL
    label          = models.CharField(max_length=50, blank=True)  # e.g. "Mobile", "Work"
    # is_primary     = models.BooleanField(default=False)
    is_verified    = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

class Address(TenantAwareModel):
    """Physical addresses — attached to *any* model."""
    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id      = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    address_type   = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)
    line1          = models.CharField(max_length=255)
    line2          = models.CharField(max_length=255, blank=True)
    city           = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True)
    country        = models.CharField(max_length=2)   # ISO 3166-1 alpha-2
    postal_code    = models.CharField(max_length=20, blank=True)
    is_primary     = models.BooleanField(default=False)
    latitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        verbose_name_plural = "addresses"
```

### 6.3 Usage Pattern

```python
# Attach contacts to a Branch
branch = Branch.objects.get(code="HQ")
ContactPoint.objects.create(
    content_object=branch,
    contact_type="phone",
    value="+1-555-000-1234",
    label="Reception",
    is_primary=True,
)
Address.objects.create(
    content_object=branch,
    address_type="office",
    line1="123 Main Street",
    city="Accra",
    country="GH",
    is_primary=True,
)

# Retrieve contacts
contacts = ContactPoint.objects.filter(
    content_type=ContentType.objects.get_for_model(Branch),
    object_id=branch.pk,
)
```

### 6.4 API Endpoints

```
GET|POST       /api/v1/party/contact-points/
GET|PATCH|DEL  /api/v1/party/contact-points/{id}/
GET|POST       /api/v1/party/addresses/
GET|PATCH|DEL  /api/v1/party/addresses/{id}/
```

---

## 7. Django Backend — Project Structure

```
backend/
├── config/                        # Django project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py                    # Root URL config
│   ├── asgi.py                    # ASGI + Channels
│   └── wsgi.py
│
├── apps/
│   ├── party/                     # Users, Profiles, Company, Dept, Branch, Contacts
│   ├── hr/                        # Human Resources + Payroll
│   ├── accounting/                # Accounting, GL, AR, AP, Budgeting
│   ├── inventory/                 # Stock, warehouses, lots, expiry
│   ├── procurement/               # Purchase orders, RFQs, vendors
│   ├── sales/                     # Sales orders, quotations, CRM
│   ├── ecommerce/                 # Storefront, cart, product catalog
│   ├── pos/                       # Point of Sale sessions, transactions
│   ├── manufacturing/             # BOM, work orders, MRP
│   ├── logistics/                 # Shipments, delivery routes, tracking
│   ├── assets/                    # Fixed assets, depreciation
│   ├── projects/                  # Project management, tasks, time logs
│   ├── crm/                       # Leads, opportunities, contacts
│   ├── reporting/                 # Report engine, dashboards, KPIs
│   ├── notifications/             # In-app, email, SMS, push
│   ├── integrations/              # Third-party APIs (payment, shipping)
│   └── agents/                    # AI agent definitions, tasks, logs
│
├── common/
│   ├── models.py                  # TenantAwareModel abstract base
│   ├── permissions.py             # Custom DRF permission classes
│   ├── pagination.py              # Standard pagination classes
│   ├── exceptions.py              # Custom exception handlers
│   ├── filters.py                 # django-filter base filters
│   ├── renderers.py               # Custom response renderers
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
django-tenants>=3.6          # Multi-tenancy via PostgreSQL schemas
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
django-celery-results>=2.5
Pillow>=10.0
WeasyPrint>=60.0
psycopg2-binary>=2.9
redis>=5.0
boto3>=1.34
python-decouple>=3.8
drf-spectacular>=0.27        # OpenAPI schema generation
langchain>=0.2               # AI agent framework
openai>=1.0                  # LLM provider
```

---

## 8. Django Apps & Models (Module by Module)

---

### 8.1 `apps/party` — Users, Profiles & Organisational Structure

#### Models
```
Company              (TenantMixin — public schema, see §4)
Domain               (DomainMixin — public schema, see §4)
Department           (TenantAwareModel, see §5)
Branch               (TenantAwareModel, see §5)
ContactPoint         (TenantAwareModel, GenericForeignKey, see §6)
Address              (TenantAwareModel, GenericForeignKey, see §6)

User                 (AbstractBaseUser + PermissionsMixin — see §2.6)

StaffProfile         (OneToOne → User[staff])
  - branches         M2M → Branch           (one or more branches)
  - employee_id      CharField unique
  - job_title        CharField
  - is_manager       BooleanField(default=False)
  - hire_date        DateField
  - avatar           ImageField

ClientProfile        (OneToOne → User[client])
  - department       FK → Department        (one department only)
  - company_name     CharField
  - credit_limit     DecimalField
  - payment_terms    PositiveIntegerField   (days)
  - loyalty_points   PositiveIntegerField
  - tier             (standard/silver/gold/platinum)
  - contact_points   GenericRelation → ContactPoint
  - addresses        GenericRelation → Address

SupplierProfile      (OneToOne → User[supplier])
  - department       FK → Department        (one department only)
  - company_name     CharField
  - registration_number CharField
  - payment_terms    PositiveIntegerField
  - credit_limit     DecimalField
  - bank_details     JSONField (encrypted)
  - rating           DecimalField (auto-computed)
  - product_categories M2M → Category
  - contact_points   GenericRelation → ContactPoint
  - addresses        GenericRelation → Address

AgentProfile         (OneToOne → User[agent])
  - agent_type       (monitor/executor/analyst/assistant)
  - capabilities     JSONField
  - assigned_modules JSONField
  - status           (active/paused/error)
  - api_key          CharField unique
```

#### API Endpoints
```
POST   /api/v1/auth/register/staff/
POST   /api/v1/auth/register/client/
POST   /api/v1/auth/register/supplier/
POST   /api/v1/auth/login/                 → returns access + refresh JWT
POST   /api/v1/auth/refresh/
POST   /api/v1/auth/logout/
POST   /api/v1/auth/password/change/
POST   /api/v1/auth/password/reset/
POST   /api/v1/auth/password/reset/confirm/
GET    /api/v1/auth/me/
PATCH  /api/v1/auth/me/

GET|POST       /api/v1/party/users/                (admin/superuser)
GET|PATCH|DEL  /api/v1/party/users/{id}/
GET|POST       /api/v1/party/users/{id}/groups/    (assign/remove groups)
GET            /api/v1/party/users/{id}/activity/
POST           /api/v1/party/users/{id}/impersonate/   (superuser)
POST           /api/v1/party/users/{id}/deactivate/

GET|POST       /api/v1/party/departments/
GET|PATCH|DEL  /api/v1/party/departments/{id}/
GET|POST       /api/v1/party/branches/
GET|PATCH|DEL  /api/v1/party/branches/{id}/

GET|POST       /api/v1/party/contact-points/
GET|PATCH|DEL  /api/v1/party/contact-points/{id}/
GET|POST       /api/v1/party/addresses/
GET|PATCH|DEL  /api/v1/party/addresses/{id}/

GET|POST       /api/v1/auth/groups/               (admin: list/create groups)
GET|PATCH|DEL  /api/v1/auth/groups/{id}/
GET|POST       /api/v1/auth/groups/{id}/permissions/
```

---

### 8.2 `apps/hr` — Human Resources & Payroll

#### Models
```
Department
  - name, code, parent FK self, head FK User
  - cost_center_code

JobTitle
  - title, grade, salary_band_min, salary_band_max

Employee                (proxy/extension of StaffProfile)
  - employment_type     (full_time/part_time/contract/intern)
  - status              (active/on_leave/terminated)
  - probation_end_date
  - contract_end_date (nullable)
  - skills              M2M → Skill
  - qualifications      JSONField

Skill / Certification
  - name, category, expiry_required

Attendance
  - employee FK, date, check_in, check_out
  - status              (present/absent/late/half_day/holiday)
  - device_id, location (lat/lng optional)
  - overtime_hours

LeaveType
  - name, days_allowed_per_year, carry_forward, paid

LeaveAllocation
  - employee FK, leave_type FK, year, days_allocated, days_used

LeaveRequest
  - employee FK, leave_type FK, start_date, end_date
  - status              (pending/approved/rejected/cancelled)
  - approver FK User, reason, attachments

PayrollPeriod
  - name, start_date, end_date, status (draft/processed/paid)

PayrollEntry
  - employee FK, period FK
  - basic_salary, allowances JSONField, deductions JSONField
  - gross_pay, tax_amount, net_pay
  - status (draft/approved/paid), payment_date, payment_ref

Expense / ExpenseClaim
  - employee FK, category, amount, currency, receipt
  - status (pending/approved/rejected/reimbursed)
  - approver FK, notes

Training
  - title, description, trainer, start_date, end_date
  - participants M2M Employee, completion_status JSONField

PerformanceReview
  - employee FK, reviewer FK, period, scores JSONField
  - overall_rating, comments, goals_next_period
```

#### API Endpoints
```
/api/v1/hr/departments/
/api/v1/hr/employees/
/api/v1/hr/employees/{id}/attendance/
/api/v1/hr/employees/{id}/payslips/
/api/v1/hr/employees/{id}/leaves/
/api/v1/hr/leave-requests/
/api/v1/hr/leave-types/
/api/v1/hr/leave-allocations/
/api/v1/hr/payroll/periods/
/api/v1/hr/payroll/entries/
/api/v1/hr/payroll/run/         POST → triggers Celery task
/api/v1/hr/expenses/
/api/v1/hr/training/
/api/v1/hr/performance-reviews/
```

---

### 8.3 `apps/accounting` — Accounting, AR, AP, Budgeting

#### Models
```
FiscalYear
  - name, start_date, end_date, status (open/closed)

AccountType (enum: asset/liability/equity/revenue/expense)

ChartOfAccounts (COA)
  - code, name, type AccountType, parent FK self
  - is_header, balance_type (debit/credit), currency

JournalEntry
  - reference, date, description, fiscal_year FK, branch FK Branch
  - status (draft/posted/voided)
  - created_by FK User

JournalLine
  - journal FK, account FK COA
  - debit, credit, currency, description
  - cost_center FK Department

Currency
  - code (ISO4217), name, symbol, is_base

ExchangeRate
  - from_currency FK, to_currency FK, rate, date

Invoice (AR)
  - invoice_number, client FK ClientProfile
  - branch FK Branch
  - issue_date, due_date, currency, tax_rate
  - status (draft/sent/partial/paid/overdue/voided)
  - line_items JSONField, subtotal, tax, total
  - sales_order FK (optional)

Bill (AP — supplier invoices)
  - bill_number, supplier FK SupplierProfile
  - branch FK Branch
  - issue_date, due_date, currency
  - status (draft/received/partial/paid/overdue)
  - line_items JSONField, subtotal, tax, total
  - purchase_order FK

Payment (both AR and AP)
  - payment_type (inbound/outbound)
  - reference, amount, currency, payment_date
  - payment_method (cash/bank/card/mobile_money)
  - account FK COA (bank/cash account)
  - branch FK Branch
  - invoice FK (nullable), bill FK (nullable)
  - exchange_rate (for multi-currency)

TaxRate / TaxGroup
  - name, rate, applies_to (sales/purchases/both)
  - tax_account FK COA

BudgetPlan
  - name, fiscal_year FK, department FK, status
  - lines M2M → BudgetLine

BudgetLine
  - account FK COA, period (month), budgeted_amount, actual_amount (computed)

Expense (company expense, distinct from HR expense claim)
  - category FK, amount, currency, date, description
  - account FK COA, paid_by FK User, branch FK Branch

FIXED ASSETS → see apps/assets
```

#### API Endpoints
```
/api/v1/accounting/fiscal-years/
/api/v1/accounting/coa/                            (Chart of Accounts)
/api/v1/accounting/journal-entries/
/api/v1/accounting/journal-entries/{id}/post/
/api/v1/accounting/invoices/
/api/v1/accounting/invoices/{id}/send/
/api/v1/accounting/invoices/{id}/record-payment/
/api/v1/accounting/bills/
/api/v1/accounting/bills/{id}/approve/
/api/v1/accounting/payments/
/api/v1/accounting/tax-rates/
/api/v1/accounting/budgets/
/api/v1/accounting/currencies/
/api/v1/accounting/exchange-rates/
/api/v1/accounting/reports/profit-loss/            (generated report)
/api/v1/accounting/reports/balance-sheet/
/api/v1/accounting/reports/cash-flow/
/api/v1/accounting/reports/trial-balance/
/api/v1/accounting/reports/ar-aging/
/api/v1/accounting/reports/ap-aging/
```

---

### 8.4 `apps/inventory` — Inventory & Warehouse Management

#### Models
```
Category
  - name, slug, parent FK self, description, image

Brand
  - name, logo, country_of_origin

UnitOfMeasure (UOM)
  - name, abbreviation, uom_type (unit/weight/volume/length)
  - conversion_factor (relative to SI base)

Product
  - sku, name, slug, barcode (EAN/UPC)
  - category FK, brand FK
  - uom FK, purchase_uom FK, sale_uom FK
  - description, short_description
  - images M2M ProductImage
  - product_type (storable/consumable/service/digital)
  - is_active, is_featured
  - tags M2M
  - attributes JSONField       (color, size, etc.)
  - weight, dimensions JSONField
  - hs_code (customs)

ProductVariant
  - product FK, sku_suffix, attributes JSONField (variant-specific)
  - barcode, weight, price_modifier

ProductImage
  - product FK, image, alt_text, is_primary, sort_order

Warehouse
  - name, code, address FK Address
  - manager FK User, type (main/branch/virtual/transit)
  - is_active

WarehouseLocation (aisle/rack/bin system)
  - warehouse FK, code, name, location_type (aisle/rack/bin/zone)
  - parent FK self, capacity

StockLot
  - product FK (or variant FK), lot_number
  - manufacture_date, expiry_date
  - supplier FK SupplierProfile
  - initial_qty, current_qty, reserved_qty
  - unit_cost, currency
  - status (active/expired/recalled/consumed)
  - warehouse FK, location FK

StockMove (every stock movement)
  - product FK, variant FK (nullable)
  - lot FK (nullable)
  - from_location FK (nullable → means receipt)
  - to_location FK (nullable → means issue)
  - quantity, uom FK
  - move_type (receipt/issue/transfer/adjustment/scrap/return)
  - reference (PO/SO/WO/manual)
  - done_at, done_by FK User

StockValuation
  - product FK, date, qty_on_hand, avg_cost, total_value
  - valuation_method (FIFO/AVCO/standard)

InventoryAdjustment
  - reference, date, warehouse FK, reason
  - status (draft/validated)
  - lines M2M → AdjustmentLine

AdjustmentLine
  - adjustment FK, product FK, lot FK
  - system_qty, actual_qty, difference, unit_cost

Scrap
  - product FK, lot FK, qty, reason, date, cost

ReorderRule
  - product FK, warehouse FK
  - min_qty, max_qty, reorder_qty
  - lead_time_days, last_triggered_at

StockAlert (system-generated)
  - alert_type (stockout/low_stock/expiry_warning/expiry_overdue/recall)
  - product FK, lot FK (nullable), warehouse FK
  - threshold, current_qty, expiry_date
  - created_at, resolved_at, notified_suppliers JSONField
```

#### API Endpoints
```
/api/v1/inventory/categories/
/api/v1/inventory/brands/
/api/v1/inventory/products/
/api/v1/inventory/products/{id}/variants/
/api/v1/inventory/products/{id}/stock/          (per-warehouse breakdown)
/api/v1/inventory/products/{id}/lots/
/api/v1/inventory/products/{id}/moves/
/api/v1/inventory/warehouses/
/api/v1/inventory/warehouses/{id}/locations/
/api/v1/inventory/stock-lots/
/api/v1/inventory/stock-moves/
/api/v1/inventory/adjustments/
/api/v1/inventory/adjustments/{id}/validate/
/api/v1/inventory/reorder-rules/
/api/v1/inventory/alerts/
/api/v1/inventory/valuation/
/api/v1/inventory/scrap/
```

---

### 8.5 `apps/procurement` — Purchasing & Vendor Management

#### Models
```
PurchaseRequisition (PR)
  - reference, requested_by FK User, department FK
  - status (draft/submitted/approved/rejected/converted)
  - lines M2M → PRLine, urgency (low/normal/high/critical)

PRLine
  - requisition FK, product FK, qty, preferred_supplier FK
  - estimated_unit_cost, notes

RequestForQuotation (RFQ)
  - reference, pr FK (nullable), created_by FK
  - status (draft/sent/received/expired)
  - suppliers M2M SupplierProfile
  - deadline

RFQResponse
  - rfq FK, supplier FK
  - status (pending/submitted/accepted/rejected)
  - lines M2M → RFQResponseLine, valid_until, notes

RFQResponseLine
  - response FK, product FK, qty, unit_price, currency
  - lead_time_days, terms

PurchaseOrder (PO)
  - po_number, supplier FK, created_by FK
  - rfq_response FK (nullable), pr FK (nullable)
  - status (draft/confirmed/partially_received/received/cancelled)
  - currency, exchange_rate, payment_terms
  - expected_delivery, shipping_address FK
  - lines M2M → POLine, notes
  - subtotal, tax, total

POLine
  - po FK, product FK (or variant FK), description
  - ordered_qty, received_qty, billed_qty
  - unit_price, tax_rate, line_total
  - discount, discount_type

GoodsReceiptNote (GRN)
  - reference, po FK, received_by FK, received_at
  - warehouse FK, status (draft/confirmed)
  - lines M2M → GRNLine

GRNLine
  - grn FK, po_line FK, product FK
  - lot FK (or creates new), quantity, location FK
  - condition (good/damaged/rejected), notes

SupplierEvaluation
  - supplier FK, period, evaluator FK
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

### 8.6 `apps/sales` — Sales Orders, Quotations & CRM

#### Models
```
PriceList
  - name, currency, is_default
  - lines M2M → PriceListLine, valid_from, valid_to

PriceListLine
  - pricelist FK, product FK (or category FK)
  - price, min_qty, discount_pct

Discount / PromotionRule
  - name, discount_type (pct/fixed/buy_x_get_y)
  - value, min_order_amount, max_uses
  - applicable_to (all/category/product/client_tier)
  - start_date, end_date, is_active

Quotation
  - quote_number, client FK ClientProfile (or lead FK)
  - issued_by FK User, issue_date, expiry_date
  - status (draft/sent/viewed/accepted/rejected/expired)
  - currency, pricelist FK
  - lines M2M → QuotationLine
  - notes, terms, discount, tax, subtotal, total

QuotationLine
  - quotation FK, product FK, description
  - qty, unit_price, discount, tax_rate, line_total

SalesOrder (SO)
  - so_number, client FK, quotation FK (nullable)
  - issued_by FK User
  - status (draft/confirmed/picking/shipped/delivered/invoiced/cancelled)
  - currency, pricelist FK, payment_terms
  - shipping_address FK, billing_address FK
  - lines M2M → SOLine, priority
  - discount, tax, subtotal, total, commission_rate

SOLine
  - so FK, product FK (or variant FK)
  - qty, delivered_qty, invoiced_qty
  - unit_price, discount, tax_rate, line_total
  - warehouse FK, lot FK (nullable)

Delivery (from SO)
  - reference, so FK, warehouse FK
  - status (draft/ready/done/cancelled)
  - scheduled_date, done_date
  - carrier FK, tracking_number
  - lines M2M → DeliveryLine

DeliveryLine
  - delivery FK, so_line FK, product FK
  - lot FK, qty_to_deliver, qty_done, location FK

Return / ReturnLine (RMA)
  - so FK or invoice FK, reason, return_date
  - lines M2M → ReturnLine
  - refund_method (credit_note/replacement/cash)
  - status (pending/approved/received/processed)

Commission
  - sales_rep FK, so FK, rate, amount, status (pending/paid)
```

---

### 8.7 `apps/crm` — CRM Module

#### Models
```
Lead
  - first_name, last_name, email, phone, company
  - source (web/referral/campaign/cold/trade_show)
  - status (new/contacted/qualified/disqualified)
  - assigned_to FK User, created_at

Contact (qualified lead or existing client contact)
  - user FK (nullable, if client exists)
  - company FK Organization, position
  - email, phone, notes, tags

Organization
  - name, industry, size, website, address FK

Opportunity
  - title, contact FK, organization FK
  - assigned_to FK User
  - stage (qualification/proposal/negotiation/closed_won/closed_lost)
  - estimated_value, currency, probability_pct
  - expected_close_date, actual_close_date
  - quotation FK (nullable)

Activity (calls, meetings, tasks, emails linked to leads/opportunities)
  - activity_type (call/meeting/email/task/note)
  - subject, description, due_date, done_date
  - related_to_type (lead/opportunity/contact)
  - related_to_id, assigned_to FK User
  - outcome

Campaign
  - name, type (email/sms/social/event)
  - status (draft/active/paused/completed)
  - start_date, end_date, budget
  - target_audience JSONField
  - leads M2M Lead, open_rate, click_rate, conversions

CustomerFeedback / Survey
  - client FK, nps_score, csat_score, comments
  - related_order FK (nullable), submitted_at
```

---

### 8.8 `apps/ecommerce` — E-Commerce Storefront

#### Models
```
Store
  - name, domain, logo, banner
  - currency, default_language, is_active
  - seo_title, seo_description

ProductListing (extends/projects Product for storefront visibility)
  - product FK, store FK
  - is_published, published_at
  - ecommerce_price (overrides pricelist)
  - description_html (rich text)
  - gallery M2M, featured_until
  - meta_title, meta_description, slug (URL slug)

Cart
  - session_id (for guests), client FK (nullable)
  - currency, created_at, updated_at, expires_at

CartItem
  - cart FK, product FK (or variant FK)
  - qty, unit_price, discount, line_total
  - notes (gift message etc.)

Wishlist
  - client FK, name, is_public
  - items M2M Product

Order (E-Commerce order, maps to SalesOrder in sales app)
  - order_number, client FK, cart FK
  - so FK (created on checkout)
  - billing_address FK, shipping_address FK
  - status (pending/payment_pending/paid/processing/shipped/delivered/cancelled/refunded)
  - payment_status (unpaid/partial/paid/refunded)
  - payment_method, payment_ref
  - coupon_code FK (nullable)
  - subtotal, discount, shipping_cost, tax, total
  - notes, ip_address (security)

OrderTracking
  - order FK, status, message, location, timestamp, notified

Review (product review)
  - product FK, client FK
  - rating (1-5), title, body
  - is_verified_purchase, is_approved
  - helpful_count, images M2M

Coupon / VoucherCode
  - code, discount_type (pct/fixed/free_shipping)
  - value, min_order, max_uses, used_count
  - valid_from, valid_to, is_active
  - applicable_products M2M, applicable_categories M2M

ShippingZone
  - name, countries JSONField

ShippingMethod
  - name, zone FK, carrier
  - price_type (fixed/weight_based/value_based/free_over)
  - rate, max_weight, min_order_for_free
  - estimated_days

PaymentGateway (config)
  - name, provider (stripe/paystack/flutterwave/paypal)
  - is_active, config JSONField (encrypted), currencies JSONField
```

---

### 8.9 `apps/pos` — Point of Sale

#### Models
```
POSConfiguration
  - name, warehouse FK, store FK, currency
  - receipt_header, receipt_footer, logo
  - open_with_session, auto_close_time

POSSession
  - pos_config FK, cashier FK User
  - opened_at, closed_at
  - opening_balance, closing_balance
  - status (open/closing/closed)
  - cash_transactions, cash_expected, cash_difference

POSOrder
  - session FK, order_number
  - client FK (nullable — walk-in or account customer)
  - status (draft/paid/invoiced/cancelled/refunded)
  - lines M2M → POSOrderLine
  - subtotal, discount, tax, total
  - payment_lines M2M → POSPaymentLine
  - is_return, return_reason

POSOrderLine
  - order FK, product FK (or variant FK)
  - lot FK (nullable), qty, unit_price
  - discount, tax_rate, line_total, note

POSPaymentLine
  - order FK, payment_method (cash/card/mobile_money/credit/voucher)
  - amount, reference (card last4, mobile ref)

POSCashMovement
  - session FK, move_type (in/out)
  - amount, reason, done_by FK User, done_at

HeldOrder (parked orders)
  - session FK, customer_name, lines JSONField, created_at
```

---

### 8.10 `apps/manufacturing` — Manufacturing & MRP

#### Models
```
BillOfMaterials (BOM)
  - product FK (finished good), bom_type (standard/phantom/by-product)
  - qty (produces), uom FK
  - version, is_active

BOMLine
  - bom FK, component FK Product (or variant)
  - qty, uom FK, scrap_pct
  - operation FK (nullable)

RoutingOperation
  - name, workcenter FK, duration_minutes
  - setup_time, teardown_time, cost_per_hour

WorkCenter
  - name, code, capacity, efficiency_pct
  - cost_per_hour, department FK

WorkOrder
  - reference, bom FK, product FK
  - planned_qty, produced_qty, scrap_qty
  - status (draft/confirmed/in_progress/done/cancelled)
  - scheduled_start, scheduled_end, actual_start, actual_end
  - warehouse FK, responsible FK User

WorkOrderLine (MO component consumption)
  - work_order FK, product FK (component)
  - lot FK (nullable), qty_to_consume, qty_consumed

ProductionLot (finished goods lot)
  - work_order FK, lot FK StockLot

MaterialRequirementPlan (MRP Run)
  - run_date, horizon_days, status
  - planned_orders JSONField (summary)

ByProduct
  - work_order FK, product FK, qty, uom FK, lot FK
```

---

### 8.11 `apps/logistics` — Shipping & Delivery

#### Models
```
Carrier
  - name, code, tracking_url_template, contact, is_active

ShipmentRoute
  - name, origin_address FK, destination_address FK
  - carrier FK, estimated_days, cost

Shipment
  - reference, carrier FK, tracking_number
  - origin FK Address, destination FK Address
  - status (pending/dispatched/in_transit/out_for_delivery/delivered/failed/returned)
  - shipped_at, estimated_delivery, actual_delivery
  - weight, dimensions JSONField, declared_value
  - related_so FK (nullable), related_po FK (nullable)

ShipmentEvent (tracking timeline)
  - shipment FK, status, location, message, timestamp, source

DeliveryRoute (for owned fleet)
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

### 8.12 `apps/assets` — Fixed Asset Management

#### Models
```
AssetCategory
  - name, depreciation_method (straight_line/declining_balance/units_of_production)
  - useful_life_years, salvage_value_pct
  - asset_account FK COA, depreciation_account FK COA, accumulated_account FK COA

FixedAsset
  - asset_number, name, category FK
  - purchase_date, in_service_date, purchase_price, currency
  - supplier FK, purchase_order FK (nullable)
  - location FK (department/warehouse), assigned_to FK User
  - status (active/idle/under_maintenance/disposed/sold)
  - serial_number, barcode, image
  - current_book_value (auto-computed)

AssetDepreciation
  - asset FK, period_date, depreciation_amount, accumulated_depreciation
  - book_value_after, journal_entry FK (auto-posted)

AssetMaintenance
  - asset FK, maintenance_type (preventive/corrective)
  - scheduled_date, done_date, cost, technician
  - description, vendor, next_due_date

AssetDisposal
  - asset FK, disposal_date, disposal_method (sold/scrapped/donated)
  - sale_price (if sold), proceeds_account FK COA
  - gain_or_loss (computed), journal_entry FK
```

---

### 8.13 `apps/projects` — Project Management

#### Models
```
Project
  - name, code, client FK (nullable)
  - manager FK User, team M2M User
  - status (planning/active/on_hold/completed/cancelled)
  - start_date, end_date, budget, currency
  - progress_pct (auto-computed), priority

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

### 8.14 `apps/reporting` — Reports, Dashboards & KPIs

#### Models & Logic
```python
# Reports are mostly generated dynamically (no persistent model needed for most)
# But we store:

SavedReport
  - name, module, query_params JSONField
  - created_by FK, is_shared, schedule (cron)
  - last_run_at, output_format (pdf/excel/csv)

ScheduledReport
  - saved_report FK, recipients M2M User
  - cron_expression, next_run_at
  - last_status (success/failed)

KPISnapshot (persisted for dashboards)
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
Finance:          P&L, Balance Sheet, Cash Flow, Trial Balance, AR/AP Aging
Inventory:        Stock Valuation, Stock Movement, Expiry Report, Reorder Report,
                  FIFO/AVCO Costing Report, Dead Stock
Procurement:      PO Status, Supplier Performance, Spend Analysis
Sales:            Sales by Product/Category/Rep/Period, Pipeline Report,
                  Customer Lifetime Value, Returns Analysis
HR:               Headcount, Attendance Summary, Leave Summary, Payroll Summary
POS:              Daily/Weekly/Monthly Sales, Session Summary, Top Products
Manufacturing:    Production vs Plan, Scrap Rate, Work Center Utilization
Projects:         Project Status, Time & Cost, Resource Utilization
Supplier Portal:  Product Sales Velocity, Stockout History, Expiry Forecast,
                  Revenue Share by Product
```

---

### 8.15 `apps/notifications` — Notification Center

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
- Leave request status (employee)
- Invoice overdue (finance team)
- Bill payment due (finance team)
- New GRN received (procurement)
- PO awaiting approval
- New lead/opportunity (assigned rep)
- Agent action completed / requires attention (staff)
- New product review submitted
- Payroll processed (employee)
```

---

### 8.16 `apps/agents` — AI Agent Core

#### Models
```
AgentDefinition
  - name, slug, description, agent_type
  - capabilities JSONField         # what modules it can access
  - model_config JSONField         # LLM, temperature, max_tokens
  - system_prompt, tools_manifest JSONField
  - is_active

AgentTask
  - agent FK AgentDefinition, triggered_by FK User (nullable — can be scheduled)
  - task_type, input_data JSONField
  - status (pending/running/completed/failed/requires_approval)
  - output_data JSONField, error_message
  - started_at, completed_at
  - requires_human_approval, approved_by FK, approved_at

AgentAction (granular steps within a task)
  - task FK, step_number, action_type
  - tool_called, tool_input JSONField, tool_output JSONField
  - timestamp, duration_ms

AgentMemory (persistent context)
  - agent FK, key, value JSONField, updated_at

AgentAlert (agent-generated alerts → routed to notifications)
  - agent FK, alert_type, severity (low/medium/high/critical)
  - title, body, data JSONField, resolved_at
  - target_user FK (or broadcast to role)
```

#### Built-in Agents
```
1. InventoryMonitorAgent
   - Watches stock levels every 15 min (Celery beat)
   - Fires stockout/low-stock alerts
   - Drafts purchase requisitions for items below reorder point
   - Notifies relevant suppliers of stockout events

2. ExpiryWatcherAgent
   - Scans lots daily for expiry within 7 / 14 / 30 days
   - Sends reports to suppliers with affected items
   - Suggests markdown pricing or transfer to clearance

3. FinanceAnalystAgent
   - Runs daily: reconciles AR/AP, flags overdue invoices
   - Generates weekly P&L summary for management
   - Alerts on cash flow anomalies

4. SalesAssistantAgent
   - Auto-qualifies new leads from web form
   - Suggests upsell/cross-sell based on order history
   - Drafts quotations from chat input

5. ProcurementAgent
   - Auto-sends RFQs when PRs are approved
   - Compares RFQ responses and recommends best vendor
   - Drafts POs pending staff approval

6. ReportBotAgent
   - Accepts natural language report requests
   - Generates and emails scheduled reports

7. FraudDetectionAgent
   - Monitors POS and e-commerce transactions
   - Flags unusual patterns (large discounts, after-hours, etc.)
```

---

## 9. REST API Design Standards

### Response Envelope
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "count": 150,
    "total_pages": 8
  },
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
    "fields": {
      "email": ["Enter a valid email address."]
    }
  }
}
```

### Conventions
- `GET /resources/` — list (paginated, filterable, searchable)
- `POST /resources/` — create
- `GET /resources/{id}/` — detail
- `PATCH /resources/{id}/` — partial update
- `DELETE /resources/{id}/` — soft delete (set `is_active=False`)
- `POST /resources/{id}/{action}/` — state machine transitions (e.g., `/confirm/`, `/approve/`)
- Versioning: `/api/v1/` prefix
- Pagination: `?page=1&page_size=20`
- Filtering: `django-filter` — `?status=active&category=5`
- Ordering: `?ordering=-created_at`
- Search: `?search=keyword`
- Date range: `?date_after=2025-01-01&date_before=2025-12-31`
- OpenAPI docs: `/api/v1/schema/` (drf-spectacular), UI at `/api/v1/docs/`
- WebSocket channels: `ws://host/ws/notifications/`, `ws://host/ws/pos/{session_id}/`, `ws://host/ws/agents/`

---

## 10. NuxtJS Frontend — Project Structure

```
frontend/
├── app.vue
├── nuxt.config.ts
├── tailwind.config.ts                    # Nuxt UI extends Tailwind
├── tsconfig.json
│
├── assets/
│   ├── css/
│   │   ├── main.css                      # Global styles, CSS vars
│   │   └── themes/                       # Light/dark token overrides
│   └── icons/                            # Custom SVG icons
│
├── components/
│   ├── ui/                               # Custom Reka UI-based components
│   │   ├── DataTable/                    # Full-featured table (sort, filter, pagination)
│   │   │   ├── DataTable.vue
│   │   │   ├── DataTableColumn.vue
│   │   │   └── DataTableFilters.vue
│   │   ├── Charts/                       # Chart wrappers (ECharts / Chart.js)
│   │   │   ├── BarChart.vue
│   │   │   ├── LineChart.vue
│   │   │   ├── PieChart.vue
│   │   │   ├── AreaChart.vue
│   │   │   └── KpiCard.vue
│   │   ├── Form/
│   │   │   ├── FormField.vue
│   │   │   ├── SearchSelect.vue          # Async remote search select (Reka Combobox)
│   │   │   ├── DateRangePicker.vue       # Reka Popover + Calendar
│   │   │   ├── FileUpload.vue
│   │   │   ├── RichTextEditor.vue        # Tiptap integration
│   │   │   ├── CurrencyInput.vue
│   │   │   └── BarcodeScanner.vue        # WebRTC barcode scan
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
│   │   │   └── CommandPalette.vue       # Global search/action (Reka Dialog + Combobox)
│   │   ├── Timeline.vue                  # Activity/audit timeline (Reka)
│   │   ├── StatusBadge.vue
│   │   ├── AvatarGroup.vue
│   │   └── PrintFrame.vue               # Print preview wrapper
│   │
│   ├── modules/                          # Feature-specific components
│   │   ├── inventory/
│   │   ├── accounting/
│   │   ├── hr/
│   │   ├── sales/
│   │   ├── pos/
│   │   ├── procurement/
│   │   ├── ecommerce/
│   │   ├── agents/
│   │   └── ...
│   │
│   └── shared/
│       ├── NotificationBell.vue
│       ├── UserAvatarMenu.vue
│       ├── BranchSelector.vue           # Dropdown to switch active branch
│       ├── TenantSwitcher.vue           # Switch between tenants (superuser)
│       ├── ThemeToggle.vue
│       └── LanguageSwitcher.vue
│
├── composables/
│   ├── useApi.ts                         # Axios/ofetch wrapper, token injection
│   ├── useAuth.ts
│   ├── useCurrentUser.ts
│   ├── usePagination.ts
│   ├── useFilters.ts
│   ├── useWebSocket.ts                   # WS connection manager
│   ├── useNotifications.ts
│   ├── usePermissions.ts                 # Groups-aware: hasGroup(), hasPerm(), isManager()
│   ├── useBranch.ts                      # Active branch selection helper
│   ├── usePrint.ts
│   ├── useCurrency.ts
│   ├── useToast.ts                       # Wraps Nuxt UI useToast
│   ├── modules/
│   │   ├── useInventory.ts
│   │   ├── useAccounting.ts
│   │   ├── useSales.ts
│   │   └── ...
│   └── useAgent.ts
│
├── layouts/
│   ├── default.vue                      # Staff ERP layout (sidebar + topbar)
│   ├── client.vue                       # Client portal layout
│   ├── supplier.vue                     # Supplier portal layout
│   ├── agent.vue                        # Agent dashboard layout
│   ├── storefront.vue                   # E-commerce public layout
│   ├── pos.vue                          # Full-screen POS layout
│   ├── auth.vue                         # Login/register pages
│   └── print.vue                        # Printable documents
│
├── middleware/
│   ├── auth.ts                          # Redirect to login if no token
│   ├── requireStaff.ts
│   ├── requireClient.ts
│   ├── requireSupplier.ts
│   ├── requirePermission.ts             # Checks Django permission string (groups-aware)
│   ├── requireManager.ts                # Requires is_manager=true
│   └── portal-router.ts                # Routes user_type → correct portal on login
│
├── pages/
│   ├── auth/
│   │   ├── login.vue
│   │   ├── register.vue
│   │   ├── forgot-password.vue
│   │   └── reset-password.vue
│   │
│   ├── (staff)/                         # Staff ERP portal
│   │   ├── index.vue                    # Main dashboard
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
│   │   │   ├── groups/                  # Group & permission management (admin only)
│   │   │   ├── branches/
│   │   │   └── departments/
│   │   └── notifications/
│   │
│   ├── (client)/                        # Client portal
│   │   ├── index.vue
│   │   ├── orders/
│   │   ├── invoices/
│   │   ├── quotes/
│   │   ├── wishlist.vue
│   │   ├── addresses.vue
│   │   └── profile.vue
│   │
│   ├── (supplier)/                      # Supplier portal
│   │   ├── index.vue                    # Supplier dashboard
│   │   ├── products/
│   │   ├── stock-alerts/
│   │   ├── expiry-reports/
│   │   ├── purchase-orders/
│   │   ├── invoices/
│   │   └── performance/
│   │
│   ├── store/                           # Public e-commerce storefront
│   │   ├── index.vue
│   │   ├── products/
│   │   │   ├── index.vue
│   │   │   └── [slug].vue
│   │   ├── categories/
│   │   │   └── [slug].vue
│   │   ├── cart.vue
│   │   ├── checkout/
│   │   │   ├── index.vue
│   │   │   ├── shipping.vue
│   │   │   ├── payment.vue
│   │   │   └── confirmation.vue
│   │   └── orders/
│   │       └── [id]/track.vue
│   │
│   └── pos/                             # Point of Sale
│       ├── index.vue                    # Session selector
│       ├── [session_id].vue             # Active POS session
│       └── close.vue                    # Session closing / Z-report
│
├── plugins/
│   ├── api.ts                           # Register $api globally
│   ├── auth.client.ts                   # Token restore on app init
│   ├── websocket.client.ts
│   ├── charts.client.ts                 # Register chart lib
│   └── i18n.ts
│
├── server/                              # Nuxt server routes (proxy/BFF if needed)
│   └── api/
│       └── proxy/[...].ts              # Optional: BFF proxy layer
│
├── stores/
│   ├── auth.ts
│   ├── ui.ts                           # Sidebar collapse, theme, breadcrumbs
│   ├── notifications.ts
│   ├── branch.ts                       # Active branch + user's assigned branches
│   ├── tenant.ts                       # Current tenant slug + metadata
│   ├── cart.ts                         # E-commerce cart
│   ├── pos.ts                          # POS session state
│   ├── inventory.ts
│   ├── accounting.ts
│   └── agents.ts
│
├── types/
│   ├── api.ts                          # Response/request type definitions
│   ├── user.ts
│   ├── inventory.ts
│   ├── accounting.ts
│   ├── sales.ts
│   └── ...
│
├── utils/
│   ├── format.ts                       # Currency, date, number formatters
│   ├── validation.ts                   # Zod schemas
│   ├── permissions.ts
│   └── constants.ts
│
└── package.json
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
    index.vue                   → Executive KPI dashboard (revenue, AR, stock, open orders)
    accounting.vue              → Accounting overview widget layout

  hr/
    index.vue                   → HR overview (headcount, attendance today)
    employees/
      index.vue                 → Employee list (table + filters)
      new.vue                   → Add employee wizard
      [id]/
        index.vue               → Employee profile (tabs: overview, attendance, leave, payroll, docs)
        edit.vue
    departments/index.vue
    attendance/
      index.vue                 → Daily attendance sheet
      calendar.vue              → Monthly view
    leaves/
      requests.vue              → Leave request list + approval queue
      allocations.vue
      calendar.vue              → Team leave calendar
    payroll/
      index.vue                 → Payroll periods list
      [period_id]/
        index.vue               → Period detail — run, review, approve, export
        payslip/[employee_id].vue
    expenses/index.vue
    training/index.vue
    performance/index.vue

  accounting/
    index.vue                   → Accounting dashboard (P&L sparklines, AR/AP summary)
    coa/index.vue               → Chart of accounts tree
    journal-entries/
      index.vue
      new.vue
      [id].vue
    invoices/
      index.vue                 → AR invoice list
      new.vue
      [id].vue                  → Invoice detail + payment history
    bills/
      index.vue                 → AP bill list
      [id].vue
    payments/index.vue
    budgets/
      index.vue
      [id].vue                  → Budget vs Actual by account/department/month
    tax-rates/index.vue
    currencies/index.vue
    reports/
      profit-loss.vue
      balance-sheet.vue
      cash-flow.vue
      trial-balance.vue
      ar-aging.vue
      ap-aging.vue

  inventory/
    index.vue                   → Stock overview (total value, low stock count, expiry)
    products/
      index.vue
      new.vue
      [id]/
        index.vue               → Product card (stock levels per warehouse, price history)
        edit.vue
        variants.vue
    categories/index.vue
    warehouses/
      index.vue
      [id]/index.vue            → Warehouse map / location tree
    stock-moves/index.vue
    adjustments/
      index.vue
      new.vue
      [id].vue
    lots/
      index.vue                 → Lot tracker with expiry column
      expiry.vue                → Dedicated expiry board (traffic-light)
    reorder-rules/index.vue
    alerts/index.vue
    valuation/index.vue

  procurement/
    index.vue
    requisitions/
      index.vue
      new.vue
      [id].vue
    rfqs/
      index.vue
      [id].vue                  → RFQ with supplier responses comparison view
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
    index.vue                   → Sales dashboard
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

  crm/
    index.vue                   → Pipeline kanban view
    leads/index.vue
    contacts/index.vue
    organizations/index.vue
    opportunities/
      index.vue
      [id].vue
    activities/index.vue
    campaigns/index.vue
    feedback/index.vue

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
    index.vue                   → Asset registry
    [id].vue                    → Asset detail (value, depreciation schedule, maintenance)
    depreciation.vue
    maintenance/index.vue
    disposals/index.vue

  projects/
    index.vue                   → Project list (card/table toggle)
    new.vue
    [id]/
      index.vue                 → Project board (kanban tasks)
      timeline.vue              → Gantt-style milestone view
      budget.vue
      team.vue
      timelogs.vue

  reports/
    index.vue                   → Report catalogue
    [report_key].vue            → Dynamic report viewer (filters, chart, table, export)
    scheduled.vue
    dashboards/
      index.vue
      [id].vue                  → Customisable dashboard builder (drag-drop widgets)

  agents/
    index.vue                   → Agent registry + status overview
    [id]/
      index.vue                 → Agent detail — tasks, actions, memory, alerts
      configure.vue
    tasks/index.vue             → All agent tasks (filterable by agent/status)
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
  index.vue                     → Order history + loyalty points dashboard
  orders/
    index.vue
    [id]/
      index.vue                 → Order detail
      track.vue                 → Live delivery tracking
  invoices/
    index.vue
    [id].vue                    → Downloadable invoice PDF
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
  index.vue                     → Supplier dashboard — my products' health at a glance
  products/
    index.vue                   → My product catalog (with stock levels, velocities)
    [id].vue                    → Product analytics for this supplier
  stock-alerts/index.vue        → Active stockout & low-stock alerts for my products
  expiry-reports/
    index.vue                   → Lots approaching / past expiry
    [product_id].vue
  purchase-orders/
    index.vue                   → POs sent to me (confirm, reject, view)
    [id].vue
  invoices/index.vue
  performance/
    index.vue                   → Sales velocity, revenue share, quality scores
    trends.vue
  profile.vue
  notifications.vue
```

### 11.4 E-Commerce Storefront
```
/store/
  index.vue                     → Home: hero, featured products, categories, promotions
  products/
    index.vue                   → Product listing (grid, filters, sort)
    [slug].vue                  → PDP: images, variants, reviews, add-to-cart
  categories/[slug].vue
  search.vue
  cart.vue
  checkout/
    index.vue                   → Address + shipping selection
    payment.vue                 → Payment gateway
    confirmation.vue            → Thank you + order number
  orders/[id]/track.vue
  auth/login.vue, register.vue
  account/ → redirects to /(client)/
```

---

## 12. UI Component Architecture

### 12.1 Design Tokens (Nuxt UI + Reka UI)
```ts
// nuxt.config.ts
ui: {
  primary: 'indigo',   // brand primary
  gray: 'zinc',
  // override per module (POS uses a dark theme)
}
```

### 12.2 Key Custom Components (Reka UI primitives)

| Component | Reka Primitive(s) Used | Purpose |
|-----------|----------------------|---------|
| `DataTable` | `Table`, `Separator` | Universal sortable, filterable, paginated table |
| `SearchSelect` | `Combobox` | Async remote search dropdown |
| `DateRangePicker` | `Popover` + `RangeCalendar` | Date range selection |
| `CommandPalette` | `Dialog` + `Combobox` | Global search (Cmd+K) |
| `ConfirmDialog` | `AlertDialog` | Destructive action confirmation |
| `Timeline` | custom + `Separator` | Activity/audit timeline |
| `Kanban` | `Draggable` (vue-draggable) + `ScrollArea` | CRM pipeline, project board |
| `GanttChart` | custom SVG + `ScrollArea` | Project milestone timeline |
| `POSNumpad` | `Dialog` + custom grid | POS quantity/price input |
| `BarcodeScanner` | `Dialog` + ZXing WASM | Camera barcode scanning |
| `WidgetGrid` | `Draggable` (vue-draggable-plus) | Dashboard builder layout |
| `PrintPreview` | `Dialog` + iframe | Print-ready document preview |
| `FileUpload` | Reka headless + dropzone | File attachment with preview |
| `RichTextEditor` | Tiptap + custom toolbar | Long-form text fields |
| `SignaturePad` | Canvas API + `Dialog` | Document signing |

### 12.3 Layout Structure (Staff Portal)

```vue
<!-- layouts/default.vue -->
<template>
  <div class="flex h-screen overflow-hidden bg-gray-950">
    <!-- Collapsible Sidebar -->
    <AppSidebar :collapsed="ui.sidebarCollapsed" />

    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- Top bar -->
      <AppTopbar />

      <!-- Page content area -->
      <main class="flex-1 overflow-y-auto p-6">
        <!-- Breadcrumbs -->
        <Breadcrumbs />
        <!-- Page slot -->
        <slot />
      </main>
    </div>

    <!-- Global notification drawer -->
    <NotificationDrawer />
    <!-- Command palette (Cmd+K) -->
    <CommandPalette />
    <!-- Global toast (Nuxt UI useToast) -->
  </div>
</template>
```

### 12.4 POS Layout (Full-screen, touch-optimized)
```vue
<!-- layouts/pos.vue — no default sidebar, tablet/kiosk optimized -->
<template>
  <div class="flex h-screen bg-gray-900 text-white select-none">
    <!-- Left: product grid / search -->
    <POSProductPanel class="flex-1" />
    <!-- Right: order summary + payment -->
    <POSOrderPanel class="w-96" />
    <!-- Modals: numpad, payment, receipt, session close -->
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
  const isStaff = computed(() => user.value?.user_type === 'staff')
  const isClient = computed(() => user.value?.user_type === 'client')
  const isSupplier = computed(() => user.value?.user_type === 'supplier')
  const isManager = computed(() => user.value?.is_manager === true)
  const hasGroup = (group: string) => user.value?.groups?.includes(group) ?? false
  const hasPerm = (perm: string) => user.value?.permissions?.includes(perm) ?? false

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
  const currentSession = ref<POSSession | null>(null)
  const currentOrder = ref<POSOrder | null>(null)
  const heldOrders = ref<HeldOrder[]>([])
  const products = ref<Product[]>([])          // loaded cache
  const isOffline = ref(false)
  const pendingSync = ref<POSOrder[]>([])       // offline queue

  // Offline-first: save to IndexedDB, sync on reconnect
  async function addToOrder(product, qty) { ... }
  async function processPayment(paymentLines) { ... }
  async function syncOfflineOrders() { ... }
  ...
})
```

### `stores/cart.ts` (E-Commerce)
```ts
export const useCartStore = defineStore('cart', {
  persist: true,   // localStorage persistence via pinia-plugin-persistedstate
  state: () => ({ items: [], couponCode: null, sessionId: uuid() }),
  ...
})
```

---

## 14. AI Agent Architecture

### 14.1 Agent Framework
- **LangChain** (Python) as the orchestration layer
- **OpenAI GPT-4o** (or configurable: Anthropic, Gemini, local Ollama)
- Each agent is a `LangChain ReAct Agent` with a defined set of tools
- Tools are Python functions that call the ERP's internal APIs / Django ORM directly
- Agents run as **Celery tasks** — triggered by schedule (beat), events (signals), or staff/API requests
- All agent actions are logged to `AgentAction` and `AgentTask` models
- Human-in-the-loop: any `AgentTask` with `requires_human_approval=True` pauses in `requires_approval` status until a staff member reviews it in the Agent Dashboard

### 14.2 Agent Tool Examples (InventoryMonitorAgent)
```python
@tool
def get_low_stock_products(threshold: int = 10) -> list:
    """Returns products with qty_on_hand <= threshold"""
    ...

@tool
def create_purchase_requisition(product_id: str, qty: int, reason: str) -> dict:
    """Drafts a PR; sets requires_human_approval=True"""
    ...

@tool
def notify_supplier(supplier_id: str, product_id: str, message: str) -> dict:
    """Sends a notification to the supplier portal"""
    ...
```

### 14.3 Agent → Staff Communication Flow
```
Agent runs task
  → determines action needed
  → if low-confidence / destructive: sets requires_human_approval=True
  → sends Notification to assigned staff (in-app + email)
  → staff opens agents/tasks page
  → reviews agent reasoning + proposed action
  → approves / rejects / modifies
  → agent executes (or discards)
```

### 14.4 Agent Dashboard (Nuxt)
```
/agents/
  ├── index.vue           → Active agents grid (status, last run, alert count)
  ├── [id]/
  │   ├── index.vue       → Agent profile: recent tasks, memory, configuration
  │   └── configure.vue   → Edit system prompt, model params, capabilities
  ├── tasks/index.vue     → All tasks with status filter; "requires approval" queue
  └── alerts/index.vue    → Agent-generated alerts (stockout, fraud, anomaly)
```

---

## 15. Development Phases / Roadmap

### Phase 0 — Foundation (Weeks 1–2)
- [ ] Django project scaffold + all apps created
- [ ] PostgreSQL + Redis + Celery setup
- [ ] Custom User model + JWT auth (all 4 user types)
- [ ] Nuxt project scaffold + Nuxt UI + Pinia
- [ ] Auth pages (login, register, password reset)
- [ ] Portal router middleware (routes by `user_type` post-login)
- [ ] Base layout components (sidebar, topbar, breadcrumbs)
- [ ] API response envelope + error handling setup
- [ ] Docker Compose for local development

### Phase 1 — Inventory & Procurement (Weeks 3–6)
- [ ] Django: Inventory models + full CRUD APIs
- [ ] Django: Procurement models + workflow APIs (PR → RFQ → PO → GRN)
- [ ] Nuxt: Product catalog management pages
- [ ] Nuxt: Warehouse & location management
- [ ] Nuxt: Stock lot tracking + expiry board
- [ ] Nuxt: Procurement workflow pages
- [ ] Reorder rule engine (Celery beat)
- [ ] InventoryMonitorAgent + ExpiryWatcherAgent (basic version)
- [ ] Supplier portal: basic product/stock views

### Phase 2 — Finance & HR (Weeks 7–11)
- [ ] Django: Finance models (COA, journal, AR, AP, budgets)
- [ ] Django: HR models (employees, attendance, leave, payroll)
- [ ] Auto-posting journal entries from GRNs, invoices, payments
- [ ] Nuxt: Finance pages (COA, journals, invoices, bills, payments)
- [ ] Nuxt: Budget vs actual report
- [ ] Nuxt: HR pages (employees, attendance, leave management)
- [ ] Payroll run engine (Celery task)
- [ ] PDF generation: invoices, payslips, bills
- [ ] FinanceAnalystAgent (basic AR/AP monitoring)

### Phase 3 — Sales, CRM & E-Commerce (Weeks 12–17)
- [ ] Django: Sales models (quotations, SO, deliveries, returns)
- [ ] Django: CRM models (leads, opportunities, contacts, campaigns)
- [ ] Django: E-Commerce models (store, cart, order, reviews, coupons)
- [ ] Payment gateway integration (Stripe + Paystack)
- [ ] Nuxt: Sales pipeline pages + CRM kanban
- [ ] Nuxt: E-Commerce storefront (full public-facing store)
- [ ] Nuxt: Client portal (order tracking, invoices, profile)
- [ ] Nuxt: Product detail page with reviews
- [ ] SalesAssistantAgent + ProcurementAgent

### Phase 4 — POS (Weeks 18–20)
- [ ] Django: POS models + session/order/payment APIs
- [ ] Nuxt: Full-screen POS interface (touch-optimized)
- [ ] Offline mode with IndexedDB + sync queue
- [ ] Barcode scanner integration
- [ ] Receipt printing (thermal + PDF)
- [ ] Session Z-report generation
- [ ] FraudDetectionAgent (POS anomaly monitoring)

### Phase 5 — Manufacturing, Logistics, Assets & Projects (Weeks 21–27)
- [ ] Django: Manufacturing models (BOM, WO, routing)
- [ ] Django: Logistics models (shipments, routes, vehicles)
- [ ] Django: Asset management + depreciation engine
- [ ] Django: Project management models
- [ ] Nuxt: Manufacturing pages (BOM editor, work order board)
- [ ] Nuxt: Shipment tracking view
- [ ] Nuxt: Asset registry + depreciation schedule
- [ ] Nuxt: Project kanban + Gantt timeline

### Phase 6 — Reporting, Dashboards & AI Agents (Weeks 28–32)
- [ ] Django: Report engine (all report types)
- [ ] Django: KPI snapshot Celery task
- [ ] Nuxt: Dynamic report viewer
- [ ] Nuxt: Dashboard builder (drag-drop widget layout)
- [ ] All AI agents fully built and tested
- [ ] Nuxt: Full agent dashboard + approval workflow
- [ ] Supplier portal: performance analytics + report subscriptions
- [ ] ReportBotAgent (natural language reports)

### Phase 7 — Notifications, Integrations & Polish (Weeks 33–36)
- [ ] Django Channels: WebSocket notifications
- [ ] Nuxt: Real-time notification bell + drawer
- [ ] Email/SMS notification system (all event types)
- [ ] Third-party integrations (shipping APIs, accounting exports)
- [ ] i18n (at least English + one additional language)
- [ ] Comprehensive audit log viewer
- [ ] Performance tuning, caching layer
- [ ] Documentation (OpenAPI, user manual)

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
  ├── /api/* + /ws/*  → Daphne (ASGI, handles HTTP + WebSocket)
  ├── /admin/*        → Daphne
  └── /*              → Nuxt SSR (Node.js server or static CDN)

Managed Services (recommended):
  - Database: Supabase PostgreSQL / RDS
  - Redis: Upstash / ElastiCache
  - Storage: AWS S3 / Cloudflare R2
  - Email: SendGrid / Mailgun
  - Monitoring: Sentry (errors) + Prometheus/Grafana (metrics)
```

---

## 17. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Auth | JWT with short expiry (15 min access, 7 day refresh rotation); HTTPS enforced |
| RBAC | `user_type` + Django `Group` memberships checked on every API endpoint via custom permission classes |
| Object-level permissions | Branch/department queryset filtering; `is_manager` flag for approval authority |
| SQL Injection | Django ORM only; raw queries forbidden unless absolutely necessary and parameterized |
| XSS | DRF JSON responses; Nuxt auto-escapes template bindings; CSP headers |
| CSRF | DRF exempt for JWT endpoints; Django CSRF for session-based admin |
| Sensitive data | Bank details, API keys stored encrypted (`django-encrypted-model-fields`) |
| Rate limiting | `django-ratelimit` on auth endpoints; `Nginx` rate limiting on API |
| Audit trail | `django-auditlog` on all models; immutable `AgentAction` logs |
| File uploads | Type validation, size limits, virus scan hook (ClamAV optional) |
| Supplier portal | Suppliers only see data scoped to their own products/POs — enforced in queryset filters |
| Client portal | Clients only see their own orders/invoices — `client = request.user.clientprofile` filters |
| Agent permissions | Agent JWT has explicit module permission list; can only call whitelisted endpoints |
| POS offline sync | Orders in offline queue signed with session token; replayed with idempotency keys |

---

*This document is a living specification. It will evolve as schema, requirements, and implementation decisions are finalized. Each section corresponds to a Django app and a Nuxt route group that will be built incrementally through the phases above.*
