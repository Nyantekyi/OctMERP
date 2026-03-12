from django.core.exceptions import ValidationError
from django.db import models
from djmoney.models.fields import MoneyField

from apps.common.models import activearchlockedMixin, createdtimestamp_uid


default_currency = "GHS"


class Skill(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    skillset = models.ManyToManyField("self", blank=True)

    def __str__(self):
        return self.name


class Holiday(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100)
    date = models.DateField()
    is_public = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    country = models.ForeignKey("contact.Country", null=True, blank=True, on_delete=models.SET_NULL, related_name="holidays")

    class Meta:
        unique_together = (("name", "date"),)

    def __str__(self):
        return self.name


class MeetingSubject(createdtimestamp_uid, activearchlockedMixin):
    purpose_type = models.JSONField(default=list, blank=True)
    subject = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    staff = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="meeting_subjects")

    def __str__(self):
        return self.subject


class Meeting(createdtimestamp_uid, activearchlockedMixin):
    room = models.ForeignKey("department.Room", on_delete=models.PROTECT, related_name="scheduled_meetings")
    subject = models.ForeignKey(MeetingSubject, null=True, blank=True, on_delete=models.SET_NULL, related_name="meetings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    assigned_branch = models.ManyToManyField("department.Branch", blank=True, related_name="meetings")
    assigned_department = models.ManyToManyField("department.Department", blank=True, related_name="meetings")
    attendees = models.ManyToManyField("party.Staff", blank=True, related_name="attending_meetings")
    participants = models.ManyToManyField("party.User", blank=True, related_name="participating_meetings")
    status = models.CharField(max_length=20, default="scheduled")
    agenda = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    rescheduled_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reschedules")

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Meeting end time must be after start time.")

    def __str__(self):
        return f"{self.subject} on {self.date}"


class Vacancy(createdtimestamp_uid, activearchlockedMixin):
    title = models.CharField(max_length=100)
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="vacancies")
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    posted_date = models.DateField(auto_now_add=True)
    closing_date = models.DateField(null=True, blank=True)
    is_filled = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Deduction(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    deduction_type = models.CharField(max_length=30, default="fixed")
    deduction = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    frequency = models.CharField(max_length=30, default="monthly")

    def __str__(self):
        return self.name


class Benefit(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    benefit_rate_type = models.CharField(max_length=30, default="fixed")
    benefit = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    frequency = models.CharField(max_length=30, default="monthly")

    def __str__(self):
        return self.name


class EmployeeManagement(createdtimestamp_uid, activearchlockedMixin):
    staff = models.OneToOneField("party.Staff", on_delete=models.CASCADE, related_name="employee_management")
    is_employed = models.BooleanField(default=True)
    works_weekends = models.BooleanField(default=False)
    position = models.ForeignKey("party.Occupation", null=True, blank=True, on_delete=models.SET_NULL, related_name="employee_records")
    date_hired = models.DateField(null=True, blank=True)
    date_terminated = models.DateField(null=True, blank=True)
    leave_days_allocated = models.PositiveIntegerField(default=0)
    taxes = models.ManyToManyField("accounts.Tax", blank=True, related_name="employees")
    net_salary = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    overtime_rate = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    salary_rate_period = models.CharField(max_length=30, default="monthly")
    preferred_payment_method = models.CharField(max_length=50, blank=True)
    last_payment_date = models.DateField(null=True, blank=True)
    vacancy = models.ForeignKey(Vacancy, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")

    def __str__(self):
        return str(self.staff)


class EmployeeSalaryRule(createdtimestamp_uid, activearchlockedMixin):
    employee = models.OneToOneField(EmployeeManagement, on_delete=models.CASCADE, related_name="salary_rule")
    notes = models.TextField(blank=True)


class EmployeeSeverancePackage(createdtimestamp_uid, activearchlockedMixin):
    employee = models.OneToOneField(EmployeeManagement, on_delete=models.CASCADE, related_name="severance_package")
    amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)


class Employee_Deduction(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="deductions")
    deduction = models.ForeignKey(Deduction, on_delete=models.CASCADE, related_name="employee_links")

    class Meta:
        unique_together = (("employee", "deduction"),)


class Employee_Benefit(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="benefits")
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE, related_name="employee_links")

    class Meta:
        unique_together = (("employee", "benefit"),)


class EmployeeSkill(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="employee_links")
    proficiency_level = models.CharField(max_length=50, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("employee", "skill"),)


class EmployeeBankDetails(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="bank_details")
    bank = models.ForeignKey("accounts.Bank", on_delete=models.CASCADE, related_name="employee_bank_details")
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=150)
    swift_code = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = (("employee", "bank", "account_number"),)


