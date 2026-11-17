from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from .models import User, AuditLog, SystemSetting
from .decorators import role_required
from courses.models import Course
from internships.models import (
    InternshipProgram, InternshipBatch, InternshipEnrollment, InternshipApplication,
    InternshipDocument, DailyWorkTracking
)
from students.models import StudentProfile
from tasks.models import Task, TaskAssignment, DailyReport
from learning.models import Enrollment
from examinations.models import ExamAttempt
from payments.models import Payment, FeeInstallment
from attendance.models import Attendance
from projects.models import ProjectMember, ProjectSubmission
from certificates.models import Certificate


def home_view(request):
    featured_courses = Course.objects.filter(course_status='Active')[:6]
    internship_programs = InternshipProgram.objects.filter(status='Active')[:6]
    stats = {
        'total_courses': Course.objects.count(),
        'total_students': User.objects.filter(role__in=['student', 'intern']).count(),
        'total_internships': InternshipProgram.objects.count(),
        'total_batches': InternshipBatch.objects.count(),
    }
    return render(request, 'public/home.html', {
        'courses': featured_courses,
        'internships': internship_programs,
        'stats': stats,
    })


def about_view(request):
    return render(request, 'public/about.html')


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for contacting us! Our team will get back to you shortly.')
        return redirect('contact')
    return render(request, 'public/contact.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            AuditLog.objects.create(user=user, action="User Login", module="Authentication", ip_address=request.META.get('REMOTE_ADDR'))
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role', 'student')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )

        # Create StudentProfile if student or intern
        if role in ['student', 'intern']:
            code = f"STU-{user.id:04d}"
            StudentProfile.objects.create(
                user=user,
                student_code=code,
                qualification=request.POST.get('qualification', ''),
                college_name=request.POST.get('college_name', ''),
                passing_year=int(request.POST.get('passing_year')) if request.POST.get('passing_year') else None
            )

        AuditLog.objects.create(user=user, action="User Registration", module="Authentication")
        messages.success(request, 'Registration successful! You can now log in.')
        return redirect('login')

    return render(request, 'accounts/register.html')


@login_required
def logout_view(request):
    AuditLog.objects.create(user=request.user, action="User Logout", module="Authentication")
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def student_dashboard_view(request):
    user = request.user
    is_staff = user.is_superuser or user.role in ['super_admin', 'admin', 'hr', 'trainer']

    # Allow staff to view any student's dashboard
    target_user = user
    student_id = request.GET.get('student_id')
    if is_staff and student_id:
        target_user = User.objects.filter(id=student_id).first() or user
    elif is_staff and user.role in ['super_admin', 'admin']:
        target_user = User.objects.filter(role='student').first() or user

    today = timezone.localdate()

    # ==========================================
    # NEW ATTENDANCE DATA & MONTHLY PERFORMANCE
    # ==========================================
    today_attendance = Attendance.objects.filter(student=target_user, attendance_date=today).first()

    month_records = Attendance.objects.filter(
        student=target_user,
        attendance_date__year=today.year,
        attendance_date__month=today.month
    )
    present_days = month_records.filter(status='present').count()
    late_days = month_records.filter(status='late').count()
    absent_days = month_records.filter(status='absent').count()
    leave_days = month_records.filter(status__in=['leave', 'holiday', 'weekly_off']).count()
    total_countable = present_days + late_days + absent_days
    attendance_pct = round((present_days + (late_days * 0.8)) / total_countable * 100) if total_countable > 0 else 0

    recent_attendances = Attendance.objects.filter(student=target_user).order_by('-attendance_date')[:6]

    # Courses & Learning
    enrollments = Enrollment.objects.filter(student=target_user).select_related('course')
    active_courses_count = enrollments.filter(enrollment_status='Active').count()
    completed_courses_count = enrollments.filter(enrollment_status='Completed').count()

    # Exams
    recent_attempts = ExamAttempt.objects.filter(student=target_user).select_related('exam').order_by('-start_time')[:5]
    passed_exams_count = ExamAttempt.objects.filter(student=target_user, result_status='Passed').count()

    # Capstone Projects
    project_memberships = ProjectMember.objects.filter(student=target_user).select_related('project')[:4]

    # Certificates
    certificates = Certificate.objects.filter(student=target_user).order_by('-issue_date')[:4]
    certificates_count = Certificate.objects.filter(student=target_user).count()

    # ==========================================
    # FEES & ONLINE PAYMENTS DATA
    # ==========================================
    student_payments = Payment.objects.filter(student=target_user).select_related('course').order_by('-payment_date')
    total_paid = student_payments.filter(payment_status='Success').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_course_fees = sum([e.course.course_fees for e in enrollments if e.course and e.course.course_fees]) or Decimal('0.00')
    pending_fee = max(Decimal('0.00'), total_course_fees - total_paid)
    fee_percentage = int(round((total_paid / total_course_fees) * 100)) if total_course_fees > 0 else (100 if total_paid > 0 else 0)
    fee_installments = FeeInstallment.objects.filter(student=target_user).select_related('course').order_by('due_date')
    next_installment = fee_installments.filter(status__in=['Pending', 'Partially Paid', 'Overdue']).first()
    all_courses = Course.objects.all()

    all_students = []
    if is_staff:
        all_students = User.objects.filter(role__in=['student', 'intern']).order_by('first_name', 'username')

    context = {
        'target_user': target_user,
        'today': today,
        'today_attendance': today_attendance,
        'present_days': present_days,
        'late_days': late_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'total_countable': total_countable,
        'attendance_pct': attendance_pct,
        'recent_attendances': recent_attendances,
        'enrollments': enrollments,
        'active_courses_count': active_courses_count,
        'completed_courses_count': completed_courses_count,
        'recent_attempts': recent_attempts,
        'passed_exams_count': passed_exams_count,
        'project_memberships': project_memberships,
        'certificates': certificates,
        'certificates_count': certificates_count,
        'student_payments': student_payments,
        'recent_payments': student_payments[:5],
        'total_paid': total_paid,
        'total_course_fees': total_course_fees,
        'pending_fee': pending_fee,
        'fee_percentage': fee_percentage,
        'fee_installments': fee_installments,
        'next_installment': next_installment,
        'all_courses': all_courses,
        'is_staff': is_staff,
        'all_students': all_students,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@login_required
def intern_dashboard_view(request):
    user = request.user
    is_staff = user.is_superuser or user.role in ['super_admin', 'admin', 'hr', 'trainer', 'team_leader']

    target_user = user
    student_id = request.GET.get('student_id')
    if is_staff and student_id:
        target_user = User.objects.filter(id=student_id).first() or user
    elif is_staff and user.role in ['super_admin', 'admin']:
        target_user = User.objects.filter(role='intern').first() or user

    today = timezone.localdate()

    # Intern enrollment & batch
    intern_enrollments = InternshipEnrollment.objects.filter(student=target_user).select_related(
        'program', 'batch', 'batch__trainer', 'batch__team_leader'
    )
    active_enrollment = intern_enrollments.filter(completion_status='Active').first() or intern_enrollments.first()

    # Daily Work Tracking & Today's Attendance
    today_attendance = Attendance.objects.filter(student=target_user, attendance_date=today).first()
    today_tracking = DailyWorkTracking.objects.filter(student=target_user, date=today).first()

    month_records = Attendance.objects.filter(
        student=target_user,
        attendance_date__year=today.year,
        attendance_date__month=today.month
    )
    present_days = month_records.filter(status='present').count()
    late_days = month_records.filter(status='late').count()
    absent_days = month_records.filter(status='absent').count()
    total_countable = present_days + late_days + absent_days
    attendance_pct = round((present_days + (late_days * 0.8)) / total_countable * 100) if total_countable > 0 else 0
    recent_attendances = Attendance.objects.filter(student=target_user).order_by('-attendance_date')[:5]

    # Tasks assigned
    assignments = TaskAssignment.objects.filter(student=target_user).select_related('task').order_by('-assigned_at')[:6]
    pending_tasks_count = TaskAssignment.objects.filter(student=target_user, submission_status='Pending').count()
    completed_tasks_count = TaskAssignment.objects.filter(student=target_user, submission_status__in=['Submitted', 'Reviewed']).count()

    # Daily Reports
    reports = DailyReport.objects.filter(student=target_user).order_by('-report_date')[:5]
    today_report = DailyReport.objects.filter(student=target_user, report_date=today).first()

    # Documents
    documents = InternshipDocument.objects.filter(student=target_user)
    verified_docs = documents.filter(verification_status='Verified').count()

    all_students = []
    if is_staff:
        all_students = User.objects.filter(role__in=['intern', 'student']).order_by('first_name', 'username')

    context = {
        'target_user': target_user,
        'today': today,
        'intern_enrollments': intern_enrollments,
        'active_enrollment': active_enrollment,
        'today_attendance': today_attendance,
        'today_tracking': today_tracking,
        'present_days': present_days,
        'late_days': late_days,
        'absent_days': absent_days,
        'total_countable': total_countable,
        'attendance_pct': attendance_pct,
        'recent_attendances': recent_attendances,
        'assignments': assignments,
        'pending_tasks_count': pending_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'reports': reports,
        'today_report': today_report,
        'documents': documents,
        'verified_docs': verified_docs,
        'is_staff': is_staff,
        'all_students': all_students,
    }
    return render(request, 'accounts/intern_dashboard.html', context)


@login_required
def dashboard_view(request):
    user = request.user
    role = user.role

    if user.is_superuser or role in ['super_admin', 'admin']:
        return redirect('admin_panel')

    # Student Dashboard
    if role == 'student':
        return student_dashboard_view(request)

    # Intern Dashboard
    elif role == 'intern':
        return intern_dashboard_view(request)

    # Trainer / Team Leader Dashboard
    elif role in ['trainer', 'team_leader']:
        batches = InternshipBatch.objects.filter(status='Active')
        if role == 'team_leader':
            batches = batches.filter(team_leader=user)
        else:
            batches = batches.filter(trainer=user)
        recent_tasks = Task.objects.filter(assigned_by=user)[:5]
        pending_reports = DailyReport.objects.filter(team_leader_remarks='')[:5]
        context = {
            'batches': batches,
            'tasks': recent_tasks,
            'pending_reports': pending_reports,
        }
        return render(request, 'accounts/trainer_dashboard.html', context)

    # Accountant Dashboard
    elif role == 'accountant':
        recent_payments = Payment.objects.all().order_by('-payment_date')[:10]
        total_revenue = Payment.objects.filter(payment_status='Success').aggregate(total=Sum('amount'))['total'] or 0
        context = {
            'recent_payments': recent_payments,
            'total_revenue': total_revenue,
        }
        return render(request, 'accounts/accountant_dashboard.html', context)

    # Default fallback
    return render(request, 'accounts/dashboard.html')


@role_required('super_admin', 'admin', 'hr')
def admin_panel_view(request):
    total_students = User.objects.filter(role__in=['student', 'intern']).count()
    active_interns = InternshipEnrollment.objects.filter(completion_status='Active').count()
    total_trainers = User.objects.filter(role__in=['trainer', 'team_leader']).count()
    active_courses = Course.objects.filter(course_status='Active').count()
    active_batches = InternshipBatch.objects.filter(status='Active').count()
    pending_tasks = TaskAssignment.objects.filter(submission_status='Submitted').count()
    revenue = Payment.objects.filter(payment_status='Success').aggregate(total=Sum('amount'))['total'] or 0
    recent_activities = AuditLog.objects.all()[:8]
    recent_applications = InternshipApplication.objects.all().order_by('-created_at')[:5]

    context = {
        'total_students': total_students,
        'active_interns': active_interns,
        'total_trainers': total_trainers,
        'active_courses': active_courses,
        'active_batches': active_batches,
        'pending_tasks': pending_tasks,
        'revenue': revenue,
        'recent_activities': recent_activities,
        'recent_applications': recent_applications,
    }
    return render(request, 'accounts/admin_panel.html', context)


@role_required('super_admin', 'admin')
def system_settings_view(request):
    setting = SystemSetting.objects.first()
    if not setting:
        setting = SystemSetting.objects.create()

    if request.method == 'POST':
        setting.institute_name = request.POST.get('institute_name', setting.institute_name)
        setting.tagline = request.POST.get('tagline', setting.tagline)
        setting.about_text = request.POST.get('about_text', setting.about_text)
        setting.address = request.POST.get('address', setting.address)
        setting.email = request.POST.get('email', setting.email)
        setting.phone = request.POST.get('phone', setting.phone)
        setting.min_video_completion_pct = int(request.POST.get('min_video_completion_pct', 90))
        setting.min_exam_passing_pct = int(request.POST.get('min_exam_passing_pct', 40))
        setting.min_attendance_pct = int(request.POST.get('min_attendance_pct', 75))
        setting.save()

        AuditLog.objects.create(user=request.user, action="Updated System Settings", module="Settings")
        messages.success(request, 'System settings updated successfully!')
        return redirect('system_settings')

    return render(request, 'accounts/settings.html', {'setting': setting})


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        new_pass = request.POST.get('new_password')
        if new_pass:
            user.set_password(new_pass)
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'user': user})


@role_required('super_admin', 'admin')
def audit_logs_view(request):
    logs = AuditLog.objects.all()[:100]
    return render(request, 'accounts/audit_logs.html', {'logs': logs})
