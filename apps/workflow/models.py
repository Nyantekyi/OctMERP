"""
apps/workflow/models.py

Workflow templates and checklist items for approval chains,
process automation, and task assignment.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantAwareModel


class WorkflowTemplate(TenantAwareModel):
    """
    A named workflow definition (e.g. "Leave Approval", "PO Approval").
    """
    MODULE_CHOICES = [
        ("hr", _("HR")),
        ("procurement", _("Procurement")),
        ("accounting", _("Accounting")),
        ("sales", _("Sales")),
        ("assets", _("Assets")),
        ("projects", _("Projects")),
        ("general", _("General")),
    ]

    name = models.CharField(_("Workflow Name"), max_length=100, unique=True)
    module = models.CharField(_("Module"), max_length=20, choices=MODULE_CHOICES, default="general")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Workflow Template")

    def __str__(self):
        return self.name


class WorkflowStep(TenantAwareModel):
    """One step in a WorkflowTemplate."""
    STEP_TYPE_CHOICES = [
        ("approval", _("Approval")),
        ("notification", _("Notification")),
        ("auto_action", _("Automatic Action")),
        ("review", _("Review")),
    ]

    workflow = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name="steps")
    sequence = models.PositiveSmallIntegerField(_("Sequence"), default=0)
    name = models.CharField(_("Step Name"), max_length=100)
    step_type = models.CharField(_("Type"), max_length=20, choices=STEP_TYPE_CHOICES, default="approval")
    assigned_group = models.ForeignKey(
        "auth.Group", on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_user = models.ForeignKey(
        "party.CustomUser", on_delete=models.SET_NULL, null=True, blank=True
    )
    requires_all = models.BooleanField(
        _("Requires All Approvers"), default=False,
        help_text=_("If True, ALL assigned users must approve.")
    )
    sla_hours = models.PositiveSmallIntegerField(
        _("SLA (hours)"), default=24,
        help_text=_("Auto-escalate if no action within this many hours.")
    )

    class Meta:
        verbose_name = _("Workflow Step")
        ordering = ["workflow", "sequence"]

    def __str__(self):
        return f"{self.workflow} → Step {self.sequence}: {self.name}"


class WorkflowInstance(TenantAwareModel):
    """A running instance of a workflow attached to a specific object."""
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("in_progress", _("In Progress")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("cancelled", _("Cancelled")),
    ]

    workflow = models.ForeignKey(WorkflowTemplate, on_delete=models.PROTECT, related_name="instances")
    content_type = models.ForeignKey(
        "contenttypes.ContentType", on_delete=models.CASCADE, related_name="workflow_instances"
    )
    object_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    current_step = models.ForeignKey(
        WorkflowStep, on_delete=models.SET_NULL, null=True, blank=True, related_name="active_instances"
    )
    initiated_by = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT, related_name="initiated_workflows"
    )

    class Meta:
        verbose_name = _("Workflow Instance")

    def __str__(self):
        return f"{self.workflow} [{self.status}]"


class WorkflowAction(TenantAwareModel):
    """An approval/rejection action performed on a WorkflowInstance step."""
    ACTION_CHOICES = [
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("returned", _("Returned for Revision")),
    ]

    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name="actions")
    step = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey(
        "party.CustomUser", on_delete=models.PROTECT, related_name="workflow_actions"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Workflow Action")

    def __str__(self):
        return f"{self.instance} — {self.step} [{self.action}]"
