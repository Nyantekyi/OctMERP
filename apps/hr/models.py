"""
apps/hr/models.py

Human Resources Management for the ERP.

Covers:
  - Skills, Certifications, Holidays
  - Vacancies, Meetings
  - Employee contract + salary rules + severance
  - Benefits, Deductions
  - Leave management
  - Scheduled shifts, Attendance, Overtime
  - Loans
  - Payroll + Payroll detail lines
  - Performance evaluations
"""

import calendar
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from apps.common.models import TenantAwareModel, DEFAULT_CURRENCY, CURRENCY_CHOICES


# ─────────────────────────────────────────────────────────────────────────────
# Skills & Certifications
# ─────────────────────────────────────────────────────────────────────────────

class Skill(TenantAwareModel):
    name = models.CharField(_("Skill"), max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ["name"]

    def __str__(self):
        return self.name


class SkillLevel(TenantAwareModel):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(_("Level Name"), max_length=50)      # e.g. Beginner/Intermediate/Expert
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Skill Level")
        verbose_name_plural = _("Skill Levels")
        unique_together = ("skill", "name")
        ordering = ["skill", "order"]

    def __str__(self):
        return f"{self.skill.name} — {self.name}"


class EmployeeSkill(TenantAwareModel):
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="skills", verbose_name=_("Staff")
    )
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="employee_skills")
    level = models.ForeignKey(SkillLevel, null=True, blank=True, on_delete=models.SET_NULL, related_name="employee_skills")
    years_experience = models.PositiveSmallIntegerField(_("Years Experience"), default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("Employee Skill")
        verbose_name_plural = _("Employee Skills")
        unique_together = ("staff", "skill")

    def __str__(self):
        return f"{self.staff} — {self.skill}"


class Certification(TenantAwareModel):
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="certifications"
    )
    title = models.CharField(_("Certification Title"), max_length=255)
    issuing_body = models.CharField(_("Issued By"), max_length=255, blank=True)
    issued_on = models.DateField(_("Issued On"), null=True, blank=True)
    expires_on = models.DateField(_("Expires On"), null=True, blank=True)
    credential_id = models.CharField(_("Credential ID"), max_length=100, blank=True)
    document = models.FileField(_("Certificate File"), upload_to="certifications/%Y/%m/", null=True, blank=True)

    class Meta:
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")
        ordering = ["-issued_on"]

    def __str__(self):
        return f"{self.title} — {self.staff}"

    @property
    def is_expired(self):
        if self.expires_on:
            return date.today() > self.expires_on
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Holiday
# ─────────────────────────────────────────────────────────────────────────────

class Holiday(TenantAwareModel):
    name = models.CharField(_("Holiday Name"), max_length=100)
    date = models.DateField(_("Date"))
    is_recurring = models.BooleanField(
        _("Recurring Annually?"), default=False,
        help_text=_("If true, this holiday recurs every year on the same date.")
    )
    country = models.ForeignKey(
        "contact.Country", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Country"), related_name="holidays"
    )
    branches = models.ManyToManyField(
        "department.Branch", verbose_name=_("Applicable Branches"), blank=True, related_name="holidays"
    )

    class Meta:
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} ({self.date})"


# ─────────────────────────────────────────────────────────────────────────────
# Meeting
# ─────────────────────────────────────────────────────────────────────────────

class MeetingSubject(TenantAwareModel):
    name = models.CharField(_("Subject"), max_length=255, unique=True)

    class Meta:
        verbose_name = _("Meeting Subject")
        verbose_name_plural = _("Meeting Subjects")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Meeting(TenantAwareModel):
    STATUS_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    title = models.CharField(_("Title"), max_length=255)
    subject = models.ForeignKey(
        MeetingSubject, on_delete=models.SET_NULL, null=True, blank=True, related_name="meetings"
    )
    scheduled_start = models.DateTimeField(_("Starts At"))
    scheduled_end = models.DateTimeField(_("Ends At"))
    location = models.CharField(_("Location"), max_length=255, blank=True)
    organizer = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="organized_meetings"
    )
    attendees = models.ManyToManyField(
        "party.StaffProfile", blank=True, verbose_name=_("Attendees"), related_name="attended_meetings"
    )
    agenda = models.TextField(_("Agenda"), blank=True)
    minutes = models.TextField(_("Minutes"), blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="scheduled")

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ["-scheduled_start"]

    def __str__(self):
        return f"{self.title} @ {self.scheduled_start:%Y-%m-%d %H:%M}"

    def clean(self):
        if self.scheduled_end and self.scheduled_start and self.scheduled_end <= self.scheduled_start:
            raise ValidationError(_("Meeting end time must be after start time."))


