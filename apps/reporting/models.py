"""
apps/reporting/models.py

Saved reports, dashboard configurations, and KPI snapshots.
Actual report data is generated dynamically; this app stores
report definitions, user-pinned dashboards, and periodic snapshots.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantAwareModel


class ReportDefinition(TenantAwareModel):
    MODULE_CHOICES = [
        ("accounting", _("Accounting")),
        ("hr", _("HR & Payroll")),
        ("inventory", _("Inventory")),
        ("sales", _("Sales")),
        ("procurement", _("Procurement")),
        ("crm", _("CRM")),
        ("manufacturing", _("Manufacturing")),
        ("logistics", _("Logistics")),
        ("pos", _("POS")),
        ("assets", _("Assets")),
        ("projects", _("Projects")),
        ("general", _("General")),
    ]
    FORMAT_CHOICES = [
        ("table", _("Table")),
        ("bar_chart", _("Bar Chart")),
        ("line_chart", _("Line Chart")),
        ("pie_chart", _("Pie Chart")),
        ("pivot", _("Pivot Table")),
        ("kpi", _("KPI Card")),
    ]

    name = models.CharField(_("Report Name"), max_length=200)
    module = models.CharField(_("Module"), max_length=20, choices=MODULE_CHOICES)
    description = models.TextField(blank=True)
    format = models.CharField(_("Display Format"), max_length=20, choices=FORMAT_CHOICES, default="table")
    # JSON config: filters, groupby, measures, sort, etc.
    config = models.JSONField(_("Report Config"), default=dict)
    is_public = models.BooleanField(_("Visible to all?"), default=False)
    owner = models.ForeignKey(
        "party.CustomUser", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="owned_reports"
    )

    class Meta:
        verbose_name = _("Report Definition")

    def __str__(self):
        return f"[{self.module}] {self.name}"


class Dashboard(TenantAwareModel):
    """User-configurable dashboard layout."""
    name = models.CharField(_("Dashboard Name"), max_length=100)
    owner = models.ForeignKey(
        "party.CustomUser", on_delete=models.CASCADE, related_name="dashboards"
    )
    is_default = models.BooleanField(_("Default Dashboard"), default=False)
    layout = models.JSONField(_("Widget Layout"), default=list)

    class Meta:
        verbose_name = _("Dashboard")

    def __str__(self):
        return f"{self.name} ({self.owner})"


class DashboardWidget(TenantAwareModel):
    WIDGET_TYPE_CHOICES = [
        ("kpi_card", _("KPI Card")),
        ("chart", _("Chart")),
        ("table", _("Data Table")),
        ("activity_feed", _("Activity Feed")),
    ]

    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name="widgets")
    report = models.ForeignKey(
        ReportDefinition, on_delete=models.SET_NULL, null=True, blank=True, related_name="widgets"
    )
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES, default="kpi_card")
    title = models.CharField(max_length=100)
    position_x = models.PositiveSmallIntegerField(default=0)
    position_y = models.PositiveSmallIntegerField(default=0)
    width = models.PositiveSmallIntegerField(default=4)
    height = models.PositiveSmallIntegerField(default=2)

    class Meta:
        verbose_name = _("Dashboard Widget")
        ordering = ["dashboard", "position_y", "position_x"]

    def __str__(self):
        return f"{self.dashboard} — {self.title}"


class KPISnapshot(TenantAwareModel):
    """
    Periodic snapshot of a KPI metric for trend analysis.
    Populated by Celery scheduled tasks.
    """
    metric_key = models.CharField(_("Metric Key"), max_length=100)
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.CASCADE,
        null=True, blank=True, related_name="kpi_snapshots"
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.CASCADE,
        null=True, blank=True, related_name="kpi_snapshots"
    )
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    value = models.DecimalField(_("Value"), max_digits=20, decimal_places=4)
    currency = models.CharField(max_length=3, blank=True)
    meta = models.JSONField(_("Metadata"), default=dict)

    class Meta:
        verbose_name = _("KPI Snapshot")
        verbose_name_plural = _("KPI Snapshots")
        ordering = ["-period_end"]
        indexes = [
            models.Index(fields=["metric_key", "branch", "period_end"]),
        ]

    def __str__(self):
        return f"{self.metric_key} @ {self.period_end}: {self.value}"


class ScheduledReport(TenantAwareModel):
    """Auto-generates and emails a report on a schedule."""
    report = models.ForeignKey(ReportDefinition, on_delete=models.CASCADE, related_name="schedules")
    recipients = models.ManyToManyField("party.CustomUser", blank=True, related_name="scheduled_reports")
    cron_expression = models.CharField(max_length=50, default="0 7 * * 1")
    format_output = models.CharField(
        max_length=10, choices=[("pdf", "PDF"), ("csv", "CSV"), ("xlsx", "Excel")], default="pdf"
    )
    last_sent_at = models.DateTimeField(null=True, blank=True)
    next_send_at = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Scheduled Report")

    def __str__(self):
        return f"Scheduled: {self.report} [{self.cron_expression}]"
