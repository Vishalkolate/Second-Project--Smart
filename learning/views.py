from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from courses.models import Course
from .models import CourseModule, Lesson, LessonMaterial, Enrollment, LessonProgress, CourseReview


@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'learning/my_courses.html', {'enrollments': enrollments})


@login_required
def course_portal(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if not enrollment and not (request.user.is_superuser or request.user.role in ['admin', 'trainer']):
        messages.warning(request, 'You must enroll in this course first.')
        return redirect('course_detail', id=course.id)

    modules = course.modules.prefetch_related('lessons__materials').filter(status='Active')
    selected_lesson_id = request.GET.get('lesson')
    selected_lesson = None
    if selected_lesson_id:
        selected_lesson = Lesson.objects.filter(id=selected_lesson_id, module__course=course).first()
    if not selected_lesson and modules.exists():
        first_mod = modules.first()
        selected_lesson = first_mod.lessons.first()

    # Progress stats
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = 0
    if enrollment:
        completed_lessons = LessonProgress.objects.filter(enrollment=enrollment, progress_status='completed').count()
    progress_pct = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0

    return render(request, 'learning/course_portal.html', {
        'course': course,
        'modules': modules,
        'selected_lesson': selected_lesson,
        'enrollment': enrollment,
        'progress_pct': progress_pct,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
    })


@login_required
@require_POST
def mark_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=lesson.module.course)
    prog, created = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    prog.progress_status = 'completed'
    prog.completed_at = timezone.now()
    prog.save()
    messages.success(request, f'Marked "{lesson.lesson_title}" as completed!')
    return redirect(f"/learning/course/{lesson.module.course.id}/?lesson={lesson.id}")


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'enrollment_status': 'Active', 'payment_status': 'Paid'}
    )
    if created:
        AuditLog.objects.create(user=request.user, action="Enrolled in Course", module="Learning", record_id=str(course.id))
        messages.success(request, f'Successfully enrolled in {course.course_name}!')
    else:
        messages.info(request, 'You are already enrolled in this course.')
    return redirect('course_portal', course_id=course.id)


@login_required
@require_POST
def add_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    rating = int(request.POST.get('rating', 5))
    review_text = request.POST.get('review', '')
    CourseReview.objects.create(student=request.user, course=course, rating=rating, review=review_text)
    messages.success(request, 'Thank you for your feedback!')
    return redirect('course_detail', id=course.id)


