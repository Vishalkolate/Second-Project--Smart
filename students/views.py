from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from .models import StudentProfile


@role_required('super_admin', 'admin', 'hr', 'trainer', 'team_leader')
def student_list(request):
    search_q = request.GET.get('search', '')
    students = StudentProfile.objects.select_related('user').all()
    if search_q:
        students = students.filter(
            user__first_name__icontains=search_q
        ) | students.filter(
            user__last_name__icontains=search_q
        ) | students.filter(
            student_code__icontains=search_q
        ) | students.filter(
            college_name__icontains=search_q
        )
    return render(request, 'students/student_list.html', {'data': students, 'students': students, 'search_q': search_q})


@role_required('super_admin', 'admin', 'hr')
def add_student(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        role = request.POST.get('role', 'student')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'students/add_student.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )

        code = request.POST.get('student_code') or f"STU-{user.id:04d}"
        profile = StudentProfile.objects.create(
            user=user,
            student_code=code,
            gender=request.POST.get('gender', ''),
            date_of_birth=request.POST.get('date_of_birth') or None,
            qualification=request.POST.get('qualification', ''),
            college_name=request.POST.get('college_name', ''),
            passing_year=int(request.POST.get('passing_year')) if request.POST.get('passing_year') else None,
            address=request.POST.get('address', '')
        )
        if 'profile_photo' in request.FILES:
            profile.profile_photo = request.FILES['profile_photo']
            profile.save()

        AuditLog.objects.create(user=request.user, action="Added Student", module="Students", record_id=str(user.id))
        messages.success(request, f'Student {user.username} created successfully!')
        return redirect('student_list')

    return render(request, 'students/add_student.html')


@role_required('super_admin', 'admin', 'hr')
def edit_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    if request.method == 'POST':
        u = student.user
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name = request.POST.get('last_name', u.last_name)
        u.email = request.POST.get('email', u.email)
        u.phone = request.POST.get('phone', u.phone)
        u.role = request.POST.get('role', u.role)
        u.save()

        student.gender = request.POST.get('gender', student.gender)
        if request.POST.get('date_of_birth'):
            student.date_of_birth = request.POST.get('date_of_birth')
        student.qualification = request.POST.get('qualification', student.qualification)
        student.college_name = request.POST.get('college_name', student.college_name)
        if request.POST.get('passing_year'):
            student.passing_year = int(request.POST.get('passing_year'))
        student.address = request.POST.get('address', student.address)
        if 'profile_photo' in request.FILES:
            student.profile_photo = request.FILES['profile_photo']
        student.save()

        AuditLog.objects.create(user=request.user, action="Updated Student", module="Students", record_id=str(student.id))
        messages.success(request, 'Student updated successfully!')
        return redirect('student_list')

    return render(request, 'students/edit_student.html', {'student': student, 'data': student})


@role_required('super_admin', 'admin', 'hr')
@require_POST
def delete_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    user = student.user
    student.delete()
    user.delete()
    AuditLog.objects.create(user=request.user, action="Deleted Student", module="Students", record_id=str(student_id))
    messages.success(request, 'Student deleted successfully!')
    return redirect('student_list')
