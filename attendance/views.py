from datetime import date, time, datetime, timedelta
import calendar
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.http import HttpResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from internships.models import InternshipBatch
from courses.models import Course
from learning.models import Lesson, Enrollment
from .models import Attendance, LeaveRequest, LectureAttendance


@login_required
def attendance_dashboard(request):
    # Both /attendance/ and /attendance/my-attendance/ present the complete visual portal
    return my_attendance(request)


@login_required
def mark_attendance(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        batch_id = request.POST.get('batch')
        att_date = request.POST.get('attendance_date', str(timezone.now().date()))
        status = request.POST.get('status', 'present')
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        remarks = request.POST.get('remarks', '')

        # Permissions: staff can mark for anyone, learners for themselves
        is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer', 'team_leader']
        if is_staff and student_id:
            student = get_object_or_404(User, id=student_id)
        else:
            student = request.user

        batch = InternshipBatch.objects.filter(id=batch_id).first() if batch_id else None

        check_in = None
        if check_in_str:
            for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p'):
                try:
                    check_in = datetime.strptime(check_in_str.strip(), fmt).time()
                    break
                except ValueError:
                    pass

        check_out = None
        if check_out_str:
            for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p'):
                try:
                    check_out = datetime.strptime(check_out_str.strip(), fmt).time()
                    break
                except ValueError:
                    pass

        att, created = Attendance.objects.update_or_create(
            student=student,
            attendance_date=att_date,
            defaults={
                'batch': batch,
                'status': status,
                'check_in': check_in,
                'check_out': check_out,
                'remarks': remarks,
                'marked_by': request.user,
            }
        )
        AuditLog.objects.create(
            user=request.user,
            action=f"Marked Attendance ({status})",
            module="Attendance",
            record_id=str(student.id)
        )
        action_word = "added" if created else "updated"
        messages.success(request, f'Attendance {action_word} successfully for {student.get_full_name() or student.username} on {att_date} ({status.title()})!')
        return redirect(f"{reverse('my_attendance')}?student_id={student.id}")
    return redirect('my_attendance')


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


@login_required
@require_POST
def quick_checkin(request):
    today = timezone.localtime(timezone.now()).date()
    now_time = get_current_time(request)
    att, created = Attendance.objects.get_or_create(
        student=request.user,
        attendance_date=today,
        defaults={'status': 'present', 'check_in': now_time}
    )
    if not created and not att.check_in:
        att.check_in = now_time
        att.status = 'present'
        att.save()
    messages.success(request, f'Attendance checked in successfully at {now_time.strftime("%I:%M %p")}')
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'my_attendance')


@login_required
@require_POST
def quick_checkout(request):
    today = timezone.localtime(timezone.now()).date()
    now_time = get_current_time(request)
    att = Attendance.objects.filter(student=request.user, attendance_date=today).first()
    if att:
        att.check_out = now_time
        att.save()
    else:
        Attendance.objects.create(student=request.user, attendance_date=today, status='present', check_out=now_time)
    messages.success(request, f'Attendance checked out successfully at {now_time.strftime("%I:%M %p")}')
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'my_attendance')


