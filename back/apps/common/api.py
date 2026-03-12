from django.db import models
from rest_framework import serializers, viewsets

from apps.common.pagination import StandardResultsPagination


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


def build_model_serializer(model_class, read_only_fields=None):
    meta_read_only = ("id", "created_at", "updated_at")
    if read_only_fields:
        meta_read_only = meta_read_only + tuple(read_only_fields)

    class AutoSerializer(BaseModelSerializer):
        class Meta(BaseModelSerializer.Meta):
            model = model_class
            read_only_fields = meta_read_only

    AutoSerializer.__name__ = f"{model_class.__name__}Serializer"
    return AutoSerializer


class ERPModelViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsPagination
    ordering = ("-created_at",)


def build_model_viewset(model_class, serializer_class, search_fields=(), filterset_fields=(), ordering_fields=()):
    class AutoViewSet(ERPModelViewSet):
        queryset = model_class.objects.all()

        def get_queryset(self):
            queryset = super().get_queryset()
            for field in self.queryset.model._meta.fields:
                if isinstance(field, models.ForeignKey):
                    queryset = queryset.select_related(field.name)
            return queryset

    AutoViewSet.__name__ = f"{model_class.__name__}ViewSet"
    AutoViewSet.serializer_class = serializer_class
    AutoViewSet.search_fields = search_fields
    AutoViewSet.filterset_fields = filterset_fields
    AutoViewSet.ordering_fields = ordering_fields or search_fields
    return AutoViewSet
