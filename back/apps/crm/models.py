from django.core.exceptions import ValidationError
from django.db import models
from djmoney.models.fields import MoneyField

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


default_currency = "GHS"


class Territory(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    branch = models.ForeignKey("department.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="territories")
    parent_territory = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    def __str__(self):
        return self.name


class SaleTeam(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    territory = models.ForeignKey(Territory, null=True, blank=True, on_delete=models.SET_NULL, related_name="sale_teams")
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="sale_teams")
    team_lead = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="led_sale_teams")
    monthly_target = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)

    def __str__(self):
        return self.name


class SaleMember(createdtimestamp_uid, activearchlockedMixin):
    team = models.ForeignKey(SaleTeam, on_delete=models.CASCADE, related_name="members")
    staff = models.ForeignKey("party.Staff", on_delete=models.CASCADE, related_name="sale_memberships")
    role = models.CharField(max_length=50, default="sales_rep")
    joined_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = (("team", "staff"),)


class Pipeline(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="pipelines")

    def __str__(self):
        return self.name


class stage(createdtimestamp_uid, activearchlockedMixin):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name="stages")
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_closed_won = models.BooleanField(default=False)
    is_closed_lost = models.BooleanField(default=False)

    class Meta:
        unique_together = (("pipeline", "name"),)
        ordering = ("pipeline", "order")

    def clean(self):
        if self.is_closed_won and self.is_closed_lost:
            raise ValidationError("A stage cannot be both won and lost.")

    def __str__(self):
        return self.name


class PipelineTransition(createdtimestamp_uid, activearchlockedMixin):
    from_stage = models.ForeignKey(stage, on_delete=models.CASCADE, related_name="outgoing")
    to_stage = models.ForeignKey(stage, on_delete=models.CASCADE, related_name="incoming")
    requires_approval = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (("from_stage", "to_stage"),)


class Campaign(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255, unique=True)
    campaign_type = models.CharField(max_length=50, default="email")
    status = models.CharField(max_length=20, default="draft")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    expected_revenue = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    actual_cost = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    team = models.ForeignKey(SaleTeam, null=True, blank=True, on_delete=models.SET_NULL, related_name="campaigns")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Prospect_Company(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255)
    industry = models.ForeignKey("company.Industry", null=True, blank=True, on_delete=models.SET_NULL, related_name="prospect_companies")
    website = models.URLField(blank=True)
    size_range = models.CharField(max_length=30, blank=True)
    country = models.ForeignKey("contact.Country", null=True, blank=True, on_delete=models.SET_NULL, related_name="prospect_companies")
    notes = models.TextField(blank=True)
    assigned_team = models.ForeignKey(SaleTeam, null=True, blank=True, on_delete=models.SET_NULL, related_name="prospect_companies")

    def __str__(self):
        return self.name


class Prospect(createdtimestamp_uid, activearchlockedMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    company = models.ForeignKey(Prospect_Company, null=True, blank=True, on_delete=models.SET_NULL, related_name="contacts")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50, default="other")
    campaign = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="prospects")
    assigned_to = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_prospects")
    notes = models.TextField(blank=True)
    converted_client = models.ForeignKey("party.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="origin_prospects")
    is_converted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class ProspectPipelineStage(createdtimestamp_uid, activearchlockedMixin):
    prospect = models.OneToOneField(Prospect, on_delete=models.CASCADE, related_name="pipeline_stage")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name="prospect_positions")
    current_stage = models.ForeignKey(stage, on_delete=models.CASCADE, related_name="prospects")
    entered_stage_on = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)


class Deal(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=255)
    prospect = models.ForeignKey(Prospect, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    client = models.ForeignKey("party.Client", null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT, related_name="deals")
    current_stage = models.ForeignKey(stage, on_delete=models.PROTECT, related_name="deals")
    assigned_to = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_deals")
    team = models.ForeignKey(SaleTeam, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    expected_revenue = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    source = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals")
    notes = models.TextField(blank=True)

    @property
    def weighted_value(self):
        return self.expected_revenue.amount * (self.probability / 100)

    def __str__(self):
        return self.name
