from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.crm.api.views import CampaignViewSet, DealViewSet, PipelineTransitionViewSet, PipelineViewSet, ProspectCompanyViewSet, ProspectPipelineStageViewSet, ProspectViewSet, SaleMemberViewSet, SaleTeamViewSet, StageViewSet, TerritoryViewSet

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
router.register("prospect-pipeline-stages", ProspectPipelineStageViewSet, basename="prospect-pipeline-stage")
router.register("deals", DealViewSet, basename="deal")

urlpatterns = [path("", include(router.urls))]
