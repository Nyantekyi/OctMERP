"""apps/hr/serializers.py"""

from apps.common.api import build_model_serializer

from .models import (
    Attendance,
    Benefit,
    Certification,
    Deduction,
    EmployeeBankDetails,
    EmployeeManagement,
    EmployeeSkill,
    Holiday,
    JobApplication,
    Leave,
    LeaveBalance,
    LeaveType,
    LoanType,
    Meeting,
    MeetingSubject,
    OverTime,
    Payroll,
    PayrollDetail,
    PerformanceEvaluation,
    ScheduledShift,
    Skill,
    SkillLevel,
    StaffLoan,
    Vacancy,
)


SkillSerializer = build_model_serializer(
    Skill,
    fields=["id", "name", "description", "is_active", "created_at", "updated_at"],
)

SkillLevelSerializer = build_model_serializer(
    SkillLevel,
    fields=["id", "skill", "level", "description", "created_at", "updated_at"],
)

CertificationSerializer = build_model_serializer(
    Certification,
    fields=["id", "name", "description", "issuing_body", "is_active", "created_at", "updated_at"],
)

HolidaySerializer = build_model_serializer(
    Holiday,
    fields=["id", "name", "date", "is_public", "is_recurring", "description", "country", "is_active", "created_at", "updated_at"],
)

MeetingSubjectSerializer = build_model_serializer(
    MeetingSubject,
    fields=["id", "purpose_type", "subject", "description", "staff", "is_active", "created_at", "updated_at"],
)

MeetingSerializer = build_model_serializer(
    Meeting,
    fields=[
        "id", "room", "subject", "date", "start_time", "end_time",
        "actual_date", "actual_start_time", "actual_end_time",
        "assigned_branch", "assigned_department",
        "attendees", "participants", "status",
        "agenda", "action_items", "minutes", "adjourned",
        "follow_up_date", "rescheduled_from",
        "is_active", "created_at", "updated_at",
    ],
)

VacancySerializer = build_model_serializer(
    Vacancy,
    fields=[
        "id", "title", "department", "description", "requirements",
        "posted_date", "closing_date", "is_filled",
        "is_active", "is_archived", "created_at", "updated_at",
    ],
)

JobApplicationSerializer = build_model_serializer(
    JobApplication,
    fields=[
        "id", "vacancy", "applicant_name", "applicant_email", "applicant_phone",
        "cover_letter", "resume_url", "status",
        "applied_at", "created_at", "updated_at",
    ],
    read_only_fields=("applied_at",),
)

BenefitSerializer = build_model_serializer(
    Benefit,
    fields=[
        "id", "name", "description", "benefit_rate_type", "benefit",
        "frequency", "is_tax_deductable", "currency",
        "min_benefit_amount", "min_benefit_amount_currency",
        "max_benefit_amount", "max_benefit_amount_currency",
        "is_active", "created_at", "updated_at",
    ],
)

DeductionSerializer = build_model_serializer(
    Deduction,
    fields=[
        "id", "name", "description", "deduction_type",
        "deduction_rate_type", "deduction", "frequency", "currency",
        "min_deduction_amount", "min_deduction_amount_currency",
        "max_deduction_amount", "max_deduction_amount_currency",
        "is_active", "created_at", "updated_at",
    ],
)

EmployeeManagementSerializer = build_model_serializer(
    EmployeeManagement,
    fields=[
        "id", "staff", "is_employed", "works_weekends",
        "position", "date_hired", "date_terminated",
        "leave_days_allocated", "taxes",
        "net_salary", "net_salary_currency",
        "overtime_rate", "overtime_rate_currency",
        "salary_rate_period",
        "preferred_payment_method", "last_payment_date",
        "vacancy",
        "is_active", "created_at", "updated_at",
    ],
)

LeaveTypeSerializer = build_model_serializer(
    LeaveType,
    fields=[
        "id", "name", "description", "is_paid", "rollover_allowed",
        "requires_medical_certificate", "requires_notice_days",
        "required_hr_approval", "max_days_allowed", "department",
        "approval_by",
        "is_active", "created_at", "updated_at",
    ],
)

