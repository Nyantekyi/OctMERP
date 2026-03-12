from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SkillViewSet, SkillLevelViewSet, CertificationViewSet,
    HolidayViewSet, MeetingSubjectViewSet, MeetingViewSet,
    VacancyViewSet, JobApplicationViewSet,
    BenefitViewSet, DeductionViewSet, EmployeeManagementViewSet,
    EmployeeSkillViewSet, EmployeeBankDetailsViewSet,
    LeaveTypeViewSet, LeaveViewSet, LeaveBalanceViewSet,
    ScheduledShiftViewSet, AttendanceViewSet, OverTimeViewSet,
    LoanTypeViewSet, StaffLoanViewSet,
    PayrollViewSet, PayrollDetailViewSet, PerformanceEvaluationViewSet,
)

app_name = "hr"

router = DefaultRouter()
router.register("skills", SkillViewSet, basename="skill")
router.register("skill-levels", SkillLevelViewSet, basename="skill-level")
router.register("certifications", CertificationViewSet, basename="certification")
router.register("holidays", HolidayViewSet, basename="holiday")
router.register("meeting-subjects", MeetingSubjectViewSet, basename="meeting-subject")
router.register("meetings", MeetingViewSet, basename="meeting")
router.register("vacancies", VacancyViewSet, basename="vacancy")
router.register("applications", JobApplicationViewSet, basename="job-application")
router.register("benefits", BenefitViewSet, basename="benefit")
router.register("deductions", DeductionViewSet, basename="deduction")
router.register("employees", EmployeeManagementViewSet, basename="employee")
router.register("employee-skills", EmployeeSkillViewSet, basename="employee-skill")
router.register("employee-bank-details", EmployeeBankDetailsViewSet, basename="employee-bank")
router.register("leave-types", LeaveTypeViewSet, basename="leave-type")
router.register("leaves", LeaveViewSet, basename="leave")
router.register("leave-balances", LeaveBalanceViewSet, basename="leave-balance")
router.register("scheduled-shifts", ScheduledShiftViewSet, basename="scheduled-shift")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("overtime", OverTimeViewSet, basename="overtime")
router.register("loan-types", LoanTypeViewSet, basename="loan-type")
router.register("loans", StaffLoanViewSet, basename="staff-loan")
router.register("payrolls", PayrollViewSet, basename="payroll")
router.register("payroll-details", PayrollDetailViewSet, basename="payroll-detail")
router.register("evaluations", PerformanceEvaluationViewSet, basename="evaluation")

urlpatterns = [path("", include(router.urls))]