# ─────────────────────────────────────────────────────────────────────────────
# Vacancy & Recruitment
# ─────────────────────────────────────────────────────────────────────────────

class Vacancy(TenantAwareModel):
    STATUS_CHOICES = [
        ("open", _("Open")),
        ("in_review", _("Under Review")),
        ("on_hold", _("On Hold")),
        ("closed", _("Closed")),
        ("filled", _("Filled")),
    ]

    title = models.CharField(_("Job Title"), max_length=200)
    occupation = models.ForeignKey(
        "party.Occupation", on_delete=models.SET_NULL, null=True, blank=True, related_name="vacancies"
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="vacancies"
    )
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="vacancies", null=True, blank=True
    )
    description = models.TextField(_("Job Description"))
    requirements = models.TextField(_("Requirements"), blank=True)
    skills_required = models.ManyToManyField(Skill, blank=True, related_name="vacancies")
    number_of_positions = models.PositiveSmallIntegerField(_("Positions Available"), default=1)
    application_deadline = models.DateField(_("Application Deadline"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="open")
    is_internal = models.BooleanField(_("Internal Posting?"), default=False)

    class Meta:
        verbose_name = _("Vacancy")
        verbose_name_plural = _("Vacancies")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.department.name}"


class JobApplication(TenantAwareModel):
    STAGE_CHOICES = [
        ("applied", _("Applied")),
        ("screening", _("Screening")),
        ("interview", _("Interview")),
        ("offer", _("Offer Extended")),
        ("hired", _("Hired")),
        ("rejected", _("Rejected")),
        ("withdrawn", _("Withdrawn")),
    ]

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="applications")
    applicant_name = models.CharField(_("Applicant Name"), max_length=200)
    applicant_email = models.EmailField(_("Applicant Email"))
    cover_letter = models.TextField(_("Cover Letter"), blank=True)
    resume = models.FileField(_("Resume"), upload_to="resumes/%Y/%m/", null=True, blank=True)
    stage = models.CharField(_("Stage"), max_length=20, choices=STAGE_CHOICES, default="applied")
    notes = models.TextField(blank=True)
    # If applicant is already a system user
    staff_profile = models.ForeignKey(
        "party.StaffProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="job_applications"
    )

    class Meta:
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant_name} → {self.vacancy.title}"


# ─────────────────────────────────────────────────────────────────────────────
# Benefits & Deductions
# ─────────────────────────────────────────────────────────────────────────────

