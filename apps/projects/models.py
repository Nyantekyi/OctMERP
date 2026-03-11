"""
apps/projects/models.py

Project and task management for the ERP.

Covers:
  - Projects with budgets, client links, and status lifecycle
  - Project members and roles
  - Milestones
  - Tasks and sub-tasks (with priority/status tracking)
  - Time logging per staff per task
  - Project expenses (linked to accounting)
  - File attachments
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────────────────────────────────────

class Project(TenantAwareModel):
    STATUS_CHOICES = [
        ("planning", _("Planning")),
        ("active", _("Active")),
        ("on_hold", _("On Hold")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]
    BILLING_TYPE_CHOICES = [
        ("fixed", _("Fixed Price")),
        ("time_material", _("Time & Material")),
        ("retainer", _("Retainer")),
        ("internal", _("Internal / Non-billable")),
    ]

    code = models.CharField(_("Project Code"), max_length=30, unique=True)
    name = models.CharField(_("Project Name"), max_length=200)
    description = models.TextField(blank=True)
    client = models.ForeignKey(
        "party.ClientProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="projects"
    )
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="projects"
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="projects"
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="planning")
    billing_type = models.CharField(_("Billing Type"), max_length=20, choices=BILLING_TYPE_CHOICES, default="fixed")
    budget = MoneyField(
        _("Budget"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    start_date = models.DateField(_("Start Date"))
    deadline = models.DateField(_("Deadline"), null=True, blank=True)
    actual_end_date = models.DateField(_("Actual End Date"), null=True, blank=True)
    expense_account = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="project_budget_accounts"
    )
    budget_allocation = models.ForeignKey(
        "accounting.BudgetAllocation", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="projects"
    )
    sales_order = models.ForeignKey(
        "sales.SalesOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="projects"
    )
    tags = models.JSONField(_("Tags"), default=list, blank=True)

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def total_logged_hours(self):
        return self.time_logs.aggregate(total=models.Sum("hours"))["total"] or 0

    @property
    def total_expenses(self):
        return self.expenses.aggregate(total=models.Sum("amount"))["total"] or 0


# ─────────────────────────────────────────────────────────────────────────────
# Project Member
# ─────────────────────────────────────────────────────────────────────────────

class ProjectMember(TenantAwareModel):
    ROLE_CHOICES = [
        ("manager", _("Project Manager")),
        ("lead", _("Team Lead")),
        ("member", _("Member")),
        ("reviewer", _("Reviewer")),
        ("observer", _("Observer")),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="project_memberships"
    )
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateField(_("Joined"), default=timezone.now)
    allocation_percent = models.PositiveSmallIntegerField(
        _("Allocation (%)"), default=100,
        help_text=_("Percentage of working time allocated to this project")
    )
    hourly_rate = MoneyField(
        _("Hourly Rate"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )

    class Meta:
        verbose_name = _("Project Member")
        verbose_name_plural = _("Project Members")
        unique_together = ("project", "staff")

    def __str__(self):
        return f"{self.staff} on {self.project} ({self.role})"


# ─────────────────────────────────────────────────────────────────────────────
# Milestone
# ─────────────────────────────────────────────────────────────────────────────

class Milestone(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("in_progress", _("In Progress")),
        ("achieved", _("Achieved")),
        ("missed", _("Missed")),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(_("Milestone"), max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(_("Due Date"))
    achieved_date = models.DateField(_("Achieved Date"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    is_billable = models.BooleanField(_("Billable"), default=False)
    amount = MoneyField(
        _("Milestone Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )

    class Meta:
        verbose_name = _("Milestone")
        verbose_name_plural = _("Milestones")
        ordering = ["project", "due_date"]

    def __str__(self):
        return f"{self.project} — {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────────────────────

class Task(TenantAwareModel):
    PRIORITY_CHOICES = [
        ("critical", _("Critical")),
        ("high", _("High")),
        ("medium", _("Medium")),
        ("low", _("Low")),
    ]
    STATUS_CHOICES = [
        ("todo", _("To Do")),
        ("in_progress", _("In Progress")),
        ("in_review", _("In Review")),
        ("done", _("Done")),
        ("cancelled", _("Cancelled")),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    milestone = models.ForeignKey(
        Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks"
    )
    priority = models.CharField(_("Priority"), max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="todo")
    start_date = models.DateField(_("Start Date"), null=True, blank=True)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    estimated_hours = models.DecimalField(_("Estimated Hours"), max_digits=6, decimal_places=2, default=0)
    sequence = models.PositiveIntegerField(_("Sequence"), default=0)
    tags = models.JSONField(_("Tags"), default=list, blank=True)

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["project", "sequence", "priority"]

    def __str__(self):
        return f"{self.project} — {self.title}"

    @property
    def logged_hours(self):
        return self.time_logs.aggregate(total=models.Sum("hours"))["total"] or 0


class SubTask(TenantAwareModel):
    """Checklist item attached to a Task."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="subtasks")
    title = models.CharField(_("Sub-task"), max_length=255)
    is_completed = models.BooleanField(_("Done"), default=False)
    assigned_to = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_subtasks"
    )
    due_date = models.DateField(_("Due Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Sub-Task")
        verbose_name_plural = _("Sub-Tasks")
        ordering = ["task", "id"]

    def __str__(self):
        done = "✓" if self.is_completed else "○"
        return f"{done} {self.title}"


# ─────────────────────────────────────────────────────────────────────────────
# Time Log
# ─────────────────────────────────────────────────────────────────────────────

class TimeLog(TenantAwareModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="time_logs")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="time_logs")
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="project_time_logs"
    )
    date = models.DateField(_("Date"), default=timezone.now)
    hours = models.DecimalField(_("Hours"), max_digits=5, decimal_places=2)
    description = models.TextField(_("Description"), blank=True)
    is_billable = models.BooleanField(_("Billable"), default=True)
    billed = models.BooleanField(_("Billed"), default=False)

    class Meta:
        verbose_name = _("Time Log")
        verbose_name_plural = _("Time Logs")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.staff} — {self.hours}h on {self.date}"

    @property
    def billable_amount(self):
        try:
            member = self.project.members.get(staff=self.staff)
            return member.hourly_rate * self.hours
        except Exception:
            return 0


