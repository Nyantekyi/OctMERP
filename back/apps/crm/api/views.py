from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.crm.api.serializers import CampaignSerializer, DealSerializer, PipelineSerializer, PipelineTransitionSerializer, ProspectCompanySerializer, ProspectPipelineStageSerializer, ProspectSerializer, SaleMemberSerializer, SaleTeamSerializer, StageSerializer, TerritorySerializer
from apps.crm.models import Campaign, Deal, Pipeline, PipelineTransition, Prospect, ProspectPipelineStage, Prospect_Company, SaleMember, SaleTeam, Territory, stage

TerritoryViewSet = build_model_viewset(Territory, TerritorySerializer, search_fields=("name",), filterset_fields=("branch",))
SaleTeamViewSet = build_model_viewset(SaleTeam, SaleTeamSerializer, search_fields=("name",), filterset_fields=("territory", "department"))
SaleMemberViewSet = build_model_viewset(SaleMember, SaleMemberSerializer, filterset_fields=("team", "staff", "role"))
PipelineViewSet = build_model_viewset(Pipeline, PipelineSerializer, search_fields=("name",), filterset_fields=("department",))
StageViewSet = build_model_viewset(stage, StageSerializer, search_fields=("name",), filterset_fields=("pipeline", "is_closed_won", "is_closed_lost"), ordering_fields=("order",))
PipelineTransitionViewSet = build_model_viewset(PipelineTransition, PipelineTransitionSerializer, filterset_fields=("from_stage", "to_stage", "requires_approval"))
CampaignViewSet = build_model_viewset(Campaign, CampaignSerializer, search_fields=("name",), filterset_fields=("status", "campaign_type", "team"), ordering_fields=("start_date", "end_date"))
ProspectCompanyViewSet = build_model_viewset(Prospect_Company, ProspectCompanySerializer, search_fields=("name",), filterset_fields=("industry", "country", "assigned_team"))
ProspectViewSet = build_model_viewset(Prospect, ProspectSerializer, search_fields=("first_name", "last_name", "email"), filterset_fields=("company", "campaign", "assigned_to", "is_converted"))
ProspectPipelineStageViewSet = build_model_viewset(ProspectPipelineStage, ProspectPipelineStageSerializer, filterset_fields=("prospect", "pipeline", "current_stage"))


def _move_deal_to_terminal_stage(viewset, request, stage_filter):
    deal = viewset.get_object()
    next_stage = stage.objects.filter(pipeline=deal.pipeline, is_active=True, **stage_filter).order_by("order").first()
    if next_stage is None:
        return Response(
            {"detail": "No matching terminal stage exists for this pipeline."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    deal.current_stage = next_stage
    deal.probability = 100 if stage_filter.get("is_closed_won") else 0
    deal.actual_close_date = timezone.now().date()
    deal.save(update_fields=["current_stage", "probability", "actual_close_date", "updated_at"])

    serializer = viewset.get_serializer(deal)
    return Response(serializer.data, status=status.HTTP_200_OK)


def _close_won_handler(viewset, request, *args, **kwargs):
    return _move_deal_to_terminal_stage(viewset, request, {"is_closed_won": True})


def _close_lost_handler(viewset, request, *args, **kwargs):
    return _move_deal_to_terminal_stage(viewset, request, {"is_closed_lost": True})


DealViewSet = build_model_viewset(
    Deal,
    DealSerializer,
    search_fields=("name",),
    filterset_fields=("pipeline", "current_stage", "assigned_to", "team"),
    ordering_fields=("expected_close_date", "created_at"),
    soft_delete=True,
    extra_routes={
        "close_won": build_action_route("close_won", _close_won_handler, url_path="close-won"),
        "close_lost": build_action_route("close_lost", _close_lost_handler, url_path="close-lost"),
    },
)
