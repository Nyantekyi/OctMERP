"""
Tenancy models stub.

The ERP system uses `apps.company.Company` as the django-tenants tenant
model (`TENANT_MODEL = "company.Company"`).  All tenant / domain logic
lives in `apps/company/models.py`.  This module is kept only for
backward-compat imports; nothing here should be used directly.
"""