# ─────────────────────────────────────────────────────────────────────────────
# Project Expense
# ─────────────────────────────────────────────────────────────────────────────

class ProjectExpense(TenantAwareModel):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("submitted", _("Submitted")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("reimbursed", _("Reimbursed")),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="expenses")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    submitted_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="project_expenses"
    )
    expense_date = models.DateField(_("Date"), default=timezone.now)
    description = models.CharField(_("Description"), max_length=255)
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    receipt_url = models.CharField(_("Receipt URL"), max_length=500, blank=True)
    expense_account = models.ForeignKey(
        "accounting.Account", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="project_expense_accounts"
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    approved_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_project_expenses"
    )

    class Meta:
        verbose_name = _("Project Expense")
        verbose_name_plural = _("Project Expenses")
        ordering = ["-expense_date"]

    def __str__(self):
        return f"{self.project} — {self.description}: {self.amount}"


# ─────────────────────────────────────────────────────────────────────────────
# Project Document
# ─────────────────────────────────────────────────────────────────────────────

class ProjectDocument(TenantAwareModel):
    DOCUMENT_TYPE_CHOICES = [
        ("specification", _("Specification")),
        ("proposal", _("Proposal")),
        ("contract", _("Contract")),
        ("report", _("Report")),
        ("design", _("Design")),
        ("other", _("Other")),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    name = models.CharField(_("Document Name"), max_length=200)
    document_type = models.CharField(_("Type"), max_length=20, choices=DOCUMENT_TYPE_CHOICES, default="other")
    file_url = models.CharField(_("File URL"), max_length=500)
    uploaded_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="project_documents"
    )
    version = models.CharField(_("Version"), max_length=20, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Project Document")
        verbose_name_plural = _("Project Documents")
        ordering = ["project", "-created_at"]

    def __str__(self):
        return f"{self.project} — {self.name}"
