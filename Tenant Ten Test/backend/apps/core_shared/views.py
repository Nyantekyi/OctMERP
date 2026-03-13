from rest_framework.generics import ListAPIView

from apps.core_shared.models import GlobalAnnouncement
from apps.core_shared.serializers import GlobalAnnouncementSerializer


class GlobalAnnouncementListAPIView(ListAPIView):
    queryset = GlobalAnnouncement.objects.filter(is_active=True)
    serializer_class = GlobalAnnouncementSerializer
