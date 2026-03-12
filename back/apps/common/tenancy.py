from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q


@dataclass(frozen=True)
class TenantContext:
    company: object | None = None
    domain: object | None = None
    host: str | None = None
    schema_name: str = "public"
    source: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.company is not None


def _company_model():
    from apps.company.models import Company

    return Company


def _domain_model():
    from apps.company.models import Domain

    return Domain


def _model_has_field(model_class, field_name: str) -> bool:
    try:
        model_class._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False


def _field_allows_null(model_class, field_name: str) -> bool:
    try:
        return bool(model_class._meta.get_field(field_name).null)
    except FieldDoesNotExist:
        return False


def _domain_relation_name() -> str | None:
    domain_model = _domain_model()
    for field_name in ("company", "tenant"):
        if _model_has_field(domain_model, field_name):
            return field_name
    return None


def _query_value(request, *names: str):
    if request is None:
        return None

    query = getattr(request, "GET", None)
    if not hasattr(query, "get"):
        return None

    for name in names:
        value = query.get(name)
        if value:
            return value
    return None


def normalize_host(host: str | None) -> str:
    if not host:
        return ""

    normalized = host.strip().lower()
    if "://" in normalized:
        normalized = normalized.split("://", 1)[1]
    normalized = normalized.split("/", 1)[0]
    normalized = normalized.split(":", 1)[0]
    return normalized.rstrip(".")


def get_request_host(request) -> str:
    if request is None:
        return ""

    try:
        return normalize_host(request.get_host())
    except Exception:
        return ""


def resolve_company_from_identifier(*, company_id=None, slug=None, require_active: bool = True):
    Company = _company_model()
    queryset = Company.objects.all()

    if company_id:
        queryset = queryset.filter(pk=company_id)
    elif slug:
        queryset = queryset.filter(slug__iexact=slug)
    else:
        return None

    company = queryset.first()
    if company is None:
        return None
    if require_active and hasattr(company, "is_active") and not company.is_active:
        return None
    return company


def request_company_identifier(request) -> tuple[str | None, str | None]:
    if request is None:
        return None, None

    company_id = (
        request.headers.get("X-Company-Id")
        or request.headers.get("X-Tenant-Id")
        or _query_value(request, "company_id", "tenant_id")
    )
    slug = (
        request.headers.get("X-Company-Slug")
        or request.headers.get("X-Tenant-Slug")
        or request.headers.get("X-Tenant")
        or _query_value(request, "company_slug", "tenant", "company")
    )

    return company_id, slug


def get_domain_company(domain):
    relation_name = _domain_relation_name()
    if relation_name is None or domain is None:
        return None
    return getattr(domain, relation_name, None)


def resolve_domain(host: str | None):
    normalized_host = normalize_host(host)
    if not normalized_host:
        return None

    domain_model = _domain_model()
    queryset = domain_model.objects.all()
    relation_name = _domain_relation_name()
    if relation_name is not None:
        queryset = queryset.select_related(relation_name)

    return queryset.filter(domain__iexact=normalized_host).first()


def resolve_company(host: str | None, *, require_active: bool = True):
    domain = resolve_domain(host)
    company = get_domain_company(domain)

    if company is None:
        return None
    if require_active and hasattr(company, "is_active") and not company.is_active:
        return None
    return company


def build_tenant_context(
    request,
    *,
    fallback_to_user: bool = True,
    fallback_to_host: bool = True,
) -> TenantContext:
    cached_context = getattr(request, "tenant_context", None)
    if isinstance(cached_context, TenantContext):
        return cached_context

    public_schema = getattr(settings, "PUBLIC_SCHEMA_NAME", "public")
    host = get_request_host(request)

    company_id, company_slug = request_company_identifier(request)
    explicit_company = resolve_company_from_identifier(company_id=company_id, slug=company_slug)
    if explicit_company is not None:
        return TenantContext(
            company=explicit_company,
            domain=None,
            host=host,
            schema_name=getattr(explicit_company, "schema_name", public_schema) or public_schema,
            source="request.identifier",
        )

    request_company = getattr(request, "company", None)
    if request_company is not None:
        return TenantContext(
            company=request_company,
            domain=getattr(request, "tenant_domain", None),
            host=host,
            schema_name=getattr(request_company, "schema_name", public_schema) or public_schema,
            source="request.company",
        )

    request_tenant = getattr(request, "tenant", None)
    if isinstance(request_tenant, _company_model()):
        return TenantContext(
            company=request_tenant,
            domain=getattr(request, "tenant_domain", None),
            host=host,
            schema_name=getattr(request_tenant, "schema_name", public_schema) or public_schema,
            source="request.tenant",
        )

    if fallback_to_host:
        domain = resolve_domain(host)
        company = get_domain_company(domain)
        if company is not None:
            return TenantContext(
                company=company,
                domain=domain,
                host=host,
                schema_name=getattr(company, "schema_name", public_schema) or public_schema,
                source="domain",
            )

    user = getattr(request, "user", None)
    if fallback_to_user and getattr(user, "is_authenticated", False):
        company = getattr(user, "company", None)
        if company is not None:
            return TenantContext(
                company=company,
                domain=None,
                host=host,
                schema_name=getattr(company, "schema_name", public_schema) or public_schema,
                source="user.company",
            )

    return TenantContext(host=host, schema_name=public_schema)


def attach_tenant_context(request, **kwargs) -> TenantContext:
    context = build_tenant_context(request, **kwargs)
    setattr(request, "tenant_context", context)
    setattr(request, "company", context.company)
    if getattr(request, "tenant", None) is None and context.company is not None:
        setattr(request, "tenant", context.company)
    if context.domain is not None:
        setattr(request, "tenant_domain", context.domain)
    return context


def current_company(request, **kwargs):
    return build_tenant_context(request, **kwargs).company


def current_schema_name(request, **kwargs) -> str:
    return build_tenant_context(request, **kwargs).schema_name


def scope_queryset(queryset, *, company=None, request=None, field_name: str = "company", include_global: bool = False):
    model_class = queryset.model
    if not _model_has_field(model_class, field_name):
        return queryset

    company = company or current_company(request)
    if company is None:
        return queryset

    company_filter = Q(**{field_name: company})
    if include_global and _field_allows_null(model_class, field_name):
        return queryset.filter(company_filter | Q(**{f"{field_name}__isnull": True}))

    return queryset.filter(company_filter)


def assign_company(instance, *, company=None, request=None, field_name: str = "company", overwrite: bool = False):
    model_class = instance.__class__
    if not _model_has_field(model_class, field_name):
        return instance

    if getattr(instance, field_name, None) is not None and not overwrite:
        return instance

    company = company or current_company(request)
    if company is not None:
        setattr(instance, field_name, company)
    return instance


def assign_company_and_save(instance, *, company=None, request=None, field_name: str = "company", overwrite: bool = False):
    previous_company = getattr(instance, field_name, None) if _model_has_field(instance.__class__, field_name) else None
    assign_company(instance, company=company, request=request, field_name=field_name, overwrite=overwrite)

    next_company = getattr(instance, field_name, None) if _model_has_field(instance.__class__, field_name) else None
    if next_company is not None and next_company != previous_company:
        instance.save(update_fields=[field_name])
    return instance