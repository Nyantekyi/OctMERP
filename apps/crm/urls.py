from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TerritoryViewSet, SaleTeamViewSet, SaleMemberViewSet,
    PipelineViewSet, StageViewSet, PipelineTransitionViewSet,
    CampaignViewSet, ProspectCompanyViewSet, ProspectViewSet,
    ProspectPipelineStageViewSet, ProspectActivityViewSet, DealViewSet,
)

app_name = "crm"

router = DefaultRouter()
router.register("territories", TerritoryViewSet, basename="territory")
router.register("sale-teams", SaleTeamViewSet, basename="sale-team")
router.register("sale-members", SaleMemberViewSet, basename="sale-member")
router.register("pipelines", PipelineViewSet, basename="pipeline")
router.register("stages", StageViewSet, basename="stage")
router.register("pipeline-transitions", PipelineTransitionViewSet, basename="pipeline-transition")
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("prospect-companies", ProspectCompanyViewSet, basename="prospect-company")
router.register("prospects", ProspectViewSet, basename="prospect")
router.register("prospect-positions", ProspectPipelineStageViewSet, basename="prospect-position")
router.register("activities", ProspectActivityViewSet, basename="activity")
router.register("deals", DealViewSet, basename="deal")

urlpatterns = [path("", include(router.urls))]

