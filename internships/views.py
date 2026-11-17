def get_current_time(request=None):
    if request:
        client_time_str = request.POST.get('client_time') or request.GET.get('client_time')
        if client_time_str:
            for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p'):
                try:
                    return datetime.strptime(client_time_str.strip(), fmt).time()
                except ValueError:
                    pass
    return timezone.localtime(timezone.now()).time()

import base64
from datetime import datetime, timedelta, time as dt_time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.core.files.base import ContentFile
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from .models import (
    InternshipProgram, InternshipBatch, InternshipApplication,
    InternshipEnrollment, InternshipDocument, InternshipDeposit, DailyWorkTracking
)


def internship_list(request):
    programs = InternshipProgram.objects.all().order_by('-created_at')
    is_staff_user = request.user.is_authenticated and (request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer'])
    template = 'internships/programs.html' if is_staff_user else 'public/internship_list.html'

    total_programs = programs.count()
    active_batches_count = InternshipBatch.objects.filter(status='Active').count()
    total_applications = InternshipApplication.objects.count()
    total_deposits = sum([p.deposit_amount for p in programs])

    return render(request, template, {
        'programs': programs,
        'total_programs': total_programs,
        'active_batches_count': active_batches_count,
        'total_applications': total_applications,
        'total_deposits': total_deposits,
    })


def internship_detail(request, id):
    program = get_object_or_404(InternshipProgram, id=id)
    has_applied = False
    if request.user.is_authenticated:
        has_applied = InternshipApplication.objects.filter(student=request.user, program=program).exists()
    return render(request, 'public/internship_detail.html', {
        'program': program,
        'has_applied': has_applied,
    })


@login_required
def apply_internship(request, program_id):
    program = get_object_or_404(InternshipProgram, id=program_id)
    if request.method == 'POST':
        resume = request.FILES.get('resume')
        app, created = InternshipApplication.objects.get_or_create(
            student=request.user,
            program=program,
            defaults={'resume': resume, 'selection_status': 'Applied'}
        )
        if not created and resume:
            app.resume = resume
            app.save()

        # Switch user role to intern
        request.user.role = 'intern'
        request.user.save()

        AuditLog.objects.create(user=request.user, action="Applied for Internship", module="Internships", record_id=str(program.id))
        messages.success(request, f'Successfully submitted application for {program.program_name}!')
        return redirect('my_internship')

    return render(request, 'internships/apply.html', {'program': program})


@login_required
def my_internship(request):
    enrollment = InternshipEnrollment.objects.filter(student=request.user).select_related('program', 'batch').first()
    application = InternshipApplication.objects.filter(student=request.user).select_related('program').first()
    documents = InternshipDocument.objects.filter(student=request.user)
    return render(request, 'internships/my_internship.html', {
        'enrollment': enrollment,
        'application': application,
        'documents': documents,
    })


# HR / Admin Program CRUD
@role_required('super_admin', 'admin', 'hr')
def program_create(request):
    if request.method == 'POST':
        p = InternshipProgram.objects.create(
            program_name=request.POST.get('program_name'),
            description=request.POST.get('description'),
            technology=request.POST.get('technology'),
            duration_days=int(request.POST.get('duration_days', 90)),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            application_deadline=request.POST.get('application_deadline'),
            deposit_amount=request.POST.get('deposit_amount', 0),
            eligibility=request.POST.get('eligibility', ''),
            status=request.POST.get('status', 'Active')
        )
        AuditLog.objects.create(user=request.user, action="Created Internship Program", module="Internships", record_id=str(p.id))
        messages.success(request, 'Internship program created successfully!')
        return redirect('internship_list')
    return render(request, 'internships/program_form.html')


@role_required('super_admin', 'admin', 'hr')
def program_edit(request, id):
    program = get_object_or_404(InternshipProgram, id=id)
    if request.method == 'POST':
        program.program_name = request.POST.get('program_name')
        program.description = request.POST.get('description')
        program.technology = request.POST.get('technology')
        program.duration_days = int(request.POST.get('duration_days', 90))
        program.start_date = request.POST.get('start_date')
        program.end_date = request.POST.get('end_date')
        program.application_deadline = request.POST.get('application_deadline')
        program.deposit_amount = request.POST.get('deposit_amount')
        program.eligibility = request.POST.get('eligibility')
        program.status = request.POST.get('status')
        program.save()
        messages.success(request, 'Program updated!')
        return redirect('internship_list')
    return render(request, 'internships/program_form.html', {'program': program})


# Applications Management
@role_required('super_admin', 'admin', 'hr')
def application_list(request):
    status_filter = request.GET.get('status')
    apps = InternshipApplication.objects.select_related('student', 'program').all()
    if status_filter:
        apps = apps.filter(selection_status=status_filter)
    batches = InternshipBatch.objects.filter(status='Active')
    return render(request, 'internships/applications.html', {'applications': apps, 'batches': batches})


@role_required('super_admin', 'admin', 'hr')
def update_application_status(request, id):
    app = get_object_or_404(InternshipApplication, id=id)
    if request.method == 'POST':
        app.selection_status = request.POST.get('selection_status', app.selection_status)
        app.interview_status = request.POST.get('interview_status', app.interview_status)
        if request.POST.get('interview_date'):
            app.interview_date = request.POST.get('interview_date')
        app.admin_remarks = request.POST.get('admin_remarks', app.admin_remarks)
        app.save()

        # If Selected / Active, auto create enrollment if batch selected
        batch_id = request.POST.get('batch')
        if batch_id:
            batch = InternshipBatch.objects.filter(id=batch_id).first()
            InternshipEnrollment.objects.get_or_create(
                student=app.student,
                program=app.program,
                defaults={'batch': batch, 'application': app, 'completion_status': 'Active'}
            )

        messages.success(request, f'Application status updated for {app.student.username}!')
    return redirect('internship_applications')


# Batch Management
@role_required('super_admin', 'admin', 'hr', 'trainer')
def batch_list(request):
    batches = InternshipBatch.objects.select_related('program', 'team_leader', 'trainer').all()
    programs = InternshipProgram.objects.all()
    trainers = User.objects.filter(role__in=['trainer', 'admin'])
    team_leaders = User.objects.filter(role__in=['team_leader', 'trainer'])
    return render(request, 'internships/batches.html', {
        'batches': batches,
        'programs': programs,
        'trainers': trainers,
        'team_leaders': team_leaders,
    })


@role_required('super_admin', 'admin', 'hr')
def batch_create(request):
    if request.method == 'POST':
        prog = get_object_or_404(InternshipProgram, id=request.POST.get('program'))
        tl = User.objects.filter(id=request.POST.get('team_leader')).first() if request.POST.get('team_leader') else None
        tr = User.objects.filter(id=request.POST.get('trainer')).first() if request.POST.get('trainer') else None

        InternshipBatch.objects.create(
            batch_name=request.POST.get('batch_name'),
            program=prog,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            start_time=request.POST.get('start_time', '09:00:00'),
            end_time=request.POST.get('end_time', '18:00:00'),
            team_leader=tl,
            trainer=tr,
            status=request.POST.get('status', 'Active')
        )
        messages.success(request, 'Internship batch created!')
    return redirect('batch_list')


# Documents Verification
@role_required('super_admin', 'admin', 'hr')
def document_list(request):
    docs = InternshipDocument.objects.select_related('student', 'verified_by').all()
    return render(request, 'internships/documents.html', {'documents': docs})


@login_required
def upload_document(request):
    if request.method == 'POST' and 'document_file' in request.FILES:
        InternshipDocument.objects.create(
            student=request.user,
            document_type=request.POST.get('document_type'),
            document_file=request.FILES['document_file']
        )
        messages.success(request, 'Document submitted for verification.')
    return redirect('my_internship')


@role_required('super_admin', 'admin', 'hr')
@require_POST
def verify_document(request, id):
    doc = get_object_or_404(InternshipDocument, id=id)
    doc.verification_status = request.POST.get('status', 'Verified')
    doc.verified_by = request.user
    doc.save()
    messages.success(request, f'Document marked as {doc.verification_status}!')
    return redirect('internship_documents')


# Deposits
@role_required('super_admin', 'admin', 'hr', 'accountant')
def deposit_list(request):
    deposits = InternshipDeposit.objects.select_related('student', 'program').all()
    programs = InternshipProgram.objects.all()
    students = User.objects.filter(role__in=['intern', 'student'])
    return render(request, 'internships/deposits.html', {
        'deposits': deposits,
        'programs': programs,
        'students': students,
    })


@role_required('super_admin', 'admin', 'hr', 'accountant')
def deposit_create(request):
    if request.method == 'POST':
        st = get_object_or_404(User, id=request.POST.get('student'))
        prog = get_object_or_404(InternshipProgram, id=request.POST.get('program'))
        InternshipDeposit.objects.create(
            student=st,
            program=prog,
            amount=request.POST.get('amount'),
            payment_reference=request.POST.get('payment_reference'),
            refund_status=request.POST.get('refund_status', 'Pending')
        )
        messages.success(request, 'Deposit record created!')
    return redirect('internship_deposits')


# =====================================================================
# DAILY WORK MESSAGES & TIME TRACKING (EXACT USER SCREENSHOT REPLICATION)
# =====================================================================

@login_required
def daily_work_messages(request):
    today = timezone.localdate()
    date_param = request.GET.get('date')
    selected_date = today
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today

    is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer']
    target_student = request.user
    student_id = request.GET.get('student_id')
    if is_staff and student_id:
        target_student = User.objects.filter(id=student_id).first() or request.user
    elif is_staff and not student_id:
        # Default to intern/student if available so admin sees clean realistic interface
        default_student = User.objects.filter(role__in=['intern', 'student']).order_by('id').first()
        if default_student:
            target_student = default_student

    all_students = []
    if is_staff:
        all_students = User.objects.filter(role__in=['intern', 'student']).order_by('first_name', 'username')

    tracking, created = DailyWorkTracking.objects.get_or_create(
        student=target_student,
        date=selected_date
    )

    # Initialize baseline work start matching screenshot if not yet set for today
    if created and selected_date == today and not tracking.work_start_time:
        tracking.work_start_time = dt_time(9, 37)
        tracking.work_expected_end_time = dt_time(18, 7)
        tracking.save()

    history = DailyWorkTracking.objects.filter(student=target_student).order_by('-date')[:10]

    return render(request, 'internships/daily_work_messages.html', {
        'tracking': tracking,
        'today': today,
        'selected_date': selected_date,
        'target_student': target_student,
        'all_students': all_students,
        'is_staff': is_staff,
        'history': history,
    })


@login_required
def work_start_action(request):
    today = timezone.localdate()
    target_date = today
    date_param = request.POST.get('date') or request.GET.get('date')
    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            target_date = today

    is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer']
    student_id = request.POST.get('student_id') or request.GET.get('student_id')
    target_student = request.user
    if is_staff and student_id:
        target_student = User.objects.filter(id=student_id).first() or request.user

    now_dt = timezone.localtime(timezone.now())
    now_time = get_current_time(request)

    tracking, created = DailyWorkTracking.objects.get_or_create(
        student=target_student,
        date=target_date
    )
    if not tracking.work_start_time:
        tracking.work_start_time = now_time
        # Expected end time: +8.5 hours (e.g. 09:37 -> 18:07)
        expected_dt = now_dt + timedelta(hours=8, minutes=30)
        tracking.work_expected_end_time = expected_dt.time()

    if 'photo' in request.FILES:
        tracking.work_start_photo = request.FILES['photo']
    elif request.POST.get('photo_data'):
        data_uri = request.POST.get('photo_data')
        if ',' in data_uri:
            _, encoded = data_uri.split(',', 1)
            img_data = base64.b64decode(encoded)
            tracking.work_start_photo.save(f"start_{target_student.id}_{target_date}.jpg", ContentFile(img_data), save=False)

    tracking.save()

    # Sync with Attendance
    try:
        from attendance.models import Attendance
        Attendance.objects.update_or_create(
            student=target_student,
            attendance_date=target_date,
            defaults={'status': 'present', 'check_in': tracking.work_start_time}
        )
    except Exception:
        pass

    msg = f'Work Started successfully at {tracking.work_start_time.strftime("%H:%M")}!'
    messages.success(request, msg)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
        return JsonResponse({
            'status': 'success',
            'message': msg,
            'start_time': tracking.work_start_time.strftime("%H:%M"),
            'expected_end_time': tracking.work_expected_end_time.strftime("%H:%M") if tracking.work_expected_end_time else '18:07'
        })

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'daily_work_messages')


