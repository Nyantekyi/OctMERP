"""
apps/crm/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    Territory, SaleTeam, SaleMember,
    Pipeline, Stage, PipelineTransition,
    Campaign, ProspectCompany, Prospect,
    ProspectPipelineStage, ProspectActivity, Deal,
)
from .serializers import (
    TerritorySerializer, SaleTeamSerializer, SaleMemberSerializer,
    PipelineSerializer, StageSerializer, PipelineTransitionSerializer,
    CampaignSerializer, ProspectCompanySerializer, ProspectSerializer,
    ProspectPipelineStageSerializer, ProspectActivitySerializer, DealSerializer,
)


class TerritoryViewSet(viewsets.ModelViewSet):
    queryset = Territory.objects.select_related("branch", "parent_territory")
    serializer_class = TerritorySerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["branch", "is_active"]


class SaleTeamViewSet(viewsets.ModelViewSet):
    queryset = SaleTeam.objects.select_related("territory", "department", "team_lead")
    serializer_class = SaleTeamSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["department", "territory", "is_active"]


class SaleMemberViewSet(viewsets.ModelViewSet):
    queryset = SaleMember.objects.select_related("team", "staff")
    serializer_class = SaleMemberSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["team", "staff", "role"]


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.select_related("department")
    serializer_class = PipelineSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["department"]


class StageViewSet(viewsets.ModelViewSet):
    queryset = Stage.objects.select_related("pipeline")
    serializer_class = StageSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["pipeline", "is_closed_won", "is_closed_lost"]
    ordering_fields = ["order"]


class PipelineTransitionViewSet(viewsets.ModelViewSet):
    queryset = PipelineTransition.objects.select_related("from_stage", "to_stage")
    serializer_class = PipelineTransitionSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["from_stage", "to_stage", "requires_approval"]


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.select_related("team")
    serializer_class = CampaignSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "campaign_type", "team", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["start_date", "end_date"]


class ProspectCompanyViewSet(viewsets.ModelViewSet):
    queryset = ProspectCompany.objects.select_related("industry", "country", "assigned_team")
    serializer_class = ProspectCompanySerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["industry", "country", "is_active"]


class ProspectViewSet(viewsets.ModelViewSet):
    queryset = Prospect.objects.select_related("company", "campaign", "assigned_to")
    serializer_class = ProspectSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["source", "campaign", "assigned_to", "is_converted"]
    search_fields = ["first_name", "last_name", "email"]

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        prospect = self.get_object()
        prospect.is_converted = True
        prospect.save()
        return Response({"success": True, "data": ProspectSerializer(prospect).data})


class ProspectPipelineStageViewSet(viewsets.ModelViewSet):
    queryset = ProspectPipelineStage.objects.select_related("prospect", "pipeline", "current_stage")
    serializer_class = ProspectPipelineStageSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["pipeline", "current_stage"]


class ProspectActivityViewSet(viewsets.ModelViewSet):
    queryset = ProspectActivity.objects.select_related("prospect", "performed_by")
    serializer_class = ProspectActivitySerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["prospect", "activity_type", "performed_by"]
    ordering_fields = ["occurred_on"]


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.select_related("prospect", "client", "pipeline", "current_stage", "assigned_to", "team")
    serializer_class = DealSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["pipeline", "current_stage", "assigned_to", "team", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["expected_close_date", "expected_revenue", "created_at"]
