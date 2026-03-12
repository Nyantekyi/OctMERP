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

    class AutoSerializer(BaseModelSerializer):
        class Meta(BaseModelSerializer.Meta):
            model = model_class
            read_only_fields = meta_read_only

        def create(self, validated_data):
            if create_handler is not None:
                return create_handler(self, validated_data)
            return super().create(validated_data)

        def update(self, instance, validated_data):
            if update_handler is not None:
                return update_handler(self, instance, validated_data)
            return super().update(instance, validated_data)

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

    if method_overrides:
        for method_name, method in method_overrides.items():
            setattr(AutoSerializer, method_name, method)

    return AutoSerializer


class ERPModelViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsPagination
    ordering = ("-created_at",)

    def build_response_envelope(self, payload, success=True, errors=None, meta=None):
        return {
            "success": success,
            "data": payload,
            "meta": meta,
            "errors": errors,
        }

    def as_enveloped_response(self, response):
        if not isinstance(response, Response):
            return response

        data = response.data
        if isinstance(data, dict) and {"success", "data", "errors"}.issubset(data.keys()):
            return response

        success = 200 <= response.status_code < 400
        meta = None
        payload = data if success else None
        errors = None if success else data

        if success and isinstance(data, dict) and "results" in data and "count" in data:
            payload = data.get("results", [])
            meta = {
                "count": data.get("count"),
                "total_pages": data.get("total_pages"),
                "next": data.get("next"),
                "previous": data.get("previous"),
            }

        response.data = self.build_response_envelope(
            payload=payload,
            success=success,
            errors=errors,
            meta=meta,
        )
        return response


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
    serializer_context_handler=None,
    serializer_class_handler=None,
    permission_handler=None,
    queryset_handler=None,
    select_related_fields=None,
    prefetch_related_fields=None,
    retrieve_object_handler=None,
    list_handler=None,
    retrieve_handler=None,
    create_handler=None,
    update_handler=None,
    partial_update_handler=None,
    destroy_handler=None,
    perform_create_handler=None,
    perform_update_handler=None,
    perform_destroy_handler=None,
    use_response_envelope=False,
    response_envelope_handler=None,
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

        def get_object(self):
            instance = super().get_object()
            if retrieve_object_handler is not None:
                return retrieve_object_handler(self, instance)
            return instance

        def get_serializer_context(self):
            context = super().get_serializer_context()
            if serializer_context_handler is not None:
                return serializer_context_handler(self, context)
            return context

        def get_serializer_class(self):
            if serializer_class_handler is not None:
                return serializer_class_handler(self)
            return super().get_serializer_class()

        def get_permissions(self):
            if permission_handler is not None:
                return permission_handler(self)
            return super().get_permissions()

        def perform_create(self, serializer):
            if perform_create_handler is not None:
                return perform_create_handler(self, serializer)
            return super().perform_create(serializer)

        def create(self, request, *args, **kwargs):
            if create_handler is not None:
                response = create_handler(self, request, *args, **kwargs)
            else:
                response = super().create(request, *args, **kwargs)
            return self._maybe_envelope_response(response)

        def list(self, request, *args, **kwargs):
            if list_handler is not None:
                response = list_handler(self, request, *args, **kwargs)
            else:
                response = super().list(request, *args, **kwargs)
            return self._maybe_envelope_response(response)

        def retrieve(self, request, *args, **kwargs):
            if retrieve_handler is not None:
                response = retrieve_handler(self, request, *args, **kwargs)
            else:
                response = super().retrieve(request, *args, **kwargs)
            return self._maybe_envelope_response(response)

        def update(self, request, *args, **kwargs):
            if update_handler is not None:
                response = update_handler(self, request, *args, **kwargs)
            else:
                response = super().update(request, *args, **kwargs)
            return self._maybe_envelope_response(response)

        def partial_update(self, request, *args, **kwargs):
            if partial_update_handler is not None:
                response = partial_update_handler(self, request, *args, **kwargs)
            else:
                response = super().partial_update(request, *args, **kwargs)
            return self._maybe_envelope_response(response)

        def destroy(self, request, *args, **kwargs):
            if destroy_handler is not None:
                response = destroy_handler(self, request, *args, **kwargs)
                return self._maybe_envelope_response(response)

            if soft_delete:
                instance = self.get_object()
                if hasattr(instance, soft_delete_field):
                    update_fields = [soft_delete_field]
                    setattr(instance, soft_delete_field, False)

                    if archive_field and hasattr(instance, archive_field):
                        setattr(instance, archive_field, True)
                        update_fields.append(archive_field)

                    instance.save(update_fields=update_fields)
                    response = Response(status=204)
                    return self._maybe_envelope_response(response)

            response = super().destroy(request, *args, **kwargs)
            return self._maybe_envelope_response(response)

        def perform_update(self, serializer):
            if perform_update_handler is not None:
                return perform_update_handler(self, serializer)
            return super().perform_update(serializer)

        def perform_destroy(self, instance):
            if perform_destroy_handler is not None:
                return perform_destroy_handler(self, instance)
            return super().perform_destroy(instance)

        def _maybe_envelope_response(self, response):
            if not use_response_envelope:
                return response
            if response_envelope_handler is not None:
                return response_envelope_handler(self, response)
            return self.as_enveloped_response(response)

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
