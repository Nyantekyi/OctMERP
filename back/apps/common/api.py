from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import StandardResultsPagination


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


def build_model_serializer(
    model_class,
    read_only_fields=None,
    nested_serializers=None,
    create_handler=None,
    update_handler=None,
    validate_handler=None,
    to_internal_value_handler=None,
    to_representation_handler=None,
    method_overrides=None,
):
    meta_read_only = ("id", "created_at", "updated_at")
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
    soft_delete=False,
    soft_delete_field="is_active",
    archive_field="is_archived",
    extra_routes=None,
    method_overrides=None,
):
    class AutoViewSet(ERPModelViewSet):
        queryset = model_class.objects.all()

        def get_queryset(self):
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

            return queryset

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
