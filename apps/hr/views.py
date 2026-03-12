"""
apps/hr/views.py
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsTenantUser, IsManager
from .models import (
    Skill, SkillLevel, EmployeeSkill, Certification, Holiday,
    MeetingSubject, Meeting, Vacancy, JobApplication,
    Benefit, Deduction, EmployeeManagement,
    EmployeeDeduction, EmployeeBenefit, EmployeeBankDetails,
    LeaveType, Leave, LeaveBalance,
    ScheduledShift, Attendance, OverTime, LoanType, StaffLoan,
    Payroll, PayrollDetail, PerformanceEvaluation,
)
from .serializers import (
    SkillSerializer, SkillLevelSerializer, CertificationSerializer,
    HolidaySerializer, MeetingSubjectSerializer, MeetingSerializer,
    VacancySerializer, JobApplicationSerializer,
    BenefitSerializer, DeductionSerializer, EmployeeManagementSerializer,
    EmployeeSkillSerializer, EmployeeBankDetailsSerializer,
    LeaveTypeSerializer, LeaveSerializer, LeaveBalanceSerializer,
    ScheduledShiftSerializer, AttendanceSerializer, OverTimeSerializer,
    LoanTypeSerializer, StaffLoanSerializer,
    PayrollSerializer, PayrollDetailSerializer, PerformanceEvaluationSerializer,
)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["is_active"]


class SkillLevelViewSet(viewsets.ModelViewSet):
    queryset = SkillLevel.objects.select_related("skill")
    serializer_class = SkillLevelSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["skill"]


class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]


class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["is_public", "country"]
    ordering_fields = ["date"]


class MeetingSubjectViewSet(viewsets.ModelViewSet):
    queryset = MeetingSubject.objects.all()
    serializer_class = MeetingSubjectSerializer
    permission_classes = [IsTenantUser]


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.select_related("room", "subject")
    serializer_class = MeetingSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status"]
    ordering_fields = ["date", "created_at"]


class VacancyViewSet(viewsets.ModelViewSet):
    queryset = Vacancy.objects.select_related("department")
    serializer_class = VacancySerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["department", "is_filled", "is_active"]
    search_fields = ["title"]


class JobApplicationViewSet(viewsets.ModelViewSet):
    queryset = JobApplication.objects.select_related("vacancy")
    serializer_class = JobApplicationSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["vacancy", "status"]


class BenefitViewSet(viewsets.ModelViewSet):
    queryset = Benefit.objects.all()
    serializer_class = BenefitSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["benefit_rate_type", "frequency", "is_active"]


class DeductionViewSet(viewsets.ModelViewSet):
    queryset = Deduction.objects.all()
    serializer_class = DeductionSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["deduction_type", "frequency", "is_active"]


class EmployeeManagementViewSet(viewsets.ModelViewSet):
    queryset = EmployeeManagement.objects.select_related("staff", "position", "vacancy")
    serializer_class = EmployeeManagementSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["is_employed", "salary_rate_period", "is_active"]
    search_fields = ["staff__user__first_name", "staff__user__last_name"]

    @action(detail=True, methods=["get"])
    def attendance(self, request, pk=None):
        emp = self.get_object()
        qs = Attendance.objects.filter(employee=emp).order_by("-date")
        serializer = AttendanceSerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["get"])
    def leaves(self, request, pk=None):
        emp = self.get_object()
        qs = Leave.objects.filter(staff=emp).order_by("-start_date")
        serializer = LeaveSerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=["get"])
    def loans(self, request, pk=None):
        emp = self.get_object()
        qs = StaffLoan.objects.filter(employee=emp).order_by("-created_at")
        serializer = StaffLoanSerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})


class EmployeeSkillViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSkill.objects.select_related("employee", "skill")
    serializer_class = EmployeeSkillSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "skill", "proficiency_level"]


class EmployeeBankDetailsViewSet(viewsets.ModelViewSet):
    queryset = EmployeeBankDetails.objects.select_related("employee", "bank")
    serializer_class = EmployeeBankDetailsSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "bank"]


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["is_paid", "department", "is_active"]
    search_fields = ["name"]


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.select_related("staff", "leave_type")
    serializer_class = LeaveSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "leave_type", "staff"]
    ordering_fields = ["start_date", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.approved_rejected_by = getattr(request.user, "staff_profile", None)
        obj.save()
        return Response({"success": True, "data": LeaveSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        obj = self.get_object()
        obj.status = "rejected"
        obj.save()
        return Response({"success": True, "data": LeaveSerializer(obj).data})


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.select_related("employee", "leave_type")
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "leave_type", "year"]


class ScheduledShiftViewSet(viewsets.ModelViewSet):
    queryset = ScheduledShift.objects.select_related("employee", "shift", "branch")
    serializer_class = ScheduledShiftSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "branch", "shift", "is_onleave"]
    ordering_fields = ["start_date"]


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("employee", "branch")
    serializer_class = AttendanceSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "branch", "status", "date"]
    ordering_fields = ["date", "check_in"]


class OverTimeViewSet(viewsets.ModelViewSet):
    queryset = OverTime.objects.select_related("attendance")
    serializer_class = OverTimeSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status", "requested_by"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.approved_rejected_by = getattr(request.user, "staff_profile", None)
        obj.save()
        return Response({"success": True, "data": OverTimeSerializer(obj).data})


class LoanTypeViewSet(viewsets.ModelViewSet):
    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer
    permission_classes = [IsTenantUser]
    search_fields = ["name"]
    filterset_fields = ["is_active"]


class StaffLoanViewSet(viewsets.ModelViewSet):
    queryset = StaffLoan.objects.select_related("employee", "loan_type")
    serializer_class = StaffLoanSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "status", "approval_status"]
    ordering_fields = ["created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.approval_status = "approved"
        obj.save()
        return Response({"success": True, "data": StaffLoanSerializer(obj).data})


class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["status"]
    ordering_fields = ["date", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()
        obj.status = "approved"
        obj.save()
        return Response({"success": True, "data": PayrollSerializer(obj).data})

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        obj = self.get_object()
        obj.status = "paid"
        obj.save()
        return Response({"success": True, "data": PayrollSerializer(obj).data})


class PayrollDetailViewSet(viewsets.ModelViewSet):
    queryset = PayrollDetail.objects.select_related("payroll", "employee")
    serializer_class = PayrollDetailSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["payroll", "employee", "status"]


class PerformanceEvaluationViewSet(viewsets.ModelViewSet):
    queryset = PerformanceEvaluation.objects.select_related("employee", "evaluator")
    serializer_class = PerformanceEvaluationSerializer
    permission_classes = [IsTenantUser]
    filterset_fields = ["employee", "evaluator"]
    ordering_fields = ["date", "created_at"]
