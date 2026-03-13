from rest_framework import serializers

from apps.manufacturing.models import WorkOrder


class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = ["id", "title", "status", "quantity", "due_date", "created_at"]
