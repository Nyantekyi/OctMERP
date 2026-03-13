from rest_framework import serializers

from apps.crm.models import Lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["id", "name", "email", "stage", "created_at"]