@login_required
def student_attendance_view(request):
    is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer', 'team_leader']
    all_students = []
    target_user = request.user

    if is_staff:
        all_students = User.objects.filter(role__in=['student', 'intern']).order_by('first_name', 'username')
        student_id = request.GET.get('student_id')
        if student_id:
            target_user = User.objects.filter(id=student_id).first() or request.user
        elif request.user.role in ['super_admin', 'admin', 'hr', 'trainer']:
            s_user = User.objects.filter(role='student').first()
            if s_user:
                target_user = s_user

    # Fetch enrolled courses
    enrollments = Enrollment.objects.filter(student=target_user).select_related('course')
    selected_course_id = request.GET.get('course_id')

    # Fetch lecture attendance records
    lecture_records = LectureAttendance.objects.filter(student=target_user).select_related('course', 'lesson', 'trainer')
    if selected_course_id:
        lecture_records = lecture_records.filter(course_id=selected_course_id)

    total_lectures = lecture_records.count()
    attended_lectures = lecture_records.filter(status='present').count()
    late_lectures = lecture_records.filter(status='late').count()
    absent_lectures = lecture_records.filter(status='absent').count()
    lecture_percentage = int(round(((attended_lectures + (late_lectures * 0.8)) / total_lectures) * 100)) if total_lectures > 0 else 0
    is_exam_eligible = lecture_percentage >= 75

    # Course-wise attendance stats
    course_stats = []
    for enr in enrollments:
        c_recs = LectureAttendance.objects.filter(student=target_user, course=enr.course)
        c_total = c_recs.count()
        c_att = c_recs.filter(status='present').count()
        c_pct = int(round((c_att / c_total) * 100)) if c_total > 0 else 0
        course_stats.append({
            'enrollment': enr,
            'total': c_total,
            'attended': c_att,
            'percentage': c_pct,
        })

    all_courses = Course.objects.all()
    all_lessons = Lesson.objects.all().select_related('module', 'module__course')
    leaves = LeaveRequest.objects.filter(student=target_user).order_by('-created_at')

    return render(request, 'attendance/student_attendance.html', {
        'target_user': target_user,
        'is_staff': is_staff,
        'all_students': all_students,
        'enrollments': enrollments,
        'selected_course_id': selected_course_id,
        'lecture_records': lecture_records,
        'total_lectures': total_lectures,
        'attended_lectures': attended_lectures,
        'late_lectures': late_lectures,
        'absent_lectures': absent_lectures,
        'lecture_percentage': lecture_percentage,
        'is_exam_eligible': is_exam_eligible,
        'course_stats': course_stats,
        'all_courses': all_courses,
        'all_lessons': all_lessons,
        'leaves': leaves,
        'today': timezone.localdate(),
    })


@login_required
def intern_attendance_view(request):
    today = timezone.localdate()
    year = int(request.GET.get('year', 2026))
    month = int(request.GET.get('month', 11))

    is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer', 'team_leader']
    all_students = []
    target_user = request.user

    if is_staff:
        all_students = User.objects.filter(role__in=['student', 'intern']).order_by('first_name', 'username')
        student_id = request.GET.get('student_id')
        if student_id:
            target_user = User.objects.filter(id=student_id).first() or request.user
        elif request.user.role in ['super_admin', 'admin', 'hr', 'trainer']:
            v_user = User.objects.filter(role='intern').first() or User.objects.filter(username='vishal').first()
            if v_user:
                target_user = v_user

    month_records = Attendance.objects.filter(
        student=target_user,
        attendance_date__year=year,
        attendance_date__month=month
    ).order_by('-attendance_date')

    present_days = month_records.filter(status='present').count()
    late_days = month_records.filter(status='late').count()
    absent_days = month_records.filter(status='absent').count()
    leave_days = month_records.filter(status='leave').count()

    total_countable = present_days + late_days + absent_days + leave_days
    percentage = int(round(((present_days + late_days) / total_countable) * 100)) if total_countable > 0 else 0

    _, num_days = calendar.monthrange(year, month)
    att_map = {att.attendance_date: att for att in month_records}

    calendar_days = []
    first_weekday = date(year, month, 1).weekday()
    sunday_offset = (first_weekday + 1) % 7
    for _ in range(sunday_offset):
        calendar_days.append({'is_empty': True})

    for d in range(1, num_days + 1):
        cur_date = date(year, month, d)
        att = att_map.get(cur_date)
        is_sunday = (cur_date.weekday() == 6)

        st = 'upcoming'
        rem = ''
        if att:
            st = att.status
            rem = att.remarks
        elif is_sunday and cur_date <= today:
            st = 'weekly_off'

        calendar_days.append({
            'is_empty': False,
            'day': d,
            'date': cur_date,
            'status': st,
            'is_today': (d == today.day and month == today.month and year == today.year),
            'remarks': rem,
        })

    daily_logs = []
    for cur_date, att in sorted(att_map.items(), key=lambda x: x[0], reverse=True):
        check_in_str = att.check_in.strftime('%I:%M %p') if att.check_in else '--'
        check_out_str = att.check_out.strftime('%I:%M %p') if att.check_out else '--'

        duration_str = '0h 0m'
        duration_class = 'duration-zero'
        progress_pct = 0
        working_hours_label = '0h 0m / 8h 00m'

        if att.status == 'late' and not att.check_out:
            duration_str = 'Not Completed'
            duration_class = 'duration-warning'
            working_hours_label = 'Not Completed / 8h 00m'
            progress_pct = 0
        elif att.check_in and att.check_out:
            dt_in = datetime.combine(cur_date, att.check_in)
            dt_out = datetime.combine(cur_date, att.check_out)
            diff_mins = max(0, int((dt_out - dt_in).total_seconds() / 60))
            h = diff_mins // 60
            m = diff_mins % 60
            duration_str = f"{h}h {m:02d}m"
            duration_class = 'duration-success'
            progress_pct = min(100, int((diff_mins / 480) * 100))
            working_hours_label = f"{duration_str} / 8h 00m"

        status_label = dict(Attendance.STATUS_CHOICES).get(att.status, att.status.title())
        if att.status == 'holiday':
            status_label = 'National Holiday'
        elif att.status == 'weekly_off':
            status_label = 'Weekly Off'
        elif att.status == 'late':
            status_label = 'Late'

        daily_logs.append({
            'date_str': cur_date.strftime('%d %b %Y'),
            'day_name': cur_date.strftime('%A'),
            'status': att.status,
            'status_label': status_label,
            'check_in': check_in_str,
            'check_out': check_out_str,
            'duration': duration_str,
            'duration_class': duration_class,
            'progress_pct': progress_pct,
            'working_hours_label': working_hours_label,
            'remarks': att.remarks or 'No punch recorded',
            'is_holiday': (att.status == 'holiday'),
            'is_diwali': ('Diwali' in (att.remarks or '')),
        })

    today_record = Attendance.objects.filter(student=target_user, attendance_date=today).first()
    leaves = LeaveRequest.objects.filter(student=target_user).order_by('-created_at')

    p_pct = (present_days / total_countable * 100) if total_countable else 0
    l_pct = (late_days / total_countable * 100) if total_countable else 0
    stop1 = p_pct
    stop2 = stop1 + l_pct

    return render(request, 'attendance/intern_attendance.html', {
        'today': today,
        'today_record': today_record,
        'year': year,
        'month': month,
        'month_name': today.strftime('%B %Y'),
        'target_user': target_user,
        'is_staff': is_staff,
        'all_students': all_students,
        'present_days': present_days,
        'late_days': late_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'percentage': percentage,
        'calendar_days': calendar_days,
        'daily_logs': daily_logs,
        'log_count': len(daily_logs),
        'leaves': leaves,
        'donut_stop1': stop1,
        'donut_stop2': stop2,
        'has_data': (total_countable > 0),
    })