# Module Management
@role_required('super_admin', 'admin', 'hr', 'trainer')
def module_list(request):
    data = CourseModule.objects.select_related('course').all()
    courses = Course.objects.all()
    return render(request, 'learning/modules.html', {'data': data, 'modules': data, 'courses': courses})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def module_save(request):
    if request.method == 'POST':
        c_id = request.POST.get('course')
        course = get_object_or_404(Course, id=c_id)
        CourseModule.objects.create(
            course=course,
            module_title=request.POST.get('module_title'),
            module_description=request.POST.get('module_description', ''),
            sequence_number=int(request.POST.get('sequence_number', 1)),
            status=request.POST.get('status', 'Active')
        )
        messages.success(request, 'Module created successfully!')
    return redirect('module_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
def module_edit(request, id):
    module = get_object_or_404(CourseModule, id=id)
    courses = Course.objects.all()
    return render(request, 'learning/module_edit.html', {'module': module, 'data': module, 'courses': courses})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def module_update(request, id):
    module = get_object_or_404(CourseModule, id=id)
    if request.method == 'POST':
        module.course_id = request.POST.get('course')
        module.module_title = request.POST.get('module_title')
        module.module_description = request.POST.get('module_description', '')
        module.sequence_number = int(request.POST.get('sequence_number', 1))
        module.status = request.POST.get('status', 'Active')
        module.save()
        messages.success(request, 'Module updated successfully!')
        return redirect('module_list')
    return redirect('module_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
@require_POST
def module_delete(request, id):
    module = get_object_or_404(CourseModule, id=id)
    module.delete()
    messages.success(request, 'Module deleted successfully!')
    return redirect('module_list')


# Lesson Management
@role_required('super_admin', 'admin', 'hr', 'trainer')
def lesson_list(request):
    data = Lesson.objects.select_related('module__course').all()
    modules = CourseModule.objects.all()
    return render(request, 'learning/lessons.html', {'data': data, 'lessons': data, 'modules': modules})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def lesson_save(request):
    if request.method == 'POST':
        mod_id = request.POST.get('module')
        module = get_object_or_404(CourseModule, id=mod_id)
        Lesson.objects.create(
            module=module,
            lesson_title=request.POST.get('lesson_title'),
            lesson_description=request.POST.get('lesson_description', ''),
            video_url=request.POST.get('video_url', ''),
            duration_minutes=int(request.POST.get('duration_minutes', 0)),
            sequence_number=int(request.POST.get('sequence_number', 1)),
            is_free='is_free' in request.POST,
            status=request.POST.get('status', 'Active')
        )
        messages.success(request, 'Lesson added successfully!')
    return redirect('lesson_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
def lesson_edit(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    modules = CourseModule.objects.all()
    return render(request, 'learning/lesson_edit.html', {'lesson': lesson, 'data': lesson, 'modules': modules})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def lesson_update(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    if request.method == 'POST':
        lesson.module_id = request.POST.get('module')
        lesson.lesson_title = request.POST.get('lesson_title')
        lesson.lesson_description = request.POST.get('lesson_description', '')
        lesson.video_url = request.POST.get('video_url', '')
        lesson.duration_minutes = int(request.POST.get('duration_minutes', 0))
        lesson.sequence_number = int(request.POST.get('sequence_number', 1))
        lesson.is_free = 'is_free' in request.POST
        lesson.status = request.POST.get('status', 'Active')
        lesson.save()
        messages.success(request, 'Lesson updated successfully!')
        return redirect('lesson_list')
    return redirect('lesson_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
@require_POST
def lesson_delete(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    lesson.delete()
    messages.success(request, 'Lesson deleted successfully!')
    return redirect('lesson_list')


# Materials
@role_required('super_admin', 'admin', 'hr', 'trainer')
def material_list(request):
    data = LessonMaterial.objects.select_related('lesson__module__course').all()
    lessons = Lesson.objects.all()
    return render(request, 'learning/materials.html', {'data': data, 'materials': data, 'lessons': lessons})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def material_save(request):
    if request.method == 'POST' and 'file_path' in request.FILES:
        les_id = request.POST.get('lesson')
        lesson = get_object_or_404(Lesson, id=les_id)
        f = request.FILES['file_path']
        ftype = f.name.split('.')[-1].upper() if '.' in f.name else 'FILE'
        LessonMaterial.objects.create(
            lesson=lesson,
            material_title=request.POST.get('material_title'),
            file_path=f,
            file_type=ftype
        )
        messages.success(request, 'Material uploaded successfully!')
    return redirect('material_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
def material_edit(request, id):
    material = get_object_or_404(LessonMaterial, id=id)
    lessons = Lesson.objects.all()
    return render(request, 'learning/material_edit.html', {'material': material, 'data': material, 'lessons': lessons})


@role_required('super_admin', 'admin', 'hr', 'trainer')
def material_update(request, id):
    material = get_object_or_404(LessonMaterial, id=id)
    if request.method == 'POST':
        material.lesson_id = request.POST.get('lesson')
        material.material_title = request.POST.get('material_title')
        if 'file_path' in request.FILES:
            material.file_path = request.FILES['file_path']
            material.file_type = material.file_path.name.split('.')[-1].upper()
        material.save()
        messages.success(request, 'Material updated!')
        return redirect('material_list')
    return redirect('material_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
@require_POST
def material_delete(request, id):
    mat = get_object_or_404(LessonMaterial, id=id)
    mat.delete()
    messages.success(request, 'Material deleted!')
    return redirect('material_list')


# Enrollments
@role_required('super_admin', 'admin', 'hr')
def enrollment_list(request):
    data = Enrollment.objects.select_related('student', 'course').all()
    students = User.objects.filter(role__in=['student', 'intern'])
    courses = Course.objects.all()
    return render(request, 'learning/enrollments.html', {'data': data, 'enrollments': data, 'students': students, 'courses': courses})


@role_required('super_admin', 'admin', 'hr')
def enrollment_save(request):
    if request.method == 'POST':
        student = get_object_or_404(User, id=request.POST.get('student'))
        course = get_object_or_404(Course, id=request.POST.get('course'))
        Enrollment.objects.create(
            student=student,
            course=course,
            enrollment_status=request.POST.get('enrollment_status', 'Active'),
            payment_status=request.POST.get('payment_status', 'Paid'),
        )
        messages.success(request, 'Enrollment recorded successfully!')
    return redirect('enrollment_list')


@role_required('super_admin', 'admin', 'hr')
def enrollment_edit(request, id):
    enrollment = get_object_or_404(Enrollment, id=id)
    students = User.objects.filter(role__in=['student', 'intern'])
    courses = Course.objects.all()
    return render(request, 'learning/enrollment_edit.html', {'enrollment': enrollment, 'data': enrollment, 'students': students, 'courses': courses})


@role_required('super_admin', 'admin', 'hr')
def enrollment_update(request, id):
    enrollment = get_object_or_404(Enrollment, id=id)
    if request.method == 'POST':
        enrollment.enrollment_status = request.POST.get('enrollment_status')
        enrollment.payment_status = request.POST.get('payment_status')
        enrollment.save()
        messages.success(request, 'Enrollment updated successfully!')
        return redirect('enrollment_list')
    return redirect('enrollment_list')


@role_required('super_admin', 'admin', 'hr')
@require_POST
def enrollment_delete(request, id):
    e = get_object_or_404(Enrollment, id=id)
    e.delete()
    messages.success(request, 'Enrollment deleted!')
    return redirect('enrollment_list')