LeaveSerializer = build_model_serializer(
    Leave,
    fields=[
        "id", "staff", "leave_type", "start_date", "end_date",
        "requested_days", "days", "reason", "status",
        "approved_rejected_by",
        "is_active", "created_at", "updated_at",
    ],
    read_only_fields=("days",),
)

LeaveBalanceSerializer = build_model_serializer(
    LeaveBalance,
    fields=[
        "id", "employee", "leave_type", "year",
        "allocated_days", "used_days", "remaining_days",
        "created_at", "updated_at",
    ],
    read_only_fields=("remaining_days",),
)

ScheduledShiftSerializer = build_model_serializer(
    ScheduledShift,
    fields=[
        "id", "employee", "shift", "branch",
        "start_date", "end_date", "is_onleave", "leave",
        "holiday", "notes", "staff",
        "is_active", "created_at", "updated_at",
    ],
)

AttendanceSerializer = build_model_serializer(
    Attendance,
    fields=[
        "id", "employee", "branch", "scheduled_shift",
        "date", "check_in", "check_out",
        "break_start", "break_end", "status",
        "created_at", "updated_at",
    ],
)

OverTimeSerializer = build_model_serializer(
    OverTime,
    fields=[
        "id", "attendance", "requested_hours", "planned_activities",
        "status", "requested_by", "approved_rejected_by",
        "start_time", "end_time", "total_hours",
        "est_overtime_amount", "est_overtime_amount_currency",
        "created_at", "updated_at",
    ],
    read_only_fields=("total_hours",),
)

LoanTypeSerializer = build_model_serializer(
    LoanType,
    fields=[
        "id", "name", "description",
        "interest_rate_type", "interest_rate_scheme",
        "interest_rate_calculation_period", "interest_rate",
        "max_loan_amount", "max_loan_amount_currency",
        "max_repayment_period_months", "min_monthly_deduction",
        "max_salary_deduction_percentage",
        "is_active", "created_at", "updated_at",
    ],
)

StaffLoanSerializer = build_model_serializer(
    StaffLoan,
    fields=[
        "id", "employee", "loan_type", "loan_amount", "loan_amount_currency",
        "reason", "approval_status", "is_disbursed",
        "est_repayment_period_months", "start_date", "end_date",
        "outstanding_balance", "deduction", "status", "staff",
        "created_at", "updated_at",
    ],
    read_only_fields=("outstanding_balance",),
)

PayrollSerializer = build_model_serializer(
    Payroll,
    fields=[
        "id", "date",
        "total_benefits", "total_benefits_currency",
        "total_gross_salary", "total_gross_salary_currency",
        "total_deductions", "total_deductions_currency",
        "total_net_salary", "total_net_salary_currency",
        "staff", "status",
        "created_at", "updated_at",
    ],
)

PayrollDetailSerializer = build_model_serializer(
    PayrollDetail,
    fields=[
        "id", "payroll", "employee", "status",
        "total_days_worked", "total_hours_worked",
        "total_overtime_hours", "total_leave_days",
        "total_absent_days", "total_late_days",
        "gross_salary", "gross_salary_currency",
        "taxed_income", "taxed_income_currency",
        "deduction", "deduction_currency",
        "loandeduction", "loandeduction_currency",
        "net_salary", "net_salary_currency",
        "approved_rejected_by",
        "created_at", "updated_at",
    ],
)

PerformanceEvaluationSerializer = build_model_serializer(
    PerformanceEvaluation,
    fields=[
        "id", "employee", "evaluator", "skills_assessed",
        "date", "score", "feedback",
        "created_at", "updated_at",
    ],
)

EmployeeSkillSerializer = build_model_serializer(
    EmployeeSkill,
    fields=[
        "id", "employee", "skill", "proficiency_level",
        "years_of_experience", "certificates",
        "created_at", "updated_at",
    ],
)

EmployeeBankDetailsSerializer = build_model_serializer(
    EmployeeBankDetails,
    fields=[
        "id", "employee", "bank", "account_number", "account_name", "swift_code",
        "created_at", "updated_at",
    ],
)