class Benefit(TenantAwareModel):
    BENEFIT_TYPE_CHOICES = (
        ("fixed", _("Fixed Amount")),
        ("percent", _("Percentage of Salary")),
        ("reimbursement", _("Reimbursement")),
    )

    name = models.CharField(_("Benefit Name"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    benefit_type = models.CharField(_("Type"), max_length=20, choices=BENEFIT_TYPE_CHOICES, default="fixed")
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    percentage = models.DecimalField(
        _("Percentage"), max_digits=5, decimal_places=2, default=0,
        help_text=_("Used when benefit_type=percent")
    )
    is_taxable = models.BooleanField(_("Taxable?"), default=False)

    class Meta:
        verbose_name = _("Benefit")
        verbose_name_plural = _("Benefits")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Deduction(TenantAwareModel):
    """Mandatory/voluntary payroll deduction type (SSF, NHIS, income tax, etc.)."""
    DEDUCTION_TYPE_CHOICES = (
        ("fixed", _("Fixed Amount")),
        ("percent", _("Percentage of Gross")),
        ("statutory", _("Statutory / Government")),
    )

    name = models.CharField(_("Deduction Name"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    deduction_type = models.CharField(_("Type"), max_length=20, choices=DEDUCTION_TYPE_CHOICES, default="fixed")
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    percentage = models.DecimalField(_("Percentage"), max_digits=5, decimal_places=2, default=0)
    is_mandatory = models.BooleanField(_("Mandatory?"), default=False)
    # Auto-linked account (posted to liabilities)
    deduction_account = models.ForeignKey(
        "accounting.Account", null=True, blank=True, editable=False,
        on_delete=models.SET_NULL, related_name="deduction_accounts"
    )

    class Meta:
        verbose_name = _("Deduction")
        verbose_name_plural = _("Deductions")
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Employee Contract / Management
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeManagement(TenantAwareModel):
    """
    Holds the formal employment record for a staff member.
    One staff member can have at most one active contract at a time.
    """
    CONTRACT_TYPE_CHOICES = [
        ("permanent", _("Permanent")),
        ("fixed_term", _("Fixed Term")),
        ("part_time", _("Part Time")),
        ("contract", _("Contract / Freelance")),
        ("intern", _("Internship")),
    ]
    STATUS_CHOICES = [
        ("active", _("Active")),
        ("probation", _("Probation")),
        ("suspended", _("Suspended")),
        ("terminated", _("Terminated")),
        ("resigned", _("Resigned")),
        ("retired", _("Retired")),
    ]

    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="employment_records"
    )
    occupation = models.ForeignKey(
        "party.Occupation", on_delete=models.PROTECT, related_name="employment_records", null=True, blank=True
    )
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="employment_records"
    )
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="employment_records", null=True, blank=True
    )
    contract_type = models.CharField(_("Contract Type"), max_length=20, choices=CONTRACT_TYPE_CHOICES)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="active")
    hire_date = models.DateField(_("Hire Date"))
    probation_end_date = models.DateField(_("Probation End Date"), null=True, blank=True)
    contract_end_date = models.DateField(_("Contract End Date"), null=True, blank=True)
    termination_date = models.DateField(_("Termination Date"), null=True, blank=True)
    termination_reason = models.TextField(_("Termination Reason"), blank=True, null=True)

    class Meta:
        verbose_name = _("Employee Management Record")
        verbose_name_plural = _("Employee Management Records")
        ordering = ["-hire_date"]

    def __str__(self):
        return f"{self.staff} — {self.contract_type} ({self.status})"

    def clean(self):
        if self.contract_end_date and self.contract_end_date < self.hire_date:
            raise ValidationError(_("Contract end date cannot be before hire date."))


