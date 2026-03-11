# ERP System

A full-featured, **multi-tenant** Enterprise Resource Planning (ERP) system built with **Django 5 + Django REST Framework** on the backend and **Nuxt 3 + Nuxt UI / Reka UI** on the frontend.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Architecture](#3-architecture)
4. [Multi-Tenancy](#4-multi-tenancy)
5. [User Types & Permissions](#5-user-types--permissions)
6. [Modules](#6-modules)
7. [Project Structure](#7-project-structure)
8. [API Design](#8-api-design)
9. [Frontend Portals](#9-frontend-portals)
10. [AI Agents](#10-ai-agents)
11. [Getting Started](#11-getting-started)
12. [Security](#12-security)

---

## 1. Project Overview

A production-grade ERP covering accounting, HR & payroll, inventory, procurement, sales, manufacturing, logistics, e-commerce, point-of-sale, CRM, fixed asset management, project management, and AI-driven automation — all within a single multi-tenant platform.

**Core design goals:**

- **Multi-tenancy** via `django-tenants` — each `Company` is a fully isolated PostgreSQL schema
- Organisational hierarchy: **Company → Department → Branch** — all users, stock, transactions, and reports are scoped to this structure
- Unified REST API consumed by four frontend surfaces: Staff ERP portal, Client portal, Supplier portal, and Agent dashboard
- Real-time updates (WebSockets via Django Channels) for live dashboards, POS sessions, and agent activity
- Django built-in `Group` + `Permission` RBAC; `is_manager` flag on `StaffProfile` for branch-level approval authority
- Autonomous AI agents that monitor, alert, draft, and execute on behalf of staff
- Supplier visibility portal: product performance, stockout alerts, expiry warnings, demand forecasting
- Client-facing e-commerce storefront and order tracking
- Fully offline-capable POS with sync-on-reconnect

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| **Backend framework** | Django 5.x + Django REST Framework |
| **Database** | PostgreSQL (per-tenant schema via `django-tenants`) |
| **Auth** | `djangorestframework-simplejwt` (JWT with refresh rotation) |
| **Async tasks** | Celery + Redis broker |
| **Real-time** | Django Channels + Redis channel layer (WebSocket) |
| **Cache** | Redis (`django-redis`) |
| **File storage** | `django-storages` + S3 / MinIO |
| **Email** | `django-anymail` (SendGrid / Mailgun) |
| **PDF generation** | WeasyPrint / ReportLab |
| **Audit log** | `django-auditlog` |
| **Search** | `django-elasticsearch-dsl` or PostgreSQL full-text |
| **AI agents** | LangChain + OpenAI |
| **Frontend framework** | Nuxt 3 |
| **UI library** | Nuxt UI v3 + Reka UI v2 |
| **State management** | Pinia |
| **Charts** | Apache ECharts (via `vue-echarts`) |
| **Rich text** | Tiptap |
| **Validation** | Zod |
| **i18n** | `@nuxtjs/i18n` |
| **Gateway** | Nginx (routes `/api/v1/*` → Django, `/ws/*` → Channels) |

---

## 3. Architecture

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
┌─────────────────────────────────▼───────────────────────────────┐
│                       API GATEWAY (Nginx)                        │
│            /api/v1/*  →  Django REST Framework                   │
│            /ws/*      →  Django Channels (WebSocket)             │
└──────────────────┬──────────────────┬───────────────────────────┘
                   │                  │
       ┌───────────▼──┐    ┌──────────▼──────────┐    ┌──────────────┐
       │ Django / DRF │    │  Celery Workers       │    │ AI Agent     │
       │ (Gunicorn)   │    │  (email, reports,     │    │ Runtime      │
       └───────┬──────┘    │   scheduled jobs)     │    │ (LangChain)  │
               │           └──────────┬────────────┘    └──────┬───────┘
               └──────────────────────┼───────────────────────┘
                                      │
         ┌────────────────────────────┼───────────────────┐
         ▼                            ▼                   ▼
  ┌─────────────┐           ┌──────────────┐    ┌──────────────┐
  │ PostgreSQL  │           │    Redis      │    │  S3 / MinIO  │
  │ (Per-tenant │           │ (Cache, Queue,│    │ (File Store) │
  │  schemas)   │           │  WebSocket)   │    │              │
  └─────────────┘           └──────────────┘    └──────────────┘
```

---

## 4. Multi-Tenancy

Each `Company` maps to a dedicated PostgreSQL schema managed by `django-tenants`.

```
public schema:
  └── Company (TenantMixin), Domain (DomainMixin)

Per-tenant schema (isolated per Company):
  └── All users, profiles, inventory, transactions, documents, etc.
```

Company is identified by subdomain or custom domain. The tenant schema is automatically created when a new `Company` is registered. All tenant-scoped models extend the `TenantAwareModel` abstract base which adds `created_at`, `updated_at`, and `created_by` audit fields.

---

## 5. User Types & Permissions

### User Types

| Type | Description | Portal |
|---|---|---|
| **Staff** | Internal employees (regular, manager, admin, superuser) | Staff ERP Portal |
| **Client** | Customers placing orders | Client Portal + E-Commerce |
| **Supplier** | Vendors, wholesalers, distributors | Supplier Portal |
| **Agent** | Autonomous AI entities | Agent Dashboard |

### RBAC via Django Groups

Permissions are managed entirely through Django's built-in `Group` and `Permission` system. Predefined groups seeded on tenant creation:

| Group | Typical Permissions |
|---|---|
| Accountants | `accounting.*` full, all others read |
| HR Officers | `hr.*` full, `party.*` read |
| Inventory Officers | `inventory.*` + `procurement.*` full |
| Sales Representatives | `sales.*` + `crm.*` + `pos.*` full |
| Warehouse Staff | `inventory.*` update, `logistics.*` update |
| Procurement Officers | `procurement.*` full |
| Project Managers | `projects.*` full |
| Manufacturing Staff | `manufacturing.*` full |
| Viewers | Read-only across all assigned modules |
| IT Support | System logs, integrations, audit log |

### Manager Elevation

`StaffProfile.is_manager = True` grants approval authority **within the user's assigned branches** for leave requests, purchase requisitions, payroll periods, and quotations. It augments — not replaces — Group membership.

### JWT Claims

```json
{
  "user_id": "uuid",
  "email": "user@company.com",
  "user_type": "staff",
  "is_manager": true,
  "groups": ["Accountants"],
  "permissions": ["accounting.add_invoice"],
  "tenant_slug": "acme-corp",
  "branch_ids": ["uuid1", "uuid2"]
}
```

---

## 6. Modules

### `apps/party` — Users, Profiles & Organisation
Users, StaffProfile, ClientProfile, SupplierProfile, AgentProfile, Company (TenantMixin), Domain, Department, Branch, ContactPoint (generic), Address (generic).

### `apps/hr` — Human Resources & Payroll
Employee records, job titles, attendance tracking, leave types & requests, leave allocations, payroll periods & entries, payslips, expense claims, training records, performance reviews.

### `apps/accounting` — Accounting, AR, AP & Budgeting
Fiscal years, Chart of Accounts, journal entries & lines, multi-currency with exchange rates, AR invoices, AP bills, payments, tax rates & groups, budget plans, budget lines with actual vs. budgeted tracking. Reports: P&L, Balance Sheet, Cash Flow, Trial Balance, AR/AP Aging.

The accounting engine is backed by a double-entry `Transaction` model validated against a `Charts_of_account` hierarchy (Assets starting at `10100000`, Expenses at `20100000`, Liabilities at `30100000`, Revenue at `40100000`, Capital/Equity at `50100000`). All debits and credits are verified to balance before posting.

### `apps/inventory` — Inventory & Warehouse
Products, product variants, images, categories, brands, units of measure, warehouses, warehouse locations (aisle/rack/bin), stock lots with expiry tracking, every stock movement recorded (`StockMove`), FIFO/AVCO/standard cost valuation, inventory adjustments, scrap tracking, reorder rules, and system-generated stock alerts (stockout, low stock, expiry warning).

### `apps/procurement` — Purchasing & Vendor Management
Purchase requisitions, request-for-quotations (RFQ) with multi-supplier comparison, RFQ responses, purchase orders (PO), goods receipt notes (GRN), lot creation on receipt, supplier evaluations, and vendor contracts.

### `apps/sales` — Sales Orders & Quotations
Price lists, discount/promotion rules, quotations, sales orders, deliveries, returns/RMA, and sales commissions.

### `apps/crm` — Customer Relationship Management
Leads, contacts, organisations, opportunities (with pipeline stages), activities (calls, meetings, tasks), and marketing campaigns with conversion tracking.

### `apps/ecommerce` — E-Commerce Storefront
Store configuration, product listings (with SEO slugs and rich HTML), guest & authenticated shopping carts, wishlists, orders (mapped to `SalesOrder`), order tracking, product reviews, coupons & vouchers, shipping zones & methods, and payment gateway configuration (Stripe, Paystack, Flutterwave, PayPal).

### `apps/pos` — Point of Sale
POS configurations, cashier sessions with opening/closing balance reconciliation, orders (walk-in or account customers), split payment lines, cash movements, held (parked) orders, and offline-capable sync.

### `apps/manufacturing` — Manufacturing & MRP
Bills of Materials (BOM) with versioning, routing operations, work centres, work orders, component consumption tracking, production lots, by-products, and MRP run planning.

### `apps/logistics` — Shipping & Delivery
Carriers, shipments with timeline events, delivery routes for owned fleet, vehicle management, route stops with ETA tracking, and customs clearance records.

### `apps/assets` — Fixed Asset Management
Asset categories with configurable depreciation methods (straight-line, declining balance, units-of-production), fixed assets, automated depreciation schedules with journal entry posting, maintenance records, and disposal with gain/loss calculation.

### `apps/projects` — Project Management
Projects with budget and progress tracking, milestones, tasks (with subtasks), time logs (billable/non-billable), project expenses, and issue/bug tracking.

### `apps/reporting` — Reports, Dashboards & KPIs
Saved & scheduled reports, KPI snapshots persisted for dashboards, customisable dashboards with configurable widgets (charts, tables, metrics, maps). Full report catalogue spanning finance, inventory, procurement, sales, HR, POS, manufacturing, projects, and supplier portal analytics.

### `apps/notifications` — Notification Centre
Template-based notifications delivered via email, SMS, in-app, and push. User notification preferences with quiet hours. Key events include: low stock, expiry warnings, invoice overdue, leave status, payroll processed, agent actions requiring approval.

### `apps/agents` — AI Agent Core
Agent definitions with LLM config and tool manifests, agent tasks with human-in-the-loop approval support, granular action logging, and persistent agent memory.

**Built-in agents:**

| Agent | Responsibility |
|---|---|
| `InventoryMonitorAgent` | Watches stock every 15 min, fires alerts, drafts purchase requisitions |
| `ExpiryWatcherAgent` | Daily expiry scans, supplier notifications, markdown suggestions |
| `FinanceAnalystAgent` | AR/AP reconciliation, overdue flags, weekly P&L summary |
| `SalesAssistantAgent` | Lead qualification, upsell suggestions, quotation drafting |
| `ProcurementAgent` | Auto-sends RFQs, compares responses, drafts POs |
| `ReportBotAgent` | Natural language report generation and scheduling |
| `FraudDetectionAgent` | Monitors POS/e-commerce for unusual patterns |

---

## 7. Project Structure

### Backend (`backend/`)

```
backend/
├── config/
│   └── settings/         # base, development, production, testing
├── apps/
│   ├── party/            # Users, profiles, company, org structure
│   ├── hr/               # Human resources & payroll
│   ├── accounting/       # GL, AR, AP, budgeting
│   ├── inventory/        # Stock, warehouses, lots, alerts
│   ├── procurement/      # POs, RFQs, GRNs, vendors
│   ├── sales/            # Sales orders, quotations
│   ├── ecommerce/        # Storefront, cart, orders
│   ├── pos/              # Point of sale sessions
│   ├── manufacturing/    # BOM, work orders, MRP
│   ├── logistics/        # Shipments, delivery routes
│   ├── assets/           # Fixed assets, depreciation
│   ├── projects/         # Project management, tasks
│   ├── crm/              # Leads, opportunities, campaigns
│   ├── reporting/        # Reports, dashboards, KPIs
│   ├── notifications/    # Notification centre
│   ├── integrations/     # Third-party APIs
│   └── agents/           # AI agent runtime
└── common/
    ├── models.py         # TenantAwareModel abstract base
    ├── permissions.py    # DRF permission classes
    └── utils/            # PDF, email, currency helpers
```

### Frontend (`frontend/`)

```
frontend/
├── layouts/              # Staff ERP, client, supplier, agent, storefront, POS, print
├── pages/
│   ├── auth/             # Login, register, password reset
│   ├── (staff)/          # Full staff ERP portal
│   ├── (client)/         # Client portal
│   ├── (supplier)/       # Supplier portal
│   ├── store/            # Public e-commerce storefront
│   └── pos/              # Point of sale
├── components/
│   ├── ui/               # Reusable UI components (DataTable, Charts, Form, etc.)
│   ├── modules/          # Feature-specific components per app
│   └── shared/           # NotificationBell, BranchSelector, TenantSwitcher
├── composables/          # useApi, useAuth, usePermissions, useWebSocket, etc.
├── stores/               # Pinia stores (auth, branch, cart, POS, inventory, etc.)
├── middleware/           # Route guards (auth, user type, permission, manager)
└── types/                # TypeScript type definitions
```

---

## 8. API Design

All endpoints are namespaced under `/api/v1/` and follow a consistent response envelope:

```json
{
  "success": true,
  "data": { "..." },
  "meta": { "page": 1, "page_size": 20, "count": 150, "total_pages": 8 },
  "errors": null
}
```

### Conventions

| Pattern | Meaning |
|---|---|
| `GET /resources/` | Paginated, filterable, searchable list |
| `POST /resources/` | Create |
| `GET /resources/{id}/` | Detail |
| `PATCH /resources/{id}/` | Partial update |
| `DELETE /resources/{id}/` | Soft delete (`is_active=False`) |
| `POST /resources/{id}/{action}/` | State transitions (e.g. `/confirm/`, `/approve/`, `/post/`) |

Query parameters: `?page=1&page_size=20`, `?ordering=-created_at`, `?search=keyword`, `?status=active`, `?date_after=2025-01-01`.

OpenAPI schema: `/api/v1/schema/` | Interactive docs: `/api/v1/docs/`

WebSocket channels:
- `ws://host/ws/notifications/`
- `ws://host/ws/pos/{session_id}/`
- `ws://host/ws/agents/`

---

## 9. Frontend Portals

| Portal | URL Pattern | Audience |
|---|---|---|
| Staff ERP | `/(staff)/` | Internal employees |
| Client Portal | `/(client)/` | Customers |
| Supplier Portal | `/(supplier)/` | Vendors & distributors |
| E-Commerce Storefront | `/store/` | Public |
| Point of Sale | `/pos/` | Cashier (full-screen) |
| Agent Dashboard | Via staff settings | Supervised AI agents |

Route middleware routes each `user_type` to the correct portal and layout after JWT login. Permission-gated pages check Django group memberships and the `is_manager` flag via `usePermissions()`.

---

## 10. AI Agents

Agents are defined in `apps/agents` with full lifecycle management:

- **Human-in-the-loop**: tasks that require approval are held in `requires_approval` state until a staff member approves or rejects them
- **Audit trail**: every tool call is logged in `AgentAction` with input, output, and duration
- **Persistent memory**: `AgentMemory` stores per-agent key/value context across runs
- **Alerts**: `AgentAlert` routes to the notification system with configurable severity levels

Agents are scheduled via Celery Beat and can also be triggered manually from the Staff ERP Agent Dashboard.

---

## 11. Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

```bash
# Clone the repo
git clone <repo-url>
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements/development.txt

# Configure environment variables
cp .env.example .env
# Edit .env: DATABASE_URL, REDIS_URL, SECRET_KEY, etc.

# Run migrations (public schema first, then tenant schemas)
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

# Create the first Company (public tenant) and superuser
python manage.py create_tenant
python manage.py createsuperuser

# Seed predefined groups and permissions
python manage.py seed_groups

# Start the development server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A config worker -l info

# Start Celery Beat scheduler (separate terminal)
celery -A config beat -l info
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit .env: NUXT_PUBLIC_API_BASE_URL, etc.

# Start development server
npm run dev
```

### Docker (Recommended)

```bash
docker compose up --build
```

---

## 12. Security

- **Tenant isolation**: PostgreSQL schema routing enforces hard tenant boundaries at the database level
- **JWT authentication**: short-lived access tokens with refresh rotation; claims include tenant slug and branch IDs
- **RBAC**: all API views enforce DRF permission classes (`IsStaff`, `IsAdminOrSuperuser`, `IsManagerOfBranch`) in addition to Django model-level permissions
- **Audit logging**: `django-auditlog` tracks all model changes with user, timestamp, and diff
- **Input validation**: all API input validated via DRF serializers; Zod schemas on the frontend
- **Encrypted fields**: supplier bank details stored with application-layer encryption
- **CORS**: restricted to known frontend origins via `django-cors-headers`
- **Payment data**: payment gateway credentials stored encrypted in `PaymentGateway.config`
- **IP logging**: e-commerce orders record `ip_address` for fraud investigation
- **Fraud detection**: `FraudDetectionAgent` monitors POS and e-commerce for anomalous patterns
- **HTTPS enforced** in production via Nginx; HSTS enabled
