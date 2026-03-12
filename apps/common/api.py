from django.conf import settings
from django.db import connection, models
from django.db.models import Q
from importlib import import_module
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from apps.common.pagination import StandardResultsPagination

try:
    # Optional external tenancy helpers (kept for backward compatibility).
    _tenancy = import_module("apps.common.tenancy")
    _assign_company_and_save = getattr(_tenancy, "assign_company_and_save", None)
    _scope_queryset = getattr(_tenancy, "scope_queryset", None)
except Exception:  # pragma: no cover - optional module may not exist in schema-only setups
    _assign_company_and_save = None
    _scope_queryset = None


def _model_has_field(model_or_instance, field_name):
    if not field_name:
        return False

    model_cls = model_or_instance if isinstance(model_or_instance, type) else model_or_instance.__class__
    try:
        model_cls._meta.get_field(field_name)
        return True
    except Exception:
        return False


def _get_request_tenant(request):
    if request is None:
        return None
    return getattr(request, "tenant", None)


def _get_current_schema_name():
    return getattr(connection, "schema_name", None)


def _get_public_schema_name():
    return getattr(settings, "PUBLIC_SCHEMA_NAME", "public")


def _is_public_schema(schema_name):
    return schema_name in {None, "", _get_public_schema_name()}


def _is_tenant_aware_model(model_class):
    return any(base.__name__ == "TenantAwareModel" for base in model_class.__mro__)


def _should_require_schema_tenant(model_class, tenant_scoped):
    return bool(tenant_scoped or _is_tenant_aware_model(model_class))


def ensure_tenant_route(model_class, request, tenant_scoped=False, allow_public_schema=False):
    tenant = _get_request_tenant(request)
    schema_name = _get_current_schema_name()
    requires_tenant = _should_require_schema_tenant(model_class, tenant_scoped)

    if tenant is not None:
        tenant_schema_name = getattr(tenant, "schema_name", None)
        if tenant_schema_name and schema_name and tenant_schema_name != schema_name:
            raise PermissionDenied("Tenant schema mismatch for this request.")
        if hasattr(tenant, "is_active") and not tenant.is_active:
            raise PermissionDenied("The requested tenant is inactive.")

    if not requires_tenant:
        return tenant

    if tenant is None:
        raise NotFound("Tenant context was not resolved for this request.")

    if _is_public_schema(schema_name) and not allow_public_schema:
        raise NotFound("Tenant-scoped routes are not available on the public schema.")

    return tenant


def _get_action_permission_codename(action):
    """Map DRF actions to Django model permission codenames."""
    action_to_codename = {
        "list": "view",
        "retrieve": "view",
        "create": "add",
        "update": "change",
        "partial_update": "change",
        "destroy": "delete",
    }
    return action_to_codename.get(action)


def _get_required_model_permission(model_class, action):
    codename_prefix = _get_action_permission_codename(action)
    if codename_prefix is None:
        return None

    app_label = model_class._meta.app_label
    model_name = model_class._meta.model_name
    return f"{app_label}.{codename_prefix}_{model_name}"


def scope_queryset(queryset, request, field_name="company", include_global=False):
    if _scope_queryset is not None:
        return _scope_queryset(queryset, request=request, field_name=field_name, include_global=include_global)

    # In django-tenants schema mode, tenant-scoped models are already isolated by schema.
    # Filter only when an explicit tenant/company FK exists on the model.
    if not _model_has_field(queryset.model, field_name):
        return queryset

    tenant = _get_request_tenant(request)
    if tenant is None:
        return queryset.none()

    if include_global:
        return queryset.filter(Q(**{field_name: tenant}) | Q(**{f"{field_name}__isnull": True}))
    return queryset.filter(**{field_name: tenant})


def assign_company_and_save(instance, request, field_name="company"):
    if _assign_company_and_save is not None:
        return _assign_company_and_save(instance, request=request, field_name=field_name)

    if not _model_has_field(instance, field_name):
        return instance

    tenant = _get_request_tenant(request)
    if tenant is None:
        return instance

    if getattr(instance, field_name, None) is None:
        setattr(instance, field_name, tenant)
        instance.save(update_fields=[field_name])

    return instance


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "created_by")


