"""apps/hr/views.py"""

from rest_framework.response import Response

from apps.common.api import build_action_route, build_model_viewset
from apps.common.permissions import IsTenantUser

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
from .serializers import (
    AttendanceSerializer,
    BenefitSerializer,
    CertificationSerializer,
    DeductionSerializer,
    EmployeeBankDetailsSerializer,
    EmployeeManagementSerializer,
    EmployeeSkillSerializer,
    HolidaySerializer,
    JobApplicationSerializer,
    LeaveBalanceSerializer,
    LeaveSerializer,
    LeaveTypeSerializer,
    LoanTypeSerializer,
    MeetingSerializer,
    MeetingSubjectSerializer,
    OverTimeSerializer,
    PayrollDetailSerializer,
    PayrollSerializer,
    PerformanceEvaluationSerializer,
    ScheduledShiftSerializer,
    SkillLevelSerializer,
    SkillSerializer,
    StaffLoanSerializer,
    VacancySerializer,
)


def _employee_attendance(self, request, *args, **kwargs):
    employee = self.get_object()
    queryset = Attendance.objects.filter(employee=employee).order_by("-date")
    serializer = AttendanceSerializer(queryset, many=True, context=self.get_serializer_context())
    return Response({"success": True, "data": serializer.data})


def _employee_leaves(self, request, *args, **kwargs):
    employee = self.get_object()
    queryset = Leave.objects.filter(staff=employee).order_by("-start_date")
    serializer = LeaveSerializer(queryset, many=True, context=self.get_serializer_context())
    return Response({"success": True, "data": serializer.data})


def _employee_loans(self, request, *args, **kwargs):
    employee = self.get_object()
    queryset = StaffLoan.objects.filter(employee=employee).order_by("-created_at")
    serializer = StaffLoanSerializer(queryset, many=True, context=self.get_serializer_context())
    return Response({"success": True, "data": serializer.data})


def _approve_leave(self, request, *args, **kwargs):
    leave = self.get_object()
    leave.status = "approved"
    leave.approved_rejected_by = getattr(request.user, "staff_profile", None)
    leave.save()
    return Response({"success": True, "data": LeaveSerializer(leave, context=self.get_serializer_context()).data})


def _reject_leave(self, request, *args, **kwargs):
    leave = self.get_object()
    leave.status = "rejected"
    leave.save()
    return Response({"success": True, "data": LeaveSerializer(leave, context=self.get_serializer_context()).data})


def _approve_overtime(self, request, *args, **kwargs):
    overtime = self.get_object()
    overtime.status = "approved"
    overtime.approved_rejected_by = getattr(request.user, "staff_profile", None)
    overtime.save()
    return Response({"success": True, "data": OverTimeSerializer(overtime, context=self.get_serializer_context()).data})


def _approve_staff_loan(self, request, *args, **kwargs):
    loan = self.get_object()
    loan.approval_status = "approved"
    loan.save()
    return Response({"success": True, "data": StaffLoanSerializer(loan, context=self.get_serializer_context()).data})


def _approve_payroll(self, request, *args, **kwargs):
    payroll = self.get_object()
    payroll.status = "approved"
    payroll.save()
    return Response({"success": True, "data": PayrollSerializer(payroll, context=self.get_serializer_context()).data})


def _process_payroll(self, request, *args, **kwargs):
    payroll = self.get_object()
    payroll.status = "paid"
    payroll.save()
    return Response({"success": True, "data": PayrollSerializer(payroll, context=self.get_serializer_context()).data})


SkillViewSet = build_model_viewset(
    Skill,
    SkillSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["is_active"],
)

SkillLevelViewSet = build_model_viewset(
    SkillLevel,
    SkillLevelSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["skill"],
    select_related_fields=["skill"],
)

CertificationViewSet = build_model_viewset(
    Certification,
    CertificationSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
)

HolidayViewSet = build_model_viewset(
    Holiday,
    HolidaySerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["is_public", "country"],
    ordering_fields=["date"],
)

MeetingSubjectViewSet = build_model_viewset(
    MeetingSubject,
    MeetingSubjectSerializer,
    permission_classes=[IsTenantUser],
)

MeetingViewSet = build_model_viewset(
    Meeting,
    MeetingSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status"],
    ordering_fields=["date", "created_at"],
    select_related_fields=["room", "subject"],
)

VacancyViewSet = build_model_viewset(
    Vacancy,
    VacancySerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["department", "is_filled", "is_active"],
    search_fields=["title"],
    select_related_fields=["department"],
)

