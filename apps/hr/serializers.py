"""
apps/hr/serializers.py
"""

from rest_framework import serializers
from .models import (
    Skill, SkillLevel, EmployeeSkill, Certification, Holiday,
    MeetingSubject, Meeting, Vacancy, JobApplication,
    Benefit, Deduction, EmployeeManagement, EmployeeSalaryRule,
    EmployeeSeverancePackage, EmployeeDeduction, EmployeeBenefit,
    EmployeeBankDetails, LeaveType, Leave, LeaveBalance,
    ScheduledShift, Attendance, OverTime, LoanType, StaffLoan,
    Payroll, PayrollDetail, PerformanceEvaluation,
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SkillLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillLevel
        fields = ["id", "skill", "level", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ["id", "name", "description", "issuing_body", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ["id", "name", "date", "is_public", "is_recurring", "description", "country", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MeetingSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingSubject
        fields = ["id", "purpose_type", "subject", "description", "staff", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            "id", "room", "subject", "date", "start_time", "end_time",
            "actual_date", "actual_start_time", "actual_end_time",
            "assigned_branch", "assigned_department",
            "attendees", "participants", "status",
            "agenda", "action_items", "minutes", "adjourned",
            "follow_up_date", "rescheduled_from",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = [
            "id", "title", "department", "description", "requirements",
            "posted_date", "closing_date", "is_filled",
            "is_active", "is_archived", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = [
            "id", "vacancy", "applicant_name", "applicant_email", "applicant_phone",
            "cover_letter", "resume_url", "status",
            "applied_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "applied_at", "created_at", "updated_at"]


class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefit
        fields = [
            "id", "name", "description", "benefit_rate_type", "benefit",
            "frequency", "is_tax_deductable", "currency",
            "min_benefit_amount", "min_benefit_amount_currency",
            "max_benefit_amount", "max_benefit_amount_currency",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deduction
        fields = [
            "id", "name", "description", "deduction_type",
            "deduction_rate_type", "deduction", "frequency", "currency",
            "min_deduction_amount", "min_deduction_amount_currency",
            "max_deduction_amount", "max_deduction_amount_currency",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmployeeManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeManagement
        fields = [
            "id", "staff", "is_employed", "works_weekends",
            "position", "date_hired", "date_terminated",
            "leave_days_allocated", "taxes",
            "net_salary", "net_salary_currency",
            "overtime_rate", "overtime_rate_currency",
            "salary_rate_period",
            "preferred_payment_method", "last_payment_date",
            "vacancy",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = [
            "id", "name", "description", "is_paid", "rollover_allowed",
            "requires_medical_certificate", "requires_notice_days",
            "required_hr_approval", "max_days_allowed", "department",
            "approval_by",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = [
            "id", "staff", "leave_type", "start_date", "end_date",
            "requested_days", "days", "reason", "status",
            "approved_rejected_by",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "days", "created_at", "updated_at"]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = [
            "id", "employee", "leave_type", "year",
            "allocated_days", "used_days", "remaining_days",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "remaining_days", "created_at", "updated_at"]


class ScheduledShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledShift
        fields = [
            "id", "employee", "shift", "branch",
            "start_date", "end_date", "is_onleave", "leave",
            "holiday", "notes", "staff",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = [
            "id", "employee", "branch", "scheduled_shift",
            "date", "check_in", "check_out",
            "break_start", "break_end", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OverTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverTime
        fields = [
            "id", "attendance", "requested_hours", "planned_activities",
            "status", "requested_by", "approved_rejected_by",
            "start_time", "end_time", "total_hours",
            "est_overtime_amount", "est_overtime_amount_currency",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_hours", "created_at", "updated_at"]


class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = [
            "id", "name", "description",
            "interest_rate_type", "interest_rate_scheme",
            "interest_rate_calculation_period", "interest_rate",
            "max_loan_amount", "max_loan_amount_currency",
            "max_repayment_period_months", "min_monthly_deduction",
            "max_salary_deduction_percentage",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StaffLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffLoan
        fields = [
            "id", "employee", "loan_type", "loan_amount", "loan_amount_currency",
            "reason", "approval_status", "is_disbursed",
            "est_repayment_period_months", "start_date", "end_date",
            "outstanding_balance", "deduction", "status", "staff",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "outstanding_balance", "created_at", "updated_at"]


class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = [
            "id", "date",
            "total_benefits", "total_benefits_currency",
            "total_gross_salary", "total_gross_salary_currency",
            "total_deductions", "total_deductions_currency",
            "total_net_salary", "total_net_salary_currency",
            "staff", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PayrollDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDetail
        fields = [
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
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PerformanceEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceEvaluation
        fields = [
            "id", "employee", "evaluator", "skills_assessed",
            "date", "score", "feedback",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmployeeSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkill
        fields = [
            "id", "employee", "skill", "proficiency_level",
            "years_of_experience", "certificates",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmployeeBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeBankDetails
        fields = [
            "id", "employee", "bank", "account_number", "account_name", "swift_code",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