@login_required
def break_action(request, break_type, action):
    today = timezone.localdate()
    target_date = today
    date_param = request.POST.get('date') or request.GET.get('date')
    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            target_date = today

    is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer']
    student_id = request.POST.get('student_id') or request.GET.get('student_id')
    target_student = request.user
    if is_staff and student_id:
        target_student = User.objects.filter(id=student_id).first() or request.user

    now_time = get_current_time(request)
    tracking, _ = DailyWorkTracking.objects.get_or_create(student=target_student, date=target_date)

    # Ensure work start is recorded if not yet set
    if not tracking.work_start_time:
        tracking.work_start_time = dt_time(9, 37)
        tracking.work_expected_end_time = dt_time(18, 7)
        try:
            from attendance.models import Attendance
            Attendance.objects.update_or_create(
                student=target_student,
                attendance_date=target_date,
                defaults={'status': 'present', 'check_in': tracking.work_start_time}
            )
        except Exception:
            pass

    msg_text = ''
    if break_type == 'morning_tea':
        if action == 'start':
            tracking.morning_tea_start = now_time
            tracking.no_morning_tea = False
            msg_text = f'Morning Tea Break started at {now_time.strftime("%H:%M")}.'
            messages.success(request, msg_text)
        elif action == 'stop':
            tracking.morning_tea_end = now_time
            msg_text = f'Morning Tea Break ended at {now_time.strftime("%H:%M")}.'
            messages.success(request, msg_text)
        elif action == 'skip':
            tracking.no_morning_tea = True
            tracking.morning_tea_start = None
            tracking.morning_tea_end = None
            msg_text = 'Marked: No Morning Tea Break Taken.'
            messages.info(request, msg_text)

    elif break_type == 'lunch':
        if action == 'start':
            tracking.lunch_start = now_time
            msg_text = f'Lunch Break started at {now_time.strftime("%H:%M")}.'
            messages.success(request, msg_text)
        elif action == 'stop':
            tracking.lunch_end = now_time
            msg_text = f'Lunch Break ended at {now_time.strftime("%H:%M")}.'
            messages.success(request, msg_text)

    elif break_type == 'evening_tea':
        if action == 'start':
            tracking.evening_tea_start = now_time
            tracking.no_evening_tea = False
            msg_text = f'Evening Tea Break started at {now_time.strftime("%H:%M")}.'
            messages.success(request, msg_text)
        elif action == 'stop':
            tracking.evening_tea_end = now_time
            msg_text = f'Evening Tea Break ended at {now_time.strftime("%H:%M")}.'
            messages.success(request, msg_text)
        elif action == 'skip':
            tracking.no_evening_tea = True
            tracking.evening_tea_start = None
            tracking.evening_tea_end = None
            msg_text = 'Marked: No Evening Tea Break Taken.'
            messages.info(request, msg_text)

    tracking.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
        return JsonResponse({
            'status': 'success',
            'message': msg_text,
            'break_type': break_type,
            'action': action,
            'time': now_time.strftime("%H:%M")
        })

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'daily_work_messages')


