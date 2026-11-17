from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from .models import Course, Category
from accounts.models import User, AuditLog


def courses(request):
    category_id = request.GET.get('category')
    search_q = request.GET.get('search')
    courses_qs = Course.objects.all().select_related('category', 'instructor')

    if category_id:
        courses_qs = courses_qs.filter(category_id=category_id)
    if search_q:
        courses_qs = courses_qs.filter(course_name__icontains=search_q)

    categories = Category.objects.filter(status='Active')
    instructors = User.objects.filter(role__in=['trainer', 'admin', 'super_admin'])
    is_staff_user = request.user.is_authenticated and (request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'hr', 'trainer'])
    template = 'courses/courses.html' if is_staff_user else 'public/course_list.html'

    return render(request, template, {
        'data': courses_qs,
        'courses': courses_qs,
        'categories': categories,
        'instructors': instructors,
        'search_q': search_q,
    })


def course_detail(request, id):
    course = get_object_or_404(Course, id=id)
    modules = course.modules.prefetch_related('lessons').filter(status='Active')
    reviews = course.reviews.select_related('student')
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = course.enrollments.filter(student=request.user).exists()

    return render(request, 'public/course_detail.html', {
        'course': course,
        'modules': modules,
        'reviews': reviews,
        'is_enrolled': is_enrolled,
    })


@role_required('super_admin', 'admin', 'hr', 'trainer')
def course_save(request):
    if request.method == 'POST':
        c = Course(
            course_name=request.POST.get('course_name'),
            course_description=request.POST.get('course_description'),
            course_duration=request.POST.get('course_duration'),
            course_fees=request.POST.get('course_fees', 0),
            level=request.POST.get('level', 'Beginner'),
            course_status=request.POST.get('course_status', 'Active'),
        )
        cat_id = request.POST.get('category')
        if cat_id:
            c.category = Category.objects.filter(id=cat_id).first()
        inst_id = request.POST.get('instructor')
        if inst_id:
            c.instructor = User.objects.filter(id=inst_id).first()
        if 'thumbnail' in request.FILES:
            c.thumbnail = request.FILES['thumbnail']
        c.save()
        AuditLog.objects.create(user=request.user, action="Created Course", module="Courses", record_id=str(c.id))
        messages.success(request, 'Course added successfully!')
    return redirect('course_list')


@role_required('super_admin', 'admin', 'hr', 'trainer')
def course_edit(request, id):
    course = get_object_or_404(Course, id=id)
    categories = Category.objects.all()
    instructors = User.objects.filter(role__in=['trainer', 'admin', 'super_admin'])
    return render(request, 'courses/course_edit.html', {
        'course': course,
        'data': course,
        'categories': categories,
        'instructors': instructors,
    })


@role_required('super_admin', 'admin', 'hr', 'trainer')
def course_update(request, id):
    course = get_object_or_404(Course, id=id)
    if request.method == 'POST':
        course.course_name = request.POST.get('course_name')
        course.course_description = request.POST.get('course_description')
        course.course_duration = request.POST.get('course_duration')
        course.course_fees = request.POST.get('course_fees')
        course.level = request.POST.get('level', 'Beginner')
        course.course_status = request.POST.get('course_status', 'Active')
        cat_id = request.POST.get('category')
        course.category = Category.objects.filter(id=cat_id).first() if cat_id else None
        inst_id = request.POST.get('instructor')
        course.instructor = User.objects.filter(id=inst_id).first() if inst_id else None
        if 'thumbnail' in request.FILES:
            course.thumbnail = request.FILES['thumbnail']
        course.save()
        AuditLog.objects.create(user=request.user, action="Updated Course", module="Courses", record_id=str(course.id))
        messages.success(request, 'Course updated successfully!')
        return redirect('course_list')
    return redirect('course_list')


@role_required('super_admin', 'admin', 'hr')
@require_POST
def course_delete(request, id):
    course = get_object_or_404(Course, id=id)
    course.delete()
    AuditLog.objects.create(user=request.user, action="Deleted Course", module="Courses", record_id=str(id))
    messages.success(request, 'Course deleted successfully!')
    return redirect('course_list')


# Categories
@role_required('super_admin', 'admin', 'hr')
def category_list(request):
    data = Category.objects.all()
    return render(request, 'courses/categories.html', {'data': data, 'categories': data})


@role_required('super_admin', 'admin', 'hr')
def category_save(request):
    if request.method == 'POST':
        Category.objects.create(
            category_name=request.POST.get('category_name'),
            description=request.POST.get('description', ''),
            status=request.POST.get('status', 'Active')
        )
        messages.success(request, 'Category added successfully!')
    return redirect('category_list')


@role_required('super_admin', 'admin', 'hr')
def category_edit(request, id):
    category = get_object_or_404(Category, id=id)
    return render(request, 'courses/category_edit.html', {'category': category, 'data': category})


@role_required('super_admin', 'admin', 'hr')
def category_update(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        category.category_name = request.POST.get('category_name')
        category.description = request.POST.get('description', '')
        category.status = request.POST.get('status', 'Active')
        category.save()
        messages.success(request, 'Category updated successfully!')
        return redirect('category_list')
    return redirect('category_list')


@role_required('super_admin', 'admin', 'hr')
@require_POST
def category_delete(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    messages.success(request, 'Category deleted successfully!')
    return redirect('category_list')
