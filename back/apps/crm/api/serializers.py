from rest_framework import serializers

from apps.common.api import build_model_serializer
from apps.crm.models import Campaign, Deal, Pipeline, PipelineTransition, Prospect, ProspectPipelineStage, Prospect_Company, SaleMember, SaleTeam, Territory, stage

TerritorySerializer = build_model_serializer(Territory)
SaleTeamSerializer = build_model_serializer(SaleTeam)
SaleMemberSerializer = build_model_serializer(SaleMember)
PipelineSerializer = build_model_serializer(Pipeline)
StageSerializer = build_model_serializer(stage)
PipelineTransitionSerializer = build_model_serializer(PipelineTransition)
CampaignSerializer = build_model_serializer(Campaign)
ProspectCompanySerializer = build_model_serializer(Prospect_Company)
ProspectSerializer = build_model_serializer(Prospect)
ProspectPipelineStageSerializer = build_model_serializer(ProspectPipelineStage)


class DealSerializer(build_model_serializer(Deal)):
    weighted_value = serializers.SerializerMethodField()

    class Meta(build_model_serializer(Deal).Meta):
        fields = "__all__"

    def get_weighted_value(self, obj):
        return str(obj.weighted_value)
