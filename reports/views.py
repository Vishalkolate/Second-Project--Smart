from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import User
from courses.models import Course
from internships.models import InternshipProgram, InternshipBatch, InternshipEnrollment
from attendance.models import Attendance
from tasks.models import TaskAssignment
from examinations.models import ExamAttempt
from payments.models import Payment
from placements.models import JobApplication
from .services import generate_excel_response, generate_csv_response


@role_required('super_admin', 'admin', 'hr', 'accountant')
def reports_dashboard(request):
    return render(request, 'reports/dashboard.html')


@role_required('super_admin', 'admin', 'hr')
def student_admissions_report(request):
    course_id = request.GET.get('course')
    fmt = request.GET.get('export')
    students = User.objects.filter(role__in=['student', 'intern']).select_related('student_profile')

    if course_id:
        students = students.filter(enrollments__course_id=course_id)

    headers = ['ID', 'Username', 'Full Name', 'Email', 'Phone', 'Role', 'Date Joined']
    rows = [
        [s.id, s.username, s.get_full_name() or '-', s.email, s.phone or '-', s.get_role_display(), s.date_joined.strftime('%Y-%m-%d')]
        for s in students
    ]

    if fmt == 'excel':
        return generate_excel_response('Admissions Report', headers, rows, 'student_admissions.xlsx')
    elif fmt == 'csv':
        return generate_csv_response(headers, rows, 'student_admissions.csv')

    courses = Course.objects.all()
    return render(request, 'reports/student_admissions.html', {'students': students, 'courses': courses})


@role_required('super_admin', 'admin', 'hr')
def attendance_report(request):
    batch_id = request.GET.get('batch')
    fmt = request.GET.get('export')
    records = Attendance.objects.select_related('student', 'batch')

    if batch_id:
        records = records.filter(batch_id=batch_id)

    headers = ['Date', 'Student', 'Batch', 'Status', 'Check In', 'Check Out', 'Remarks']
    rows = [
        [
            r.attendance_date.strftime('%Y-%m-%d'),
            r.student.username,
            r.batch.batch_name if r.batch else '-',
            r.get_status_display(),
            r.check_in.strftime('%H:%M') if r.check_in else '-',
            r.check_out.strftime('%H:%M') if r.check_out else '-',
            r.remarks or '-'
        ]
        for r in records
    ]

    if fmt == 'excel':
        return generate_excel_response('Attendance Report', headers, rows, 'attendance_report.xlsx')
    elif fmt == 'csv':
        return generate_csv_response(headers, rows, 'attendance_report.csv')

    batches = InternshipBatch.objects.all()
    return render(request, 'reports/attendance.html', {'records': records[:100], 'batches': batches})


@role_required('super_admin', 'admin', 'accountant')
def fees_report(request):
    fmt = request.GET.get('export')
    payments = Payment.objects.select_related('student', 'course').all()

    headers = ['Transaction ID', 'Student', 'Course / Program', 'Amount (INR)', 'Type', 'Method', 'Status', 'Date']
    rows = [
        [
            p.transaction_id,
            p.student.username,
            p.course.course_name if p.course else '-',
            float(p.amount),
            p.payment_type,
            p.payment_method,
            p.payment_status,
            p.payment_date.strftime('%Y-%m-%d %H:%M')
        ]
        for p in payments
    ]

    if fmt == 'excel':
        return generate_excel_response('Fees Report', headers, rows, 'fees_collection.xlsx')
    elif fmt == 'csv':
        return generate_csv_response(headers, rows, 'fees_collection.csv')

    return render(request, 'reports/fees.html', {'payments': payments})


@role_required('super_admin', 'admin', 'hr')
def internships_report(request):
    fmt = request.GET.get('export')
    interns = InternshipEnrollment.objects.select_related('student', 'program', 'batch').all()

    headers = ['Student', 'Program', 'Batch', 'Joining Date', 'Status', 'Certificate Status']
    rows = [
        [
            i.student.username,
            i.program.program_name,
            i.batch.batch_name if i.batch else '-',
            i.joining_date.strftime('%Y-%m-%d') if i.joining_date else '-',
            i.completion_status,
            i.certificate_status
        ]
        for i in interns
    ]

    if fmt == 'excel':
        return generate_excel_response('Internships Report', headers, rows, 'internships_report.xlsx')
    elif fmt == 'csv':
        return generate_csv_response(headers, rows, 'internships_report.csv')

    return render(request, 'reports/internships.html', {'interns': interns})