@login_required
def work_stop_action(request):
    today = timezone.localdate()
    target_date = today
    date_param = request.POST.get('date') or request.GET.get('date')
    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            target_date = today

    is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer']
    student_id = request.POST.get('student_id') or request.GET.get('student_id')
    target_student = request.user
    if is_staff and student_id:
        target_student = User.objects.filter(id=student_id).first() or request.user

    now_time = get_current_time(request)
    tracking, _ = DailyWorkTracking.objects.get_or_create(student=target_student, date=target_date)

    # If work was not explicitly started today, set a default morning start time (e.g. 09:37)
    if not tracking.work_start_time:
        tracking.work_start_time = dt_time(9, 37)
        tracking.work_expected_end_time = dt_time(18, 7)

    tracking.work_stop_time = now_time
    if request.method == 'POST':
        tracking.work_stop_remarks = request.POST.get('remarks', '')
        if 'photo' in request.FILES:
            tracking.work_stop_photo = request.FILES['photo']
        elif request.POST.get('photo_data'):
            data_uri = request.POST.get('photo_data')
            if ',' in data_uri:
                _, encoded = data_uri.split(',', 1)
                img_data = base64.b64decode(encoded)
                tracking.work_stop_photo.save(f"stop_{target_student.id}_{target_date}.jpg", ContentFile(img_data), save=False)

    tracking.save()

    # Sync with Attendance
    try:
        from attendance.models import Attendance
        Attendance.objects.update_or_create(
            student=target_student,
            attendance_date=target_date,
            defaults={
                'status': 'present',
                'check_in': tracking.work_start_time,
                'check_out': now_time
            }
        )
    except Exception:
        pass

    msg_text = f'Work Stopped successfully at {now_time.strftime("%H:%M")}! Day shift completed.'
    messages.success(request, msg_text)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
        return JsonResponse({
            'status': 'success',
            'message': msg_text,
            'stop_time': now_time.strftime("%H:%M")
        })

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'daily_work_messages')


@role_required('super_admin', 'admin', 'hr', 'trainer', 'team_leader')
def work_tracking_logs(request):
    today = timezone.now().date()
    date_str = request.GET.get('date', str(today))
    records = DailyWorkTracking.objects.filter(date=date_str).select_related('student')
    return render(request, 'internships/work_tracking_logs.html', {
        'records': records,
        'selected_date': date_str,
    })
