from django.urls import path
from . import views

urlpatterns = [
    path('my-courses/', views.my_courses, name='my_courses'),
    path('course/<int:course_id>/', views.course_portal, name='course_portal'),
    path('course/<int:course_id>/review/', views.add_review, name='add_review'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('lesson/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),

    # Modules
    path('modules/', views.module_list, name='module_list'),
    path('modules/save/', views.module_save, name='module_save'),
    path('modules/edit/<int:id>/', views.module_edit, name='module_edit'),
    path('modules/update/<int:id>/', views.module_update, name='module_update'),
    path('modules/delete/<int:id>/', views.module_delete, name='module_delete'),

    # Lessons
    path('lessons/', views.lesson_list, name='lesson_list'),
    path('lessons/save/', views.lesson_save, name='lesson_save'),
    path('lessons/edit/<int:id>/', views.lesson_edit, name='lesson_edit'),
    path('lessons/update/<int:id>/', views.lesson_update, name='lesson_update'),
    path('lessons/delete/<int:id>/', views.lesson_delete, name='lesson_delete'),

    # Materials
    path('materials/', views.material_list, name='material_list'),
    path('materials/save/', views.material_save, name='material_save'),
    path('materials/edit/<int:id>/', views.material_edit, name='material_edit'),
    path('materials/update/<int:id>/', views.material_update, name='material_update'),
    path('materials/delete/<int:id>/', views.material_delete, name='material_delete'),

    # Enrollments
    path('enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/save/', views.enrollment_save, name='enrollment_save'),
    path('enrollments/edit/<int:id>/', views.enrollment_edit, name='enrollment_edit'),
    path('enrollments/update/<int:id>/', views.enrollment_update, name='enrollment_update'),
    path('enrollments/delete/<int:id>/', views.enrollment_delete, name='enrollment_delete'),
]
