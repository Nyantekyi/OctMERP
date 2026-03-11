"""
apps/crm/models.py

Customer Relationship Management for the ERP.

Covers:
  - Sales territory & team structure
  - Pipelines, stages, and stage transition rules
  - Campaigns and leads
  - Prospect companies and contacts
  - Deals with revenue tracking
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Territory & Sales Team
# ─────────────────────────────────────────────────────────────────────────────

class Territory(TenantAwareModel):
    """Geographic or market segment assigned to a sales team."""
    name = models.CharField(_("Territory Name"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    countries = models.ManyToManyField(
        "contact.Country", blank=True, verbose_name=_("Countries"), related_name="territories"
    )
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="territories"
    )
    parent_territory = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_territories"
    )

    class Meta:
        verbose_name = _("Territory")
        verbose_name_plural = _("Territories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class SaleTeam(TenantAwareModel):
    name = models.CharField(_("Team Name"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    territory = models.ForeignKey(
        Territory, on_delete=models.SET_NULL, null=True, blank=True, related_name="sale_teams"
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="sale_teams"
    )
    team_lead = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="led_teams"
    )
    monthly_target = MoneyField(
        _("Monthly Target"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )

    class Meta:
        verbose_name = _("Sales Team")
        verbose_name_plural = _("Sales Teams")
        ordering = ["name"]

    def __str__(self):
        return self.name


class SaleMember(TenantAwareModel):
    ROLE_CHOICES = [
        ("sales_rep", _("Sales Representative")),
        ("team_lead", _("Team Lead")),
        ("key_account", _("Key Account Manager")),
        ("support", _("Sales Support")),
    ]

    team = models.ForeignKey(SaleTeam, on_delete=models.CASCADE, related_name="members")
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="sale_memberships"
    )
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default="sales_rep")
    joined_on = models.DateField(_("Joined Team"), auto_now_add=True)

    class Meta:
        verbose_name = _("Sale Team Member")
        verbose_name_plural = _("Sale Team Members")
        unique_together = ("team", "staff")

    def __str__(self):
        return f"{self.staff} ({self.role}) — {self.team}"


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline & Stages
# ─────────────────────────────────────────────────────────────────────────────

class Pipeline(TenantAwareModel):
    """Defines a named sales or lead pipeline."""
    name = models.CharField(_("Pipeline Name"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="pipelines"
    )

    class Meta:
        verbose_name = _("Pipeline")
        verbose_name_plural = _("Pipelines")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Stage(TenantAwareModel):
    """Named stage within a pipeline with probability weighting."""
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name="stages")
    name = models.CharField(_("Stage Name"), max_length=100)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)
    probability = models.DecimalField(_("Win Probability %"), max_digits=5, decimal_places=2, default=0)
    is_closed_won = models.BooleanField(_("Closed Won?"), default=False)
    is_closed_lost = models.BooleanField(_("Closed Lost?"), default=False)
    color = models.CharField(_("Kanban Colour"), max_length=7, default="#6B7280")

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages")
        unique_together = ("pipeline", "name")
        ordering = ["pipeline", "order"]

    def __str__(self):
        return f"{self.pipeline.name} → {self.name}"

    def clean(self):
        if self.is_closed_won and self.is_closed_lost:
            raise ValidationError(_("A stage cannot be both Closed Won and Closed Lost."))


class PipelineTransition(TenantAwareModel):
    """Allowed transitions between stages (optional guardrail)."""
    from_stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="outgoing_transitions")
    to_stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="incoming_transitions")
    requires_approval = models.BooleanField(_("Requires Approval?"), default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Pipeline Transition")
        verbose_name_plural = _("Pipeline Transitions")
        unique_together = ("from_stage", "to_stage")

    def __str__(self):
        return f"{self.from_stage} → {self.to_stage}"

    def clean(self):
        if self.from_stage == self.to_stage:
            raise ValidationError(_("A stage cannot transition to itself."))
        if self.from_stage.pipeline != self.to_stage.pipeline:
            raise ValidationError(_("Transitions must be within the same pipeline."))


# ─────────────────────────────────────────────────────────────────────────────
# Campaign
# ─────────────────────────────────────────────────────────────────────────────

class Campaign(TenantAwareModel):
    CAMPAIGN_TYPE_CHOICES = [
        ("email", _("Email")),
        ("sms", _("SMS")),
        ("social_media", _("Social Media")),
        ("event", _("Event")),
        ("webinar", _("Webinar")),
        ("referral", _("Referral")),
        ("other", _("Other")),
    ]
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("active", _("Active")),
        ("paused", _("Paused")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    name = models.CharField(_("Campaign Name"), max_length=255, unique=True)
    campaign_type = models.CharField(_("Type"), max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    start_date = models.DateField(_("Start Date"), null=True, blank=True)
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    budget = MoneyField(
        _("Budget"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    expected_revenue = MoneyField(
        _("Expected Revenue"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    actual_cost = MoneyField(
        _("Actual Cost"), max_digits=20, decimal_places=2,
        null=True, blank=True, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    team = models.ForeignKey(
        SaleTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name="campaigns"
    )
    description = models.TextField(blank=True)
    target_url = models.URLField(_("Target / Landing Page URL"), blank=True)

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError(_("Campaign end date must be after start date."))


# ─────────────────────────────────────────────────────────────────────────────
# Prospect / Lead
# ─────────────────────────────────────────────────────────────────────────────

class ProspectCompany(TenantAwareModel):
    """An external company being prospected (not yet a client)."""
    name = models.CharField(_("Company Name"), max_length=255)
    industry = models.ForeignKey(
        "company.Industry", on_delete=models.SET_NULL, null=True, blank=True, related_name="prospect_companies"
    )
    website = models.URLField(_("Website"), blank=True)
    size_range = models.CharField(
        _("Company Size"), max_length=20, blank=True,
        help_text=_("e.g. '1-10', '11-50', '51-200', '200+'")
    )
    country = models.ForeignKey(
        "contact.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="prospect_companies"
    )
    notes = models.TextField(blank=True)
    assigned_team = models.ForeignKey(
        SaleTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name="prospect_companies"
    )

    class Meta:
        verbose_name = _("Prospect Company")
        verbose_name_plural = _("Prospect Companies")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Prospect(TenantAwareModel):
    """Individual lead/contact at a ProspectCompany."""
    SOURCE_CHOICES = [
        ("website", _("Website")),
        ("referral", _("Referral")),
        ("cold_call", _("Cold Call")),
        ("trade_show", _("Trade Show")),
        ("campaign", _("Campaign")),
        ("social_media", _("Social Media")),
        ("other", _("Other")),
    ]

    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100, blank=True)
    company = models.ForeignKey(
        ProspectCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name="contacts"
    )
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=30, blank=True)
    job_title = models.CharField(_("Job Title"), max_length=100, blank=True)
    source = models.CharField(_("Lead Source"), max_length=20, choices=SOURCE_CHOICES, default="other")
    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="prospects"
    )
    assigned_to = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_prospects"
    )
    notes = models.TextField(blank=True)
    # Once qualified, converted_client can be set
    converted_client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="originated_from_prospects"
    )
    is_converted = models.BooleanField(_("Converted?"), default=False)

    class Meta:
        verbose_name = _("Prospect")
        verbose_name_plural = _("Prospects")
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class ProspectPipelineStage(TenantAwareModel):
    """Tracks a prospect's current position in a pipeline."""
    prospect = models.OneToOneField(Prospect, on_delete=models.CASCADE, related_name="pipeline_position")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT, related_name="prospect_positions")
    current_stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="prospects_in_stage")
    entered_stage_on = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Prospect Pipeline Position")
        verbose_name_plural = _("Prospect Pipeline Positions")

    def __str__(self):
        return f"{self.prospect} in {self.current_stage}"


