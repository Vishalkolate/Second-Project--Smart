from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from .models import Project, ProjectMember, ProjectMilestone, ProjectSubmission


@login_required
def project_list(request):
    user = request.user
    if user.is_superuser or user.role in ['super_admin', 'admin', 'trainer', 'team_leader']:
        projects = Project.objects.select_related('assigned_by').all().order_by('-created_at')
        return render(request, 'projects/project_list.html', {'projects': projects})
    else:
        memberships = ProjectMember.objects.filter(student=user).select_related('project')
        projects = [m.project for m in memberships]
        if not projects:
            projects = list(Project.objects.all().order_by('-created_at'))
        user_submissions = {s.project_id: s for s in ProjectSubmission.objects.filter(student=user)}
        return render(request, 'projects/my_projects.html', {
            'projects': projects,
            'user_submissions': user_submissions,
        })


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
def project_create(request):
    if request.method == 'POST':
        project = Project.objects.create(
            project_name=request.POST.get('project_name'),
            description=request.POST.get('description'),
            assigned_by=request.user,
            deadline=request.POST.get('deadline'),
            status='In Progress'
        )

        member_ids = request.POST.getlist('members')
        for m_id in member_ids:
            stu = User.objects.filter(id=m_id).first()
            if stu:
                ProjectMember.objects.create(project=project, student=stu, role='Developer')

        AuditLog.objects.create(user=request.user, action="Created Project", module="Projects", record_id=str(project.id))
        messages.success(request, 'Project created and assigned!')
        return redirect('project_detail', id=project.id)

    students = User.objects.filter(role__in=['intern', 'student'])
    return render(request, 'projects/project_form.html', {'students': students})


@login_required
def project_detail(request, id):
    project = get_object_or_404(Project, id=id)
    members = project.members.select_related('student')
    milestones = project.milestones.all()
    submissions = project.submissions.select_related('student')
    user_submission = submissions.filter(student=request.user).first() if request.user.is_authenticated else None
    return render(request, 'projects/project_detail.html', {
        'project': project,
        'members': members,
        'milestones': milestones,
        'submissions': submissions,
        'user_submission': user_submission,
    })


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
def milestone_add(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        ProjectMilestone.objects.create(
            project=project,
            milestone_name=request.POST.get('milestone_name'),
            deadline=request.POST.get('deadline'),
            status='Pending'
        )
        messages.success(request, 'Milestone added!')
    return redirect('project_detail', id=project.id)


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
@require_POST
def milestone_toggle(request, milestone_id):
    ms = get_object_or_404(ProjectMilestone, id=milestone_id)
    ms.status = 'Completed' if ms.status == 'Pending' else 'Pending'
    ms.save()
    messages.success(request, f'Milestone status changed to {ms.status}!')
    return redirect('project_detail', id=ms.project_id)


@login_required
def project_submit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        github_url = request.POST.get('github_url', '')
        remarks = request.POST.get('remarks', '')

        sub, created = ProjectSubmission.objects.update_or_create(
            project=project,
            student=request.user,
            defaults={
                'github_url': github_url,
                'review_status': 'Pending',
                'remarks': remarks,
            }
        )
        if 'attachment' in request.FILES:
            sub.attachment = request.FILES['attachment']
            sub.save()

        AuditLog.objects.create(user=request.user, action="Submitted Project", module="Projects", record_id=str(project.id))
        messages.success(request, f'Project deliverables for "{project.project_name}" uploaded successfully for mentor evaluation!')
        return redirect('project_detail', id=project.id)

    existing_sub = ProjectSubmission.objects.filter(project=project, student=request.user).first()
    return render(request, 'projects/project_submit.html', {'project': project, 'existing_sub': existing_sub})


@role_required('super_admin', 'admin', 'trainer', 'team_leader')
@require_POST
def submission_review(request, submission_id):
    sub = get_object_or_404(ProjectSubmission, id=submission_id)
    status = request.POST.get('review_status', 'Approved')
    sub.review_status = status
    sub.remarks = request.POST.get('remarks', '')
    sub.save()
    if status == 'Approved':
        sub.project.status = 'Approved'
        sub.project.save()
    AuditLog.objects.create(user=request.user, action=f"Reviewed Project ({status})", module="Projects", record_id=str(sub.id))
    messages.success(request, f'Project submission marked as {status}!')
    return redirect('project_detail', id=sub.project_id)