@login_required
def my_attendance(request):
    # Role-based redirection to dedicated separate attendance files
    if request.user.role == 'student':
        return student_attendance_view(request)
    elif request.user.role == 'intern':
        return intern_attendance_view(request)
    
    # For staff/admin, allow switching between student lecture attendance and intern shift attendance
    att_type = request.GET.get('type')
    if att_type == 'student':
        return student_attendance_view(request)
    return intern_attendance_view(request)


@login_required
def mark_lecture_attendance(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        lesson_id = request.POST.get('lesson_id')
        lecture_title = request.POST.get('lecture_title', '').strip()
        lecture_date_str = request.POST.get('lecture_date', str(timezone.localdate()))
        lecture_time_str = request.POST.get('lecture_time')
        status = request.POST.get('status', 'present')
        duration = int(request.POST.get('duration', 60) or 60)
        remarks = request.POST.get('remarks', '')

        is_staff = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer']
        if is_staff and student_id:
            target_student = get_object_or_404(User, id=student_id)
        else:
            target_student = request.user

        course = get_object_or_404(Course, id=course_id)
        lesson = Lesson.objects.filter(id=lesson_id).first() if lesson_id else None
        if not lecture_title and lesson:
            lecture_title = lesson.lesson_title
        elif not lecture_title:
            lecture_title = f"{course.course_name} Lecture Session"

        try:
            lecture_date = datetime.strptime(lecture_date_str, '%Y-%m-%d').date()
        except ValueError:
            lecture_date = timezone.localdate()

        lecture_time = None
        if lecture_time_str:
            for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p'):
                try:
                    lecture_time = datetime.strptime(lecture_time_str.strip(), fmt).time()
                    break
                except ValueError:
                    pass
        if not lecture_time:
            lecture_time = timezone.localtime(timezone.now()).time()

        rec, created = LectureAttendance.objects.update_or_create(
            student=target_student,
            course=course,
            lecture_date=lecture_date,
            lecture_title=lecture_title,
            defaults={
                'lesson': lesson,
                'lecture_time': lecture_time,
                'status': status,
                'attended_duration_minutes': duration,
                'trainer': request.user if is_staff else (course.instructor or request.user),
                'remarks': remarks or 'Attended course lecture',
            }
        )
        AuditLog.objects.create(
            user=request.user,
            action=f"Marked Lecture Attendance ({course.course_name} - {status})",
            module="Attendance",
            record_id=str(rec.id)
        )
        action_word = "recorded" if created else "updated"
        messages.success(request, f'Lecture attendance {action_word} successfully for {course.course_name}: "{lecture_title}" ({status.title()})!')
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer if referer else f"{reverse('student_attendance')}?student_id={target_student.id}")
    return redirect('student_attendance')


