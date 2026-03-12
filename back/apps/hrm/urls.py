from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.hrm.api.views import AttendanceViewSet, BenefitViewSet, DeductionViewSet, EmployeeBankDetailsViewSet, EmployeeBenefitViewSet, EmployeeDeductionViewSet, EmployeeManagementViewSet, EmployeeSalaryRuleViewSet, EmployeeSeverancePackageViewSet, EmployeeSkillViewSet, HolidayViewSet, LeaveBalanceViewSet, LeaveTypeViewSet, LeaveViewSet, LoanTypeViewSet, MeetingSubjectViewSet, MeetingViewSet, OverTimeViewSet, PayrollDetailViewSet, PayrollViewSet, PerformanceEvaluationViewSet, ScheduledShiftViewSet, SkillViewSet, StaffLoanViewSet, VacancyViewSet

router = DefaultRouter()
router.register("skills", SkillViewSet, basename="skill")
router.register("holidays", HolidayViewSet, basename="holiday")
router.register("meeting-subjects", MeetingSubjectViewSet, basename="meeting-subject")
router.register("meetings", MeetingViewSet, basename="meeting")
router.register("vacancies", VacancyViewSet, basename="vacancy")
router.register("deductions", DeductionViewSet, basename="deduction")
router.register("benefits", BenefitViewSet, basename="benefit")
router.register("employees", EmployeeManagementViewSet, basename="employee")
router.register("employee-salary-rules", EmployeeSalaryRuleViewSet, basename="employee-salary-rule")
router.register("employee-severance-packages", EmployeeSeverancePackageViewSet, basename="employee-severance-package")
router.register("employee-deductions", EmployeeDeductionViewSet, basename="employee-deduction")
router.register("employee-benefits", EmployeeBenefitViewSet, basename="employee-benefit")
router.register("employee-skills", EmployeeSkillViewSet, basename="employee-skill")
router.register("employee-bank-details", EmployeeBankDetailsViewSet, basename="employee-bank-detail")
router.register("leave-types", LeaveTypeViewSet, basename="leave-type")
router.register("leaves", LeaveViewSet, basename="leave")
router.register("leave-balances", LeaveBalanceViewSet, basename="leave-balance")
router.register("scheduled-shifts", ScheduledShiftViewSet, basename="scheduled-shift")
router.register("attendance", AttendanceViewSet, basename="attendance")
router.register("overtime", OverTimeViewSet, basename="overtime")
router.register("loan-types", LoanTypeViewSet, basename="loan-type")
router.register("staff-loans", StaffLoanViewSet, basename="staff-loan")
router.register("payrolls", PayrollViewSet, basename="payroll")
router.register("payroll-details", PayrollDetailViewSet, basename="payroll-detail")
router.register("performance-evaluations", PerformanceEvaluationViewSet, basename="performance-evaluation")

urlpatterns = [path("", include(router.urls))]