class LeaveType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_paid = models.BooleanField(default=True)
    rollover_allowed = models.BooleanField(default=False)
    requires_medical_certificate = models.BooleanField(default=False)
    requires_notice_days = models.PositiveIntegerField(default=0)
    required_hr_approval = models.BooleanField(default=False)
    max_days_allowed = models.PositiveIntegerField(default=0)
    department = models.ForeignKey("department.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="leave_types")
    approval_by = models.ManyToManyField("party.Staff", blank=True, related_name="approved_leave_types")

    def __str__(self):
        return self.name


class Leave(createdtimestamp_uid, activearchlockedMixin):
    staff = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="leaves")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="leave_requests")
    start_date = models.DateField()
    end_date = models.DateField()
    requested_days = models.PositiveIntegerField(default=0)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="pending")
    approved_rejected_by = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="processed_leaves")

    @property
    def days(self):
        return (self.end_date - self.start_date).days + 1 if self.start_date and self.end_date else 0


class LeaveBalance(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="balances")
    year = models.PositiveIntegerField()
    allocated_days = models.PositiveIntegerField(default=0)
    used_days = models.PositiveIntegerField(default=0)

    @property
    def remaining_days(self):
        return self.allocated_days - self.used_days


class ScheduledShift(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="scheduled_shifts")
    shift = models.ForeignKey("department.Shift", on_delete=models.PROTECT, related_name="scheduled_employee_shifts")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="scheduled_employee_shifts")
    start_date = models.DateField()
    end_date = models.DateField()
    is_onleave = models.BooleanField(default=False)
    leave = models.ForeignKey(Leave, null=True, blank=True, on_delete=models.SET_NULL, related_name="scheduled_shifts")
    holiday = models.ForeignKey(Holiday, null=True, blank=True, on_delete=models.SET_NULL, related_name="scheduled_shifts")
    notes = models.TextField(blank=True)
    staff = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_schedules")


class Attendance(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="attendance_records")
    branch = models.ForeignKey("department.Branch", on_delete=models.PROTECT, related_name="attendance_records")
    scheduled_shift = models.ForeignKey(ScheduledShift, null=True, blank=True, on_delete=models.SET_NULL, related_name="attendance_records")
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="present")


class OverTime(createdtimestamp_uid, activearchlockedMixin):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="overtimes")
    requested_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    planned_activities = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="pending")
    requested_by = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="requested_overtimes")
    approved_rejected_by = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="processed_overtimes")
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    est_overtime_amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)


class LoanType(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    interest_rate_type = models.CharField(max_length=30, default="simple")
    interest_rate_scheme = models.CharField(max_length=30, default="flat")
    interest_rate_calculation_period = models.CharField(max_length=30, default="monthly")
    interest_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    max_loan_amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    max_repayment_period_months = models.PositiveIntegerField(default=12)
    min_monthly_deduction = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    max_salary_deduction_percentage = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class StaffLoan(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="loans")
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, related_name="loans")
    loan_amount = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    reason = models.TextField(blank=True)
    approval_status = models.CharField(max_length=20, default="pending")
    is_disbursed = models.BooleanField(default=False)
    est_repayment_period_months = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    outstanding_balance = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    deduction = models.ForeignKey(Employee_Deduction, null=True, blank=True, on_delete=models.SET_NULL, related_name="loans")
    status = models.CharField(max_length=20, default="active")
    staff = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_loans")


class Payroll(createdtimestamp_uid, activearchlockedMixin):
    date = models.DateField()
    total_benefits = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    total_gross_salary = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    total_deductions = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    total_net_salary = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    staff = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="payrolls")
    status = models.CharField(max_length=20, default="draft")


class PayrollDetail(createdtimestamp_uid, activearchlockedMixin):
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name="details")
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="payroll_details")
    status = models.CharField(max_length=20, default="draft")
    total_days_worked = models.PositiveIntegerField(default=0)
    total_hours_worked = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_leave_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_absent_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_late_days = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gross_salary = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    taxed_income = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    deduction = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    loandeduction = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    net_salary = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency=default_currency)
    approved_rejected_by = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="processed_payroll_details")

    class Meta:
        unique_together = (("payroll", "employee"),)


class PerformanceEvaluation(createdtimestamp_uid, activearchlockedMixin):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name="evaluations")
    evaluator = models.ForeignKey("party.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="given_evaluations")
    skills_assessed = models.ManyToManyField(Skill, blank=True, related_name="evaluations")
    date = models.DateField()
    score = models.PositiveIntegerField(default=0)
    feedback = models.TextField(blank=True)