@login_required
def export_attendance_excel(request):
    year = int(request.GET.get('year', 2026))
    month = int(request.GET.get('month', 11))
    records = Attendance.objects.filter(
        student=request.user,
        attendance_date__year=year,
        attendance_date__month=month
    ).order_by('attendance_date')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Log"

    # Header title
    ws.merge_cells('A1:G1')
    title_cell = ws['A1']
    title_cell.value = f"Daily Attendance Log - {request.user.get_full_name() or request.user.username} (November {year})"
    title_cell.font = Font(size=14, bold=True, color="1E3A8A")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")

    headers = ["Date", "Day", "Status", "Check In", "Check Out", "Duration", "Remarks"]
    ws.append([])
    ws.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for r in records:
        in_str = r.check_in.strftime('%I:%M %p') if r.check_in else '--'
        out_str = r.check_out.strftime('%I:%M %p') if r.check_out else '--'
        dur_str = '--'
        if r.check_in and r.check_out:
            dt_in = datetime.combine(r.attendance_date, r.check_in)
            dt_out = datetime.combine(r.attendance_date, r.check_out)
            mins = max(0, int((dt_out - dt_in).total_seconds() / 60))
            dur_str = f"{mins // 60}h {mins % 60}m"
        elif r.status == 'late':
            dur_str = 'Not Completed'

        ws.append([
            r.attendance_date.strftime('%d-%m-%Y'),
            r.attendance_date.strftime('%A'),
            r.status.title(),
            in_str,
            out_str,
            dur_str,
            r.remarks
        ])

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Attendance_{request.user.username}_{month}_{year}.xlsx'
    wb.save(response)
    return response


# Leave Management
@login_required
def leave_apply(request):
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('leave_reason')

        LeaveRequest.objects.create(
            student=request.user,
            from_date=from_date,
            to_date=to_date,
            leave_reason=reason,
            approval_status='pending'
        )
        AuditLog.objects.create(user=request.user, action="Applied for Leave", module="Attendance", record_id=str(request.user.id))
        messages.success(request, 'Leave request submitted! Admin/HR will review and verify your request.')
        return redirect('my_attendance')
    return render(request, 'attendance/leave_apply.html')


@role_required('super_admin', 'admin', 'hr', 'trainer')
def leave_list(request):
    status_filter = request.GET.get('status', '')
    leaves = LeaveRequest.objects.select_related('student', 'approved_by').all().order_by('-created_at')
    if status_filter:
        leaves = leaves.filter(approval_status=status_filter)

    pending_count = LeaveRequest.objects.filter(approval_status='pending').count()
    approved_count = LeaveRequest.objects.filter(approval_status='approved').count()
    rejected_count = LeaveRequest.objects.filter(approval_status='rejected').count()

    return render(request, 'attendance/leaves.html', {
        'leaves': leaves,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@role_required('super_admin', 'admin', 'hr', 'trainer')
@require_POST
def leave_action(request, id):
    leave = get_object_or_404(LeaveRequest, id=id)
    action = request.POST.get('action')  # approved or rejected
    remarks = request.POST.get('remarks', '')
    if action in ['approved', 'rejected']:
        leave.approval_status = action
        leave.approved_by = request.user
        leave.admin_remarks = remarks
        leave.save()
        AuditLog.objects.create(user=request.user, action=f"Leave {action.title()}", module="Attendance", record_id=str(leave.id))
        messages.success(request, f'Leave request for {leave.student.username} has been {action}!')
    return redirect('leave_list')
