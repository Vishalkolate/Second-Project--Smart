from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from courses.models import Course
from internships.models import InternshipProgram
from .models import Certificate
from .services import generate_certificate_pdf, generate_qr_for_certificate


@login_required
def certificate_list(request):
    user = request.user
    is_staff = user.is_superuser or user.role in ['super_admin', 'admin', 'hr', 'trainer']
    if is_staff:
        certificates = Certificate.objects.select_related('student', 'course', 'internship_program').all()
        students = User.objects.filter(role__in=['student', 'intern'])
        courses = Course.objects.all()
        programs = InternshipProgram.objects.all()
        return render(request, 'certificates/certificate_list.html', {
            'certificates': certificates,
            'students': students,
            'courses': courses,
            'programs': programs,
        })
    else:
        # Student / Intern view of their verified certificates
        certificates = Certificate.objects.filter(student=user).select_related('course', 'internship_program').order_by('-issue_date')
        return render(request, 'certificates/my_certificates.html', {
            'certificates': certificates,
        })


@role_required('super_admin', 'admin', 'hr', 'trainer')
def certificate_issue(request):
    if request.method == 'POST':
        student = get_object_or_404(User, id=request.POST.get('student'))
        cert_type = request.POST.get('certificate_type', 'Course Completion')
        course = Course.objects.filter(id=request.POST.get('course')).first() if request.POST.get('course') else None
        internship_program = InternshipProgram.objects.filter(id=request.POST.get('internship_program')).first() if request.POST.get('internship_program') else None

        cert = Certificate.objects.create(
            student=student,
            course=course,
            internship_program=internship_program,
            certificate_type=cert_type,
            remarks=request.POST.get('remarks', '')
        )

        host = request.get_host()
        generate_certificate_pdf(cert, host)
        AuditLog.objects.create(user=request.user, action="Issued Certificate", module="Certificates", record_id=cert.certificate_number)
        messages.success(request, f'Certificate {cert.certificate_number} issued for {student.username}!')
        return redirect('certificate_list')
    return redirect('certificate_list')


def verify_certificate(request, certificate_number):
    cert = Certificate.objects.filter(certificate_number=certificate_number).select_related('student', 'course', 'internship_program').first()
    return render(request, 'public/verify_certificate.html', {
        'cert': cert,
        'certificate_number': certificate_number,
    })


def verify_certificate_search(request):
    cert_no = request.GET.get('cert_number', '').strip()
    if cert_no:
        return redirect('verify_certificate', certificate_number=cert_no)
    return render(request, 'public/verify_certificate.html', {'cert': None})


@login_required
def my_certificates(request):
    certs = Certificate.objects.filter(student=request.user).select_related('course', 'internship_program')
    return render(request, 'certificates/my_certificates.html', {'certificates': certs})


@login_required
def download_certificate(request, id):
    cert = get_object_or_404(Certificate, id=id)
    if cert.student != request.user and not (request.user.is_superuser or request.user.role in ['admin', 'hr', 'trainer']):
        messages.error(request, 'Unauthorized.')
        return redirect('my_certificates')

    if not cert.pdf_file:
        generate_certificate_pdf(cert, request.get_host())

    return FileResponse(cert.pdf_file.open('rb'), content_type='application/pdf', filename=f"{cert.certificate_number}.pdf")