JobApplicationViewSet = build_model_viewset(
    JobApplication,
    JobApplicationSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["vacancy", "status"],
    select_related_fields=["vacancy"],
)

BenefitViewSet = build_model_viewset(
    Benefit,
    BenefitSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["benefit_rate_type", "frequency", "is_active"],
)

DeductionViewSet = build_model_viewset(
    Deduction,
    DeductionSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["deduction_type", "frequency", "is_active"],
)

EmployeeManagementViewSet = build_model_viewset(
    EmployeeManagement,
    EmployeeManagementSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["is_employed", "salary_rate_period", "is_active"],
    search_fields=["staff__user__first_name", "staff__user__last_name"],
    select_related_fields=["staff", "position", "vacancy"],
    extra_routes={
        "attendance": build_action_route("attendance", _employee_attendance, methods=("get",), detail=True),
        "leaves": build_action_route("leaves", _employee_leaves, methods=("get",), detail=True),
        "loans": build_action_route("loans", _employee_loans, methods=("get",), detail=True),
    },
)

EmployeeSkillViewSet = build_model_viewset(
    EmployeeSkill,
    EmployeeSkillSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "skill", "proficiency_level"],
    select_related_fields=["employee", "skill"],
)

EmployeeBankDetailsViewSet = build_model_viewset(
    EmployeeBankDetails,
    EmployeeBankDetailsSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "bank"],
    select_related_fields=["employee", "bank"],
)

LeaveTypeViewSet = build_model_viewset(
    LeaveType,
    LeaveTypeSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["is_paid", "department", "is_active"],
    search_fields=["name"],
)

LeaveViewSet = build_model_viewset(
    Leave,
    LeaveSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "leave_type", "staff"],
    ordering_fields=["start_date", "created_at"],
    select_related_fields=["staff", "leave_type"],
    extra_routes={
        "approve": build_action_route("approve", _approve_leave, methods=("post",), detail=True),
        "reject": build_action_route("reject", _reject_leave, methods=("post",), detail=True),
    },
)

LeaveBalanceViewSet = build_model_viewset(
    LeaveBalance,
    LeaveBalanceSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "leave_type", "year"],
    select_related_fields=["employee", "leave_type"],
)

ScheduledShiftViewSet = build_model_viewset(
    ScheduledShift,
    ScheduledShiftSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "branch", "shift", "is_onleave"],
    ordering_fields=["start_date"],
    select_related_fields=["employee", "shift", "branch"],
)

AttendanceViewSet = build_model_viewset(
    Attendance,
    AttendanceSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "branch", "status", "date"],
    ordering_fields=["date", "check_in"],
    select_related_fields=["employee", "branch"],
)

OverTimeViewSet = build_model_viewset(
    OverTime,
    OverTimeSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status", "requested_by"],
    select_related_fields=["attendance"],
    extra_routes={
        "approve": build_action_route("approve", _approve_overtime, methods=("post",), detail=True),
    },
)

LoanTypeViewSet = build_model_viewset(
    LoanType,
    LoanTypeSerializer,
    permission_classes=[IsTenantUser],
    search_fields=["name"],
    filterset_fields=["is_active"],
)

StaffLoanViewSet = build_model_viewset(
    StaffLoan,
    StaffLoanSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "status", "approval_status"],
    ordering_fields=["created_at"],
    select_related_fields=["employee", "loan_type"],
    extra_routes={
        "approve": build_action_route("approve", _approve_staff_loan, methods=("post",), detail=True),
    },
)

PayrollViewSet = build_model_viewset(
    Payroll,
    PayrollSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["status"],
    ordering_fields=["date", "created_at"],
    extra_routes={
        "approve": build_action_route("approve", _approve_payroll, methods=("post",), detail=True),
        "process": build_action_route("process", _process_payroll, methods=("post",), detail=True),
    },
)

PayrollDetailViewSet = build_model_viewset(
    PayrollDetail,
    PayrollDetailSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["payroll", "employee", "status"],
    select_related_fields=["payroll", "employee"],
)

PerformanceEvaluationViewSet = build_model_viewset(
    PerformanceEvaluation,
    PerformanceEvaluationSerializer,
    permission_classes=[IsTenantUser],
    filterset_fields=["employee", "evaluator"],
    ordering_fields=["date", "created_at"],
    select_related_fields=["employee", "evaluator"],
)
