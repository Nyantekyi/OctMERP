from apps.common.api import build_model_viewset
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
DealViewSet = build_model_viewset(Deal, DealSerializer, search_fields=("name",), filterset_fields=("pipeline", "current_stage", "assigned_to", "team"), ordering_fields=("expected_close_date", "created_at"))
