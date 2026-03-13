from rest_framework import serializers

from apps.core_shared.models import GlobalAnnouncement


class GlobalAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalAnnouncement
        fields = ["id", "title", "body", "is_active", "created_at"]
