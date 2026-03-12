"""
apps/crm/serializers.py
"""
from rest_framework import serializers

from .models import (
    Territory, SaleTeam, SaleMember,
    Pipeline, Stage, PipelineTransition,
    Campaign, ProspectCompany, Prospect,
    ProspectPipelineStage, ProspectActivity, Deal,
)


class TerritorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Territory
        fields = ["id", "name", "description", "countries", "branch", "parent_territory", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SaleTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleTeam
        fields = ["id", "name", "description", "territory", "department", "team_lead", "monthly_target", "monthly_target_currency", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SaleMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleMember
        fields = ["id", "team", "staff", "role", "joined_on", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "joined_on", "created_at", "updated_at"]


class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ["id", "name", "description", "department", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ["id", "pipeline", "name", "order", "probability", "is_closed_won", "is_closed_lost", "color", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PipelineTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineTransition
        fields = ["id", "from_stage", "to_stage", "requires_approval", "notes", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id", "name", "campaign_type", "status", "start_date", "end_date",
            "budget", "budget_currency", "expected_revenue", "expected_revenue_currency",
            "actual_cost", "actual_cost_currency",
            "team", "description", "target_url", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProspectCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProspectCompany
        fields = ["id", "name", "industry", "website", "size_range", "country", "notes", "assigned_team", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prospect
        fields = [
            "id", "first_name", "last_name", "company", "email", "phone", "job_title",
            "source", "campaign", "assigned_to", "notes",
            "converted_client", "is_converted", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProspectPipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProspectPipelineStage
        fields = ["id", "prospect", "pipeline", "current_stage", "entered_stage_on", "notes", "created_at", "updated_at"]
        read_only_fields = ["id", "entered_stage_on", "created_at", "updated_at"]


class ProspectActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProspectActivity
        fields = [
            "id", "prospect", "activity_type", "performed_by", "occurred_on",
            "summary", "next_action", "next_action_date", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DealSerializer(serializers.ModelSerializer):
    weighted_value = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            "id", "name", "prospect", "client", "pipeline", "current_stage",
            "assigned_to", "team",
            "expected_revenue", "expected_revenue_currency",
            "probability", "expected_close_date", "actual_close_date",
            "source", "notes", "sales_order",
            "weighted_value", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_weighted_value(self, obj):
        val = obj.weighted_value
        return {"amount": str(val.amount), "currency": str(val.currency)}