def build_model_serializer(
    model_class,
    fields=None,
    read_only_fields=None,
    nested_serializers=None,
    create_handler=None,
    update_handler=None,
    validate_handler=None,
    to_internal_value_handler=None,
    to_representation_handler=None,
    method_overrides=None,
):
    serializer_fields = fields
    meta_read_only = ("id", "created_at", "updated_at", "created_by")
    if read_only_fields:
        meta_read_only = meta_read_only + tuple(read_only_fields)

    normalized_nested = {}
    if nested_serializers:
        for field_name, config in nested_serializers.items():
            if isinstance(config, dict):
                serializer_cls = config.get("serializer")
                if serializer_cls is None:
                    raise ValueError(f"nested_serializers['{field_name}'] must include a 'serializer' key")
                normalized_nested[field_name] = config
            else:
                normalized_nested[field_name] = {"serializer": config}

    class AutoSerializer(BaseModelSerializer):
        class Meta(BaseModelSerializer.Meta):
            model = model_class
            fields = serializer_fields or BaseModelSerializer.Meta.fields
            read_only_fields = meta_read_only

        def _update_object_with_setattr(self, instance, attrs):
            for attr, value in attrs.items():
                setattr(instance, attr, value)
            instance.save()
            return instance

        def _save_nested_item(self, field_name, manager_or_instance, item_data):
            if isinstance(manager_or_instance, models.Model):
                return self._update_object_with_setattr(manager_or_instance, item_data)

            related_model = manager_or_instance.model
            item_id = item_data.get("id") or item_data.get("pk")
            if item_id:
                existing = related_model.objects.filter(pk=item_id).first()
                if existing:
                    payload = dict(item_data)
                    payload.pop("id", None)
                    payload.pop("pk", None)
                    return self._update_object_with_setattr(existing, payload)

            return related_model.objects.create(**item_data)

        def _apply_nested_writes(self, instance, nested_payload, is_update=False):
            if not nested_payload:
                return

            for field_name, config in nested_payload.items():
                source_name = config["source"]
                many = config["many"]
                writable_on_create = config["write_on_create"]
                writable_on_update = config["write_on_update"]
                nested_data = config["data"]

                if nested_data is serializers.empty:
                    continue

                if not is_update and not writable_on_create:
                    continue
                if is_update and not writable_on_update:
                    continue

                target = getattr(instance, source_name, None)

                if many:
                    if nested_data is None:
                        if hasattr(target, "clear"):
                            target.clear()
                        continue

                    if not hasattr(target, "set"):
                        continue

                    saved_objects = []
                    for row in nested_data:
                        saved_objects.append(self._save_nested_item(field_name, target, row))
                    target.set(saved_objects)
                    continue

                if nested_data is None:
                    setattr(instance, source_name, None)
                    instance.save(update_fields=[source_name])
                    continue

                if target is None:
                    relation_field = instance._meta.get_field(source_name)
                    related_model = relation_field.remote_field.model
                    target = related_model.objects.create(**nested_data)
                    setattr(instance, source_name, target)
                    instance.save(update_fields=[source_name])
                else:
                    self._update_object_with_setattr(target, nested_data)

        def create(self, validated_data):
            nested_payload = {}
            if normalized_nested:
                for field_name, config in normalized_nested.items():
                    source_name = config.get("source", field_name)
                    nested_payload[field_name] = {
                        "source": source_name,
                        "many": bool(config.get("many", False)),
                        "write_on_create": bool(config.get("write_on_create", True)),
                        "write_on_update": bool(config.get("write_on_update", True)),
                        "data": validated_data.pop(source_name, serializers.empty),
                    }

            if create_handler is not None:
                instance = create_handler(self, validated_data)
            else:
                instance = super().create(validated_data)

            self._apply_nested_writes(instance, nested_payload, is_update=False)
            return instance

        def update(self, instance, validated_data):
            nested_payload = {}
            if normalized_nested:
                for field_name, config in normalized_nested.items():
                    source_name = config.get("source", field_name)
                    nested_payload[field_name] = {
                        "source": source_name,
                        "many": bool(config.get("many", False)),
                        "write_on_create": bool(config.get("write_on_create", True)),
                        "write_on_update": bool(config.get("write_on_update", True)),
                        "data": validated_data.pop(source_name, serializers.empty),
                    }

            if update_handler is not None:
                updated_instance = update_handler(self, instance, validated_data)
            else:
                updated_instance = super().update(instance, validated_data)

            self._apply_nested_writes(updated_instance, nested_payload, is_update=True)
            return updated_instance

        def validate(self, attrs):
            attrs = super().validate(attrs)
            if validate_handler is not None:
                return validate_handler(self, attrs)
            return attrs

        def to_internal_value(self, data):
            if to_internal_value_handler is not None:
                return to_internal_value_handler(self, data)
            return super().to_internal_value(data)

        def to_representation(self, instance):
            representation = super().to_representation(instance)
            if to_representation_handler is not None:
                return to_representation_handler(self, instance, representation)
            return representation

    AutoSerializer.__name__ = f"{model_class.__name__}Serializer"

    if normalized_nested:
        for field_name, config in normalized_nested.items():
            serializer_cls = config["serializer"]
            source_name = config.get("source", field_name)
            nested_field = serializer_cls(
                many=bool(config.get("many", False)),
                required=bool(config.get("required", False)),
                allow_null=bool(config.get("allow_null", True)),
                read_only=bool(config.get("read_only", False)),
                source=source_name,
            )
            AutoSerializer._declared_fields[field_name] = nested_field

    if method_overrides:
        for method_name, method in method_overrides.items():
            setattr(AutoSerializer, method_name, method)

    return AutoSerializer


class ERPModelViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsPagination
    ordering = ("-created_at",)


class ERPReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = StandardResultsPagination
    ordering = ("-created_at",)


def build_action_route(
    method_name,
    handler,
    *,
    methods=("post",),
    detail=True,
    url_path=None,
    url_name=None,
):
    """Create a DRF @action-decorated route handler for dynamic viewsets."""

    @action(methods=list(methods), detail=detail, url_path=url_path, url_name=url_name)
    def route(self, request, *args, **kwargs):
        return handler(self, request, *args, **kwargs)

    route.__name__ = method_name
    return route


def build_model_viewset(
    model_class,
    serializer_class,
    search_fields=(),
    filterset_fields=(),
    ordering_fields=(),
    permission_classes=None,
    queryset_handler=None,
    select_related_fields=None,
    prefetch_related_fields=None,
    destroy_handler=None,
    tenant_field_name="company",
    tenant_scoped=None,
    include_global_records=False,
    auto_assign_company=True,
    soft_delete=False,
    soft_delete_field="is_active",
    archive_field="is_archived",
    extra_routes=None,
    method_overrides=None,
    base_viewset_class=ERPModelViewSet,
    allow_public_schema=False,
    enforce_model_permissions=True,
):
    has_tenant_field = _model_has_field(model_class, tenant_field_name)
    if tenant_scoped is None:
        # Auto-enable only for models that explicitly carry a tenant/company FK.
        # For schema-isolated TenantAwareModel records, DB schema already scopes data.
        tenant_scoped = has_tenant_field

    class AutoViewSet(base_viewset_class):
        queryset = model_class.objects.all()

        def initial(self, request, *args, **kwargs):
            ensure_tenant_route(
                model_class,
                request,
                tenant_scoped=tenant_scoped,
                allow_public_schema=allow_public_schema,
            )
            return super().initial(request, *args, **kwargs)

        def get_serializer_context(self):
            context = super().get_serializer_context()
            context["tenant"] = _get_request_tenant(self.request)
            context["schema_name"] = _get_current_schema_name()
            return context

        def check_permissions(self, request):
            super().check_permissions(request)

            if not enforce_model_permissions:
                return

            required_perm = _get_required_model_permission(model_class, self.action)
            if required_perm is None:
                return

            if not getattr(request.user, "is_authenticated", False):
                raise PermissionDenied("Authentication is required for this action.")

            if not request.user.has_perm(required_perm):
                raise PermissionDenied(f"Missing required permission: {required_perm}")

        def get_queryset(self):
            ensure_tenant_route(
                model_class,
                self.request,
                tenant_scoped=tenant_scoped,
                allow_public_schema=allow_public_schema,
            )
            queryset = super().get_queryset()
            if select_related_fields:
                queryset = queryset.select_related(*select_related_fields)
            else:
                for field in self.queryset.model._meta.fields:
                    if isinstance(field, models.ForeignKey):
                        queryset = queryset.select_related(field.name)

            if prefetch_related_fields:
                queryset = queryset.prefetch_related(*prefetch_related_fields)

            if queryset_handler is not None:
                queryset = queryset_handler(self, queryset)

            if tenant_scoped:
                queryset = scope_queryset(
                    queryset,
                    request=self.request,
                    field_name=tenant_field_name,
                    include_global=include_global_records,
                )

            return queryset

        def perform_create(self, serializer):
            save_kwargs = {}
            if getattr(self.request.user, "is_authenticated", False) and _model_has_field(model_class, "created_by"):
                save_kwargs["created_by"] = self.request.user

            if tenant_scoped and auto_assign_company and has_tenant_field:
                tenant = _get_request_tenant(self.request)
                if tenant is not None:
                    save_kwargs[tenant_field_name] = tenant

            instance = serializer.save(**save_kwargs)
            if tenant_scoped and auto_assign_company:
                assign_company_and_save(
                    instance,
                    request=self.request,
                    field_name=tenant_field_name,
                )
            return instance

        def destroy(self, request, *args, **kwargs):
            if destroy_handler is not None:
                return destroy_handler(self, request, *args, **kwargs)

            if soft_delete:
                instance = self.get_object()
                if hasattr(instance, soft_delete_field):
                    update_fields = [soft_delete_field]
                    setattr(instance, soft_delete_field, False)

                    if archive_field and hasattr(instance, archive_field):
                        setattr(instance, archive_field, True)
                        update_fields.append(archive_field)

                    instance.save(update_fields=update_fields)
                    return Response(status=204)

            return super().destroy(request, *args, **kwargs)

    AutoViewSet.__name__ = f"{model_class.__name__}ViewSet"
    AutoViewSet.serializer_class = serializer_class
    AutoViewSet.search_fields = search_fields
    AutoViewSet.filterset_fields = filterset_fields
    AutoViewSet.ordering_fields = ordering_fields or search_fields
    if permission_classes is not None:
        AutoViewSet.permission_classes = permission_classes

    if extra_routes:
        for route_name, route_handler in extra_routes.items():
            setattr(AutoViewSet, route_name, route_handler)

    if method_overrides:
        for method_name, method in method_overrides.items():
            setattr(AutoViewSet, method_name, method)

    return AutoViewSet


def build_readonly_model_viewset(
    model_class,
    serializer_class,
    search_fields=(),
    filterset_fields=(),
    ordering_fields=(),
    permission_classes=None,
    queryset_handler=None,
    select_related_fields=None,
    prefetch_related_fields=None,
    tenant_field_name="company",
    tenant_scoped=None,
    include_global_records=False,
    extra_routes=None,
    method_overrides=None,
):
    return build_model_viewset(
        model_class,
        serializer_class,
        search_fields=search_fields,
        filterset_fields=filterset_fields,
        ordering_fields=ordering_fields,
        permission_classes=permission_classes,
        queryset_handler=queryset_handler,
        select_related_fields=select_related_fields,
        prefetch_related_fields=prefetch_related_fields,
        tenant_field_name=tenant_field_name,
        tenant_scoped=tenant_scoped,
        include_global_records=include_global_records,
        extra_routes=extra_routes,
        method_overrides=method_overrides,
        base_viewset_class=ERPReadOnlyModelViewSet,
        allow_public_schema=True,
    )
