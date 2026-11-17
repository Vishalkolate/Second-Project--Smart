from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from .models import Company, JobVacancy, JobApplication, MockInterview


def placement_portal(request):
    vacancies = JobVacancy.objects.filter(status='Open').select_related('company')
    companies = Company.objects.all()
    user_applied_ids = []
    if request.user.is_authenticated:
        user_applied_ids = list(JobApplication.objects.filter(student=request.user).values_list('vacancy_id', flat=True))
    return render(request, 'placements/portal.html', {
        'vacancies': vacancies,
        'companies': companies,
        'user_applied_ids': user_applied_ids,
    })


@role_required('super_admin', 'admin', 'hr')
def company_create(request):
    if request.method == 'POST':
        Company.objects.create(
            company_name=request.POST.get('company_name'),
            website=request.POST.get('website', ''),
            contact_email=request.POST.get('contact_email'),
            phone=request.POST.get('phone', ''),
            location=request.POST.get('location', '')
        )
        AuditLog.objects.create(user=request.user, action="Added Hiring Company", module="Placements", record_id=request.POST.get('company_name'))
        messages.success(request, 'Company added successfully!')
    return redirect('placement_portal')


@role_required('super_admin',   'admin', 'hr')
def vacancy_create(request):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=request.POST.get('company'))
        v = JobVacancy.objects.create(
            company=company,
            job_title=request.POST.get('job_title'),
            description=request.POST.get('description'),
            eligibility=request.POST.get('eligibility'),
            salary_package=request.POST.get('salary_package', ''),
            deadline=request.POST.get('deadline'),
            status='Open'
        )
        AuditLog.objects.create(user=request.user, action="Posted Vacancy", module="Placements", record_id=str(v.id))
        messages.success(request, 'Job Vacancy posted successfully!')
    return redirect('placement_portal')


@login_required
def job_apply(request, vacancy_id):
    vacancy = get_object_or_404(JobVacancy, id=vacancy_id)
    if request.method == 'POST':
        resume = request.FILES.get('resume')
        app, created = JobApplication.objects.get_or_create(
            vacancy=vacancy,
            student=request.user,
            defaults={'resume': resume, 'application_status': 'Applied'}
        )
        if not created and resume:
            app.resume = resume
            app.save()
        AuditLog.objects.create(user=request.user, action="Applied for Job", module="Placements", record_id=str(vacancy.id))
        messages.success(request, f'Application submitted successfully for {vacancy.job_title} at {vacancy.company.company_name}!')
        return redirect('placement_portal')
    return render(request, 'placements/job_apply.html', {'vacancy': vacancy})


@role_required('super_admin', 'admin', 'hr')
def job_applications(request):
    apps = JobApplication.objects.select_related('vacancy__company', 'student').all().order_by('-applied_at')
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        status = request.POST.get('status')
        app = get_object_or_404(JobApplication, id=app_id)
        app.application_status = status
        app.save()
        AuditLog.objects.create(user=request.user, action=f"Application {status}", module="Placements", record_id=str(app.id))
        messages.success(request, f'Application status updated to {status}!')
        return redirect('job_applications')
    return render(request, 'placements/applications.html', {'applications': apps})


@login_required
def mock_interviews(request):
    user = request.user
    if user.is_superuser or user.role in ['super_admin', 'admin', 'hr', 'trainer']:
        interviews = MockInterview.objects.select_related('student', 'interviewer').all().order_by('-interview_date')
        interviewers = User.objects.filter(role__in=['trainer', 'hr', 'admin'])
        students = User.objects.filter(role__in=['intern', 'student'])
        total_interviews = interviews.count()
        completed_interviews = interviews.filter(status='Completed').count()
        scheduled_interviews = interviews.filter(status='Scheduled').count()
        completed_list = [i.marks for i in interviews if i.marks is not None]
        avg_marks = round(sum(completed_list) / len(completed_list), 1) if completed_list else 0
        return render(request, 'placements/mock_interviews.html', {
            'interviews': interviews,
            'interviewers': interviewers,
            'students': students,
            'total_interviews': total_interviews,
            'completed_interviews': completed_interviews,
            'scheduled_interviews': scheduled_interviews,
            'avg_marks': avg_marks,
        })
    else:
        interviews = MockInterview.objects.filter(student=user).select_related('interviewer').order_by('-interview_date')
        return render(request, 'placements/my_mock_interviews.html', {'interviews': interviews})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def mock_interview_schedule(request):
    if request.method == 'POST':
        student = get_object_or_404(User, id=request.POST.get('student'))
        interviewer = get_object_or_404(User, id=request.POST.get('interviewer'))
        m = MockInterview.objects.create(
            student=student,
            interviewer=interviewer,
            interview_date=request.POST.get('interview_date'),
            status='Scheduled'
        )
        AuditLog.objects.create(user=request.user, action="Scheduled Mock Interview", module="Placements", record_id=str(m.id))
        messages.success(request, f'Mock interview scheduled for {student.username} with {interviewer.username}!')
    return redirect('mock_interviews')


@role_required('super_admin', 'admin', 'hr', 'trainer')
def mock_interview_evaluate(request, id):
    interview = get_object_or_404(MockInterview, id=id)
    if request.method == 'POST':
        interview.marks = request.POST.get('marks')
        interview.feedback = request.POST.get('feedback', '')
        interview.status = 'Completed'
        interview.save()
        AuditLog.objects.create(user=request.user, action="Evaluated Mock Interview", module="Placements", record_id=str(interview.id))
        messages.success(request, f'Evaluation submitted for {interview.student.username}!')
        return redirect('mock_interviews')
    return render(request, 'placements/mock_evaluate.html', {'interview': interview})
