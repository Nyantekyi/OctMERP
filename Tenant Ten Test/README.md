# Django Tenants + DRF + Nuxt Demo

This workspace demonstrates a multi-tenant ERP-style setup with:

- `backend/`: Django + `django-tenants` + Django REST Framework
- `frontend/`: Nuxt app that calls tenant APIs and only uses enabled feature routes

## Architecture Summary

- Main tenant model: `Company` (`backend/apps/customers/models.py`)
- Company type controls specialized modules:
  - `service` -> `crm`
  - `manufacturing` -> `manufacturing`
  - `hybrid` -> both
- Common module for all tenants: `accounting`
- Shared/global data across companies: `core_shared` app (`GlobalAnnouncement`)

Tenant-scoped apps:

- `accounting` (for all companies)
- `crm` (service/hybrid companies)
- `manufacturing` (manufacturing/hybrid companies)

Shared apps:

- `customers` (tenant metadata and domains)
- `core_shared` (global records)

## 1. Start Postgres

```bash
docker compose up -d postgres
```

## 2. Run Django Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

### Domain Notes

`django-tenants` resolves tenants by domain. For local testing, map these hosts to `127.0.0.1`:

- `alpha.localhost`
- `beta.localhost`
- `gamma.localhost`

Then use tenant domain URLs, for example:

- `http://alpha.localhost:8000/api/tenant/features/`
- `http://beta.localhost:8000/api/accounting/entries/`

Public/shared endpoints (host can be any configured public host):

- `http://localhost:8000/api/public/companies/`
- `http://localhost:8000/api/public/shared-announcements/`

## 3. Run Nuxt Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

If you want the frontend to point at a specific tenant domain, set:

```bash
NUXT_PUBLIC_API_BASE_URL=http://alpha.localhost:8000
```

## API Behavior

1. Nuxt loads shared announcements from public routes.
2. Nuxt requests `/api/tenant/features/` from a tenant domain.
3. Based on returned modules, Nuxt only calls matching app routes:
   - `accounting` -> `/api/accounting/entries/`
   - `crm` -> `/api/crm/leads/`
   - `manufacturing` -> `/api/manufacturing/work-orders/`

## Important Files

- `backend/config/settings.py`
- `backend/config/public_urls.py`
- `backend/config/tenant_urls.py`
- `backend/apps/customers/models.py`
- `backend/apps/customers/permissions.py`
- `backend/apps/customers/management/commands/seed_demo.py`
- `frontend/composables/useTenantApi.ts`
- `frontend/pages/index.vue`
