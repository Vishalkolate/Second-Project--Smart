from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from internships.models import InternshipBatch
from .models import Task, TaskAssignment, TaskSubmission, DailyReport


@login_required
def task_list(request):
    user = request.user
    if user.is_superuser or user.role in ['super_admin', 'admin', 'trainer', 'team_leader']:
        tasks = Task.objects.select_related('assigned_by', 'batch').all()
        batches = InternshipBatch.objects.filter(status='Active')
        return render(request, 'tasks/task_list.html', {'tasks': tasks, 'batches': batches})
    else:
        # Intern or student view
        assignments = TaskAssignment.objects.filter(student=user).select_related('task__batch', 'task__assigned_by')
        return render(request, 'tasks/my_tasks.html', {'assignments': assignments})


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
def task_create(request):
    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        batch = InternshipBatch.objects.filter(id=batch_id).first() if batch_id else None

        task = Task.objects.create(
            task_title=request.POST.get('task_title'),
            task_description=request.POST.get('task_description'),
            batch=batch,
            assigned_by=request.user,
            deadline=request.POST.get('deadline'),
            priority=request.POST.get('priority', 'Medium'),
            marks=int(request.POST.get('marks', 100)),
            status='Active'
        )

        # Assign task to students
        if batch:
            interns = batch.interns.values_list('student', flat=True)
            for stu_id in interns:
                TaskAssignment.objects.create(task=task, student_id=stu_id)
        else:
            all_interns = User.objects.filter(role='intern')
            for stu in all_interns:
                TaskAssignment.objects.create(task=task, student=stu)

        AuditLog.objects.create(user=request.user, action="Created Task", module="Tasks", record_id=str(task.id))
        messages.success(request, 'Task created and assigned successfully!')
        return redirect('task_list')

    batches = InternshipBatch.objects.filter(status='Active')
    return render(request, 'tasks/task_form.html', {'batches': batches})


@login_required
def task_detail(request, id):
    task = get_object_or_404(Task, id=id)
    assignments = task.assignments.select_related('student')
    user_assignment = assignments.filter(student=request.user).first() if request.user.role in ['intern', 'student'] else None
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'assignments': assignments,
        'user_assignment': user_assignment,
    })


@login_required
def task_submit(request, assignment_id):
    assignment = get_object_or_404(TaskAssignment, id=assignment_id)
    if assignment.student != request.user and not request.user.is_superuser:
        messages.error(request, 'Unauthorized submission attempt.')
        return redirect('task_list')

    if request.method == 'POST':
        text = request.POST.get('submission_text', '')
        github_url = request.POST.get('github_url', '')
        attachment = request.FILES.get('attachment')

        prev_count = assignment.submissions.count()
        TaskSubmission.objects.create(
            task_assignment=assignment,
            submission_text=text,
            github_url=github_url,
            attachment=attachment,
            version_number=prev_count + 1
        )

        now = timezone.now()
        is_late = now > assignment.task.deadline
        assignment.submission_status = 'Late Submitted' if is_late else 'Submitted'
        assignment.submission_date = now
        assignment.save()

        AuditLog.objects.create(user=request.user, action="Submitted Task", module="Tasks", record_id=str(assignment.id))
        messages.success(request, 'Task submission uploaded successfully!')
        return redirect('task_detail', id=assignment.task.id)

    return render(request, 'tasks/task_submit.html', {'assignment': assignment})


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
def task_review(request, assignment_id):
    assignment = get_object_or_404(TaskAssignment, id=assignment_id)
    if request.method == 'POST':
        assignment.obtained_marks = request.POST.get('obtained_marks')
        assignment.feedback = request.POST.get('feedback', '')
        assignment.submission_status = 'Reviewed'
        assignment.reviewed_by = request.user
        assignment.save()
        messages.success(request, f'Marks and feedback updated for {assignment.student.username}!')
        return redirect('task_detail', id=assignment.task.id)

    submissions = assignment.submissions.all()
    return render(request, 'tasks/task_review.html', {'assignment': assignment, 'submissions': submissions})


# Daily Reports (PDF Page 18-19)
@login_required
def daily_reports_list(request):
    user = request.user
    if user.is_superuser or user.role in ['super_admin', 'admin', 'trainer', 'team_leader']:
        reports = DailyReport.objects.select_related('student', 'batch').all()
    else:
        reports = DailyReport.objects.filter(student=user).select_related('batch')
    return render(request, 'tasks/daily_reports.html', {'reports': reports})


@login_required
def submit_daily_report(request):
    if request.method == 'POST':
        st_enrollment = request.user.internship_enrollments.first()
        batch = st_enrollment.batch if st_enrollment else None

        DailyReport.objects.create(
            student=request.user,
            batch=batch,
            report_date=request.POST.get('report_date', str(timezone.now().date())),
            today_task=request.POST.get('today_task'),
            completed_work=request.POST.get('completed_work'),
            pending_work=request.POST.get('pending_work', ''),
            github_url=request.POST.get('github_url', ''),
            screenshot=request.FILES.get('screenshot'),
            tomorrow_plan=request.POST.get('tomorrow_plan', '')
        )
        AuditLog.objects.create(user=request.user, action="Submitted Daily Report", module="Tasks")
        messages.success(request, 'Daily report submitted successfully!')
        return redirect('daily_reports_list')

    return render(request, 'tasks/daily_report_form.html')


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
def report_feedback(request, id):
    report = get_object_or_404(DailyReport, id=id)
    if request.method == 'POST':
        if request.user.role == 'team_leader':
            report.team_leader_remarks = request.POST.get('team_leader_remarks', '')
        else:
            report.trainer_feedback = request.POST.get('trainer_feedback', '')
        report.save()
        messages.success(request, 'Feedback saved!')
        return redirect('daily_reports_list')
    return render(request, 'tasks/daily_report_feedback.html', {'report': report})
