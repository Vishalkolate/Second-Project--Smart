from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from .models import InstructorProfile, StaffProfile


@role_required('super_admin', 'admin', 'hr')
def instructor_list(request):
    data = InstructorProfile.objects.select_related('user').all()
    staff = StaffProfile.objects.select_related('user').all()
    return render(request, 'instructors/instructors.html', {'data': data, 'instructors': data, 'staff': staff})


@role_required('super_admin', 'admin', 'hr')
def instructor_save(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='trainer'
        )

        InstructorProfile.objects.create(
            user=user,
            designation=request.POST.get('designation', 'Trainer'),
            qualification=request.POST.get('qualification', ''),
            specialization=request.POST.get('specialization', ''),
            experience=int(request.POST.get('experience', 0)),
            joining_date=request.POST.get('joining_date') or None,
            bio=request.POST.get('bio', ''),
            address=request.POST.get('address', '')
        )
        AuditLog.objects.create(user=request.user, action="Added Instructor", module="Instructors", record_id=str(user.id))
        messages.success(request, 'Instructor created successfully!')
    return redirect('instructor_list')


@role_required('super_admin', 'admin', 'hr')
def instructor_edit(request, id):
    inst = get_object_or_404(InstructorProfile, id=id)
    return render(request, 'instructors/instructor_edit.html', {'instructor': inst, 'data': inst})


@role_required('super_admin', 'admin', 'hr')
def instructor_update(request, id):
    inst = get_object_or_404(InstructorProfile, id=id)
    if request.method == 'POST':
        u = inst.user
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name = request.POST.get('last_name', u.last_name)
        u.email = request.POST.get('email', u.email)
        u.save()

        inst.designation = request.POST.get('designation', inst.designation)
        inst.qualification = request.POST.get('qualification', inst.qualification)
        inst.specialization = request.POST.get('specialization', inst.specialization)
        inst.experience = int(request.POST.get('experience', 0)) if request.POST.get('experience') else 0
        if request.POST.get('joining_date'):
            inst.joining_date = request.POST.get('joining_date')
        inst.bio = request.POST.get('bio', inst.bio)
        inst.address = request.POST.get('address', inst.address)
        inst.save()

        AuditLog.objects.create(user=request.user, action="Updated Instructor", module="Instructors", record_id=str(inst.id))
        messages.success(request, 'Instructor updated successfully!')
        return redirect('instructor_list')
    return redirect('instructor_list')


@role_required('super_admin', 'admin', 'hr')
@require_POST
def instructor_delete(request, id):
    inst = get_object_or_404(InstructorProfile, id=id)
    user = inst.user
    inst.delete()
    user.delete()
    AuditLog.objects.create(user=request.user, action="Deleted Instructor", module="Instructors", record_id=str(id))
    messages.success(request, 'Instructor removed successfully!')
    return redirect('instructor_list')