class ProspectActivity(TenantAwareModel):
    """Log of every touch point with a prospect."""
    ACTIVITY_TYPE_CHOICES = [
        ("call", _("Call")),
        ("email", _("Email")),
        ("meeting", _("Meeting")),
        ("demo", _("Demo")),
        ("proposal", _("Proposal")),
        ("note", _("Note")),
        ("other", _("Other")),
    ]

    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(_("Activity Type"), max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    performed_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, related_name="crm_activities"
    )
    occurred_on = models.DateTimeField(_("Occurred On"), default=timezone.now)
    summary = models.TextField(_("Summary"))
    next_action = models.TextField(_("Next Action"), blank=True)
    next_action_date = models.DateField(_("Next Action Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Prospect Activity")
        verbose_name_plural = _("Prospect Activities")
        ordering = ["-occurred_on"]

    def __str__(self):
        return f"{self.activity_type} with {self.prospect} on {self.occurred_on:%Y-%m-%d}"


# ─────────────────────────────────────────────────────────────────────────────
# Deal
# ─────────────────────────────────────────────────────────────────────────────

class Deal(TenantAwareModel):
    """An active sales opportunity with monetary value."""
    name = models.CharField(_("Deal Name"), max_length=255)
    prospect = models.ForeignKey(
        Prospect, on_delete=models.SET_NULL, null=True, blank=True, related_name="deals", verbose_name=_("Prospect")
    )
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="deals", verbose_name=_("Existing Client")
    )
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT, related_name="deals")
    current_stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="deals")
    assigned_to = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_deals"
    )
    team = models.ForeignKey(
        SaleTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name="deals"
    )
    expected_revenue = MoneyField(
        _("Expected Revenue"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    probability = models.DecimalField(_("Win Probability %"), max_digits=5, decimal_places=2, default=0)
    expected_close_date = models.DateField(_("Expected Close Date"), null=True, blank=True)
    actual_close_date = models.DateField(_("Actual Close Date"), null=True, blank=True)
    source = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="deals"
    )
    notes = models.TextField(blank=True)
    # After winning, link to SalesOrder
    sales_order = models.OneToOneField(
        "sales.SalesOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="deal"
    )

    class Meta:
        verbose_name = _("Deal")
        verbose_name_plural = _("Deals")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.expected_revenue} ({self.current_stage})"

    @property
    def weighted_value(self):
        return self.expected_revenue * (self.probability / 100)