class EmployeeSalaryRule(TenantAwareModel):
    """Salary bracket/rule for an employment record."""
    employment = models.ForeignKey(
        EmployeeManagement, on_delete=models.CASCADE, related_name="salary_rules"
    )
    effective_from = models.DateField(_("Effective From"))
    effective_to = models.DateField(_("Effective To"), null=True, blank=True)
    basic_salary = MoneyField(
        _("Basic Salary"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    benefits = models.ManyToManyField(Benefit, blank=True, verbose_name=_("Benefits"), related_name="salary_rules")
    deductions = models.ManyToManyField(
        Deduction, blank=True, verbose_name=_("Deductions"), related_name="salary_rules"
    )

    class Meta:
        verbose_name = _("Employee Salary Rule")
        verbose_name_plural = _("Employee Salary Rules")
        ordering = ["-effective_from"]

    def __str__(self):
        return f"{self.employment.staff} — {self.basic_salary} from {self.effective_from}"


class EmployeeSeverancePackage(TenantAwareModel):
    employment = models.OneToOneField(
        EmployeeManagement, on_delete=models.CASCADE, related_name="severance_package"
    )
    amount = MoneyField(
        _("Severance Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    notice_period_days = models.PositiveSmallIntegerField(_("Notice Period (days)"), default=30)
    calculated_on = models.DateField(_("Calculated On"), auto_now_add=True)
    transaction_doc = models.ForeignKey(
        "accounting.TransactionDoc", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="severance_packages"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Severance Package")
        verbose_name_plural = _("Severance Packages")

    def __str__(self):
        return f"Severance for {self.employment.staff} — {self.amount}"


class EmployeeDeduction(TenantAwareModel):
    """Individual deduction instance per employee per payroll cycle."""
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="deduction_records"
    )
    deduction = models.ForeignKey(Deduction, on_delete=models.PROTECT, related_name="employee_deductions")
    amount = MoneyField(
        _("Deduction Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    effective_from = models.DateField(_("Effective From"))
    effective_to = models.DateField(_("Effective To"), null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    # Auto-linked via signal on creation
    liability_account = models.ForeignKey(
        "accounting.Account", null=True, blank=True, editable=False,
        on_delete=models.SET_NULL, related_name="deduction_liabilities"
    )

    class Meta:
        verbose_name = _("Employee Deduction")
        verbose_name_plural = _("Employee Deductions")
        ordering = ["staff", "-effective_from"]

    def __str__(self):
        return f"{self.staff} — {self.deduction.name}"


class EmployeeBenefit(TenantAwareModel):
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="benefit_records"
    )
    benefit = models.ForeignKey(Benefit, on_delete=models.PROTECT, related_name="employee_benefits")
    amount_override = MoneyField(
        _("Amount Override"), max_digits=20, decimal_places=2,
        null=True, blank=True,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    effective_from = models.DateField(_("Effective From"))
    effective_to = models.DateField(_("Effective To"), null=True, blank=True)

    class Meta:
        verbose_name = _("Employee Benefit")
        verbose_name_plural = _("Employee Benefits")
        unique_together = ("staff", "benefit")

    def __str__(self):
        return f"{self.staff} — {self.benefit.name}"


class EmployeeBankDetails(TenantAwareModel):
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="bank_details"
    )
    bank = models.ForeignKey(
        "accounting.Bank", on_delete=models.PROTECT, related_name="staff_accounts"
    )
    account_name = models.CharField(_("Account Name"), max_length=255)
    account_number = models.CharField(_("Account Number"), max_length=50)
    is_primary = models.BooleanField(_("Primary?"), default=False)

    class Meta:
        verbose_name = _("Employee Bank Details")
        verbose_name_plural = _("Employee Bank Details")
        unique_together = ("staff", "bank", "account_number")

    def __str__(self):
        return f"{self.staff} — {self.account_name} @ {self.bank}"


# ─────────────────────────────────────────────────────────────────────────────
# Leave
# ─────────────────────────────────────────────────────────────────────────────

class LeaveType(TenantAwareModel):
    name = models.CharField(_("Leave Type"), max_length=100, unique=True)
    days_allowed_per_year = models.PositiveSmallIntegerField(_("Days Allowed per Year"), default=21)
    is_paid = models.BooleanField(_("Paid Leave?"), default=True)
    carry_over = models.BooleanField(_("Carry Over to Next Year?"), default=False)
    max_carry_over_days = models.PositiveSmallIntegerField(_("Max Carry-Over Days"), default=0)
    requires_document = models.BooleanField(_("Requires Supporting Document?"), default=False)
    color = models.CharField(_("Calendar Colour"), max_length=7, default="#3B82F6")

    class Meta:
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Leave(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("cancelled", _("Cancelled")),
    ]

    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="leaves"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="leave_requests")
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    reason = models.TextField(_("Reason"), blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(
        "party.StaffProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="approved_leaves"
    )
    support_document = models.FileField(
        _("Supporting Document"), upload_to="leave_docs/%Y/%m/", null=True, blank=True
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)

    class Meta:
        verbose_name = _("Leave Request")
        verbose_name_plural = _("Leave Requests")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.staff} — {self.leave_type} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError(_("End date cannot be before start date."))

    @property
    def number_of_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0


class LeaveBalance(TenantAwareModel):
    """Running leave balance per staff per leave type per year."""
    staff = models.ForeignKey("party.StaffProfile", on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="balances")
    year = models.PositiveSmallIntegerField(_("Year"), default=timezone.now().year)
    entitled_days = models.PositiveSmallIntegerField(_("Entitled Days"), default=0)
    taken_days = models.DecimalField(_("Days Taken"), max_digits=5, decimal_places=1, default=0)
    carry_over_days = models.PositiveSmallIntegerField(_("Carry-Over Days"), default=0)

    class Meta:
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")
        unique_together = ("staff", "leave_type", "year")

    def __str__(self):
        return f"{self.staff} — {self.leave_type} {self.year}: {self.remaining_days} remaining"

    @property
    def remaining_days(self):
        return self.entitled_days + self.carry_over_days - float(self.taken_days)


# ─────────────────────────────────────────────────────────────────────────────
# Shifts & Attendance
# ─────────────────────────────────────────────────────────────────────────────

class ScheduledShift(TenantAwareModel):
    """Assigned shift for a staff member on a given date/week."""
    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="scheduled_shifts"
    )
    shift = models.ForeignKey("department.Shift", on_delete=models.PROTECT, related_name="scheduled_shifts")
    date = models.DateField(_("Date"))
    branch = models.ForeignKey(
        "department.Branch", on_delete=models.PROTECT, related_name="scheduled_shifts"
    )
    notes = models.CharField(_("Notes"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Scheduled Shift")
        verbose_name_plural = _("Scheduled Shifts")
        ordering = ["date", "shift"]
        unique_together = ("staff", "date", "shift")

    def __str__(self):
        return f"{self.staff} — {self.shift} on {self.date}"


class Attendance(TenantAwareModel):
    STATUS_CHOICES = [
        ("present", _("Present")),
        ("absent", _("Absent")),
        ("late", _("Late")),
        ("half_day", _("Half Day")),
        ("on_leave", _("On Leave")),
        ("public_holiday", _("Public Holiday")),
    ]

    staff = models.ForeignKey("party.StaffProfile", on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(_("Date"))
    check_in = models.DateTimeField(_("Check-In Time"), null=True, blank=True)
    check_out = models.DateTimeField(_("Check-Out Time"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="present")
    shift = models.ForeignKey(
        "department.Shift", on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_records"
    )
    leave = models.ForeignKey(Leave, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_records")
    location = models.CharField(_("Work Location"), max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Attendance Record")
        verbose_name_plural = _("Attendance Records")
        ordering = ["-date"]
        unique_together = ("staff", "date")

    def __str__(self):
        return f"{self.staff} — {self.date} ({self.status})"

    @property
    def hours_worked(self):
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 2)
        return 0


class OverTime(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("paid", _("Paid")),
    ]

    staff = models.ForeignKey("party.StaffProfile", on_delete=models.CASCADE, related_name="overtime_records")
    attendance = models.ForeignKey(Attendance, on_delete=models.PROTECT, related_name="overtime_entries")
    hours = models.DecimalField(_("Overtime Hours"), max_digits=5, decimal_places=2, default=0)
    rate_multiplier = models.DecimalField(_("Rate Multiplier"), max_digits=4, decimal_places=2, default=1.5)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(
        "party.StaffProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="approved_overtimes"
    )
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Overtime")
        verbose_name_plural = _("Overtimes")
        ordering = ["-attendance__date"]

    def __str__(self):
        return f"{self.staff} — {self.hours}h OT on {self.attendance.date}"


# ─────────────────────────────────────────────────────────────────────────────
# Staff Loans
# ─────────────────────────────────────────────────────────────────────────────

class LoanType(TenantAwareModel):
    name = models.CharField(_("Loan Type"), max_length=100, unique=True)
    description = models.TextField(blank=True)
    max_amount = MoneyField(
        _("Max Amount"), max_digits=20, decimal_places=2, null=True, blank=True,
        default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    interest_rate_percent = models.DecimalField(_("Interest Rate %"), max_digits=5, decimal_places=2, default=0)
    max_tenure_months = models.PositiveSmallIntegerField(_("Max Tenure (months)"), default=12)

    class Meta:
        verbose_name = _("Loan Type")
        verbose_name_plural = _("Loan Types")
        ordering = ["name"]

    def __str__(self):
        return self.name


class StaffLoan(TenantAwareModel):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("active", _("Active")),
        ("completed", _("Completed")),
        ("rejected", _("Rejected")),
        ("written_off", _("Written Off")),
    ]

    staff = models.ForeignKey("party.StaffProfile", on_delete=models.CASCADE, related_name="loans")
    loan_type = models.ForeignKey(LoanType, on_delete=models.PROTECT, related_name="loans")
    amount = MoneyField(
        _("Loan Amount"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    outstanding_balance = MoneyField(
        _("Outstanding Balance"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    disbursement_date = models.DateField(_("Disbursement Date"), null=True, blank=True)
    tenure_months = models.PositiveSmallIntegerField(_("Tenure (months)"), default=12)
    monthly_repayment = MoneyField(
        _("Monthly Repayment"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(
        "party.StaffProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="approved_loans"
    )
    transaction_doc = models.ForeignKey(
        "accounting.TransactionDoc", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="staff_loans"
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Staff Loan")
        verbose_name_plural = _("Staff Loans")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.staff} — {self.loan_type.name} {self.amount}"


# ─────────────────────────────────────────────────────────────────────────────
# Payroll
# ─────────────────────────────────────────────────────────────────────────────

class Payroll(TenantAwareModel):
    """
    Represents the payroll run for a given period.
    The pay_date is always set to the first day of the month by default.
    """
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("processing", _("Processing")),
        ("approved", _("Approved")),
        ("paid", _("Paid")),
        ("cancelled", _("Cancelled")),
    ]

    name = models.CharField(_("Name"), max_length=100, unique=True)
    pay_date = models.DateField(_("Pay Date"))
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="draft")
    department = models.ForeignKey(
        "department.Department", on_delete=models.PROTECT, related_name="payrolls"
    )
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        "party.StaffProfile", null=True, blank=True, on_delete=models.SET_NULL, related_name="processed_payrolls"
    )
    transaction_doc = models.ForeignKey(
        "accounting.TransactionDoc", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="payrolls"
    )

    class Meta:
        verbose_name = _("Payroll")
        verbose_name_plural = _("Payrolls")
        ordering = ["-pay_date"]

    def __str__(self):
        return f"{self.name} — {self.pay_date}"

    def save(self, *args, **kwargs):
        # Normalise pay_date to first of the month on creation
        if self._state.adding and self.pay_date:
            self.pay_date = self.pay_date.replace(day=1)
        super().save(*args, **kwargs)

    @property
    def total_gross(self):
        return sum(d.gross_salary.amount for d in self.details.all())

    @property
    def total_net(self):
        return sum(d.net_salary.amount for d in self.details.all())


class PayrollDetail(TenantAwareModel):
    """Per-employee line inside a Payroll run."""
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name="details")
    staff = models.ForeignKey("party.StaffProfile", on_delete=models.PROTECT, related_name="payroll_details")
    employment = models.ForeignKey(
        EmployeeManagement, on_delete=models.PROTECT, related_name="payroll_details", null=True, blank=True
    )
    basic_salary = MoneyField(
        _("Basic Salary"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    total_allowances = MoneyField(
        _("Total Allowances"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    gross_salary = MoneyField(
        _("Gross Salary"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    total_deductions = MoneyField(
        _("Total Deductions"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    income_tax = MoneyField(
        _("Income Tax"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    social_security = MoneyField(
        _("Social Security"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    overtime_pay = MoneyField(
        _("Overtime Pay"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    loan_repayment = MoneyField(
        _("Loan Repayment"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    net_salary = MoneyField(
        _("Net Salary"), max_digits=20, decimal_places=2,
        default=0, default_currency=DEFAULT_CURRENCY, currency_choices=CURRENCY_CHOICES
    )
    is_paid = models.BooleanField(_("Paid?"), default=False)
    payment_date = models.DateTimeField(_("Payment Date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Payroll Detail")
        verbose_name_plural = _("Payroll Details")
        unique_together = ("payroll", "staff")
        ordering = ["staff"]

    def __str__(self):
        return f"{self.payroll} — {self.staff} net {self.net_salary}"

    def compute_net(self):
        self.gross_salary = self.basic_salary + self.total_allowances + self.overtime_pay
        self.net_salary = self.gross_salary - self.total_deductions - self.income_tax - self.social_security - self.loan_repayment
        return self.net_salary


# ─────────────────────────────────────────────────────────────────────────────
# Performance Evaluation
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceEvaluation(TenantAwareModel):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]   # 1–5

    staff = models.ForeignKey(
        "party.StaffProfile", on_delete=models.CASCADE, related_name="evaluations"
    )
    evaluated_by = models.ForeignKey(
        "party.StaffProfile", on_delete=models.PROTECT, related_name="evaluations_given"
    )
    period_start = models.DateField(_("Period Start"))
    period_end = models.DateField(_("Period End"))
    overall_rating = models.PositiveSmallIntegerField(_("Overall Rating"), choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    goals_set = models.TextField(_("Goals Set"), blank=True)
    goals_achieved = models.TextField(_("Goals Achieved"), blank=True)
    areas_for_improvement = models.TextField(_("Areas for Improvement"), blank=True)
    training_recommended = models.TextField(_("Training Recommended"), blank=True)

    class Meta:
        verbose_name = _("Performance Evaluation")
        verbose_name_plural = _("Performance Evaluations")
        ordering = ["-period_end"]

    def __str__(self):
        return f"{self.staff} — Rating {self.overall_rating} for {self.period_start} to {self.period_end}"


# ─────────────────────────────────────────────────────────────────────────────
# Account auto-creation for EmployeeDeduction via post_save
# ─────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender=EmployeeDeduction)
def create_deduction_account(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from django.contrib.contenttypes.models import ContentType
        from apps.accounting.models import Account, ChartsOfAccount
        coa = ChartsOfAccount.objects.get(name="Other Liabilities")
        ct = ContentType.objects.get_for_model(sender)
        acc, _ = Account.objects.get_or_create(
            content_type=ct, object_id=instance.id, account_type=coa
        )
        EmployeeDeduction.objects.filter(pk=instance.id).update(liability_account=acc)
    except Exception:
        pass
