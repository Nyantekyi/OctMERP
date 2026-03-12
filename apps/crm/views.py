"""apps/crm/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser
from .models import (
    Campaign,
    Deal,
    Pipeline,
    PipelineTransition,
    Prospect,
    ProspectActivity,
    ProspectCompany,
    ProspectPipelineStage,
    SaleMember,
    SaleTeam,
    Stage,
    Territory,
)
from .serializers import (
    CampaignSerializer,
    DealSerializer,
    PipelineSerializer,
    PipelineTransitionSerializer,
    ProspectActivitySerializer,
    ProspectCompanySerializer,
    ProspectPipelineStageSerializer,
    ProspectSerializer,
    SaleMemberSerializer,
    SaleTeamSerializer,
    StageSerializer,
    TerritorySerializer,
)


def _convert_prospect(self, request, *args, **kwargs):
    prospect = self.get_object()
    prospect.is_converted = True
    prospect.save(update_fields=["is_converted", "updated_at"])
    return Response({"success": True, "data": ProspectSerializer(prospect).data})


TerritoryViewSet = build_model_viewset(
    Territory,
    TerritorySerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["branch", "is_active"],
    select_related_fields=["branch", "parent_territory"],
)

SaleTeamViewSet = build_model_viewset(
    SaleTeam,
    SaleTeamSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["department", "territory", "is_active"],
    select_related_fields=["territory", "department", "team_lead"],
)

SaleMemberViewSet = build_model_viewset(
    SaleMember,
    SaleMemberSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["team", "staff", "role"],
    select_related_fields=["team", "staff"],
)

PipelineViewSet = build_model_viewset(
    Pipeline,
    PipelineSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["department"],
    select_related_fields=["department"],
)

StageViewSet = build_model_viewset(
    Stage,
    StageSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["pipeline", "is_closed_won", "is_closed_lost"],
    ordering_fields=["order"],
    select_related_fields=["pipeline"],
)

PipelineTransitionViewSet = build_model_viewset(
    PipelineTransition,
    PipelineTransitionSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["from_stage", "to_stage", "requires_approval"],
    select_related_fields=["from_stage", "to_stage"],
)

CampaignViewSet = build_model_viewset(
    Campaign,
    CampaignSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["status", "campaign_type", "team", "is_active"],
    ordering_fields=["start_date", "end_date"],
    select_related_fields=["team"],
)

ProspectCompanyViewSet = build_model_viewset(
    ProspectCompany,
    ProspectCompanySerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["industry", "country", "is_active"],
    select_related_fields=["industry", "country", "assigned_team"],
)

ProspectViewSet = build_model_viewset(
    Prospect,
    ProspectSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["first_name", "last_name", "email"],
    filterset_fields=["source", "campaign", "assigned_to", "is_converted"],
    select_related_fields=["company", "campaign", "assigned_to"],
    extra_routes={
        "convert": build_action_route("convert", _convert_prospect, methods=("post",), detail=True),
    },
)

ProspectPipelineStageViewSet = build_model_viewset(
    ProspectPipelineStage,
    ProspectPipelineStageSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["pipeline", "current_stage"],
    select_related_fields=["prospect", "pipeline", "current_stage"],
)

ProspectActivityViewSet = build_model_viewset(
    ProspectActivity,
    ProspectActivitySerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["prospect", "activity_type", "performed_by"],
    ordering_fields=["occurred_on"],
    select_related_fields=["prospect", "performed_by"],
)

DealViewSet = build_model_viewset(
    Deal,
    DealSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["pipeline", "current_stage", "assigned_to", "team", "is_active"],
    ordering_fields=["expected_close_date", "expected_revenue", "created_at"],
    select_related_fields=["prospect", "client", "pipeline", "current_stage", "assigned_to", "team"],
)
