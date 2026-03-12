"""apps/crm/serializers.py"""

from apps.common.api import build_model_serializer

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


def _deal_to_representation(serializer, instance, representation):
    val = instance.weighted_value
    representation["weighted_value"] = {"amount": str(val.amount), "currency": str(val.currency)}
    return representation


TerritorySerializer = build_model_serializer(Territory)
SaleTeamSerializer = build_model_serializer(SaleTeam)
SaleMemberSerializer = build_model_serializer(SaleMember, read_only_fields=("joined_on",))
PipelineSerializer = build_model_serializer(Pipeline)
StageSerializer = build_model_serializer(Stage)
PipelineTransitionSerializer = build_model_serializer(PipelineTransition)
CampaignSerializer = build_model_serializer(Campaign)
ProspectCompanySerializer = build_model_serializer(ProspectCompany)
ProspectSerializer = build_model_serializer(Prospect)
ProspectPipelineStageSerializer = build_model_serializer(
    ProspectPipelineStage,
    read_only_fields=("entered_stage_on",),
)
ProspectActivitySerializer = build_model_serializer(ProspectActivity)
DealSerializer = build_model_serializer(
    Deal,
    to_representation_handler=_deal_to_representation,
)
