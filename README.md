## ERP Scaffold

This workspace contains a Django REST backend and a Nuxt UI frontend, now prepared to run with PostgreSQL in Docker and `django-tenants` schema routing.

### Quick Start With Docker

From the repository root:

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Backend API: `http://127.0.0.1:8000/api/`
- Health check: `http://127.0.0.1:8000/api/health/`
- Django admin: `http://127.0.0.1:8000/admin/`
- Nuxt frontend: `http://127.0.0.1:3000/`
- PostgreSQL: `localhost:5432` using database `erp_tenant_db` by default

The backend container will:

1. Wait for PostgreSQL.
2. Run shared tenant migrations.
3. Bootstrap a default tenant from `.env`.
4. Start the Django development server.

### Default Tenant

The default bootstrap tenant is controlled by these environment variables:

- `DEFAULT_TENANT_NAME`
- `DEFAULT_TENANT_SCHEMA`
- `DEFAULT_TENANT_DOMAINS`
- `DEFAULT_TENANT_TRADE_COUNTRY`
- `DEFAULT_TENANT_CURRENCY`

By default the project boots a `public` tenant that responds on `localhost` and `127.0.0.1`.

### API Surface

Auth endpoints:

- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/logout-all/`
- `GET /api/auth/me/`

Company endpoints:

- `GET /api/company/companies/`
- `GET /api/company/industries/`
- `GET /api/company/payment-classes/`
- `GET /api/company/business-types/`

Contact endpoints:

- `GET /api/contact/countries/`
- `GET /api/contact/states/`
- `GET /api/contact/cities/`
- `GET /api/contact/address-types/`
- `GET /api/contact/phone-types/`
- `GET /api/contact/email-types/`
- `GET /api/contact/website-types/`
- `GET /api/contact/phones/`
- `GET /api/contact/addresses/`
- `GET /api/contact/emails/`
- `GET /api/contact/websites/`
- `GET /api/contact/contacts/`

### Local Non-Docker Backend

If you want to run Django directly against PostgreSQL on your machine:

```bash
cd backend
../.venv/bin/python manage.py migrate_schemas --shared
../.venv/bin/python manage.py bootstrap_tenant
../.venv/bin/python manage.py runserver
```

### Frontend Configuration

The frontend uses Nuxt UI v4 and reads `NUXT_PUBLIC_API_BASE`, defaulting to `http://127.0.0.1:8000/api`.
