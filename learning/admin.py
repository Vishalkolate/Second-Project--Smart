from django.contrib import admin
from .models import CourseModule, Lesson , LessonMaterial, Enrollment


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):

    list_display = (
        'module_title',
        'course',
        'sequence_number',
        'status',
        'created_at',
    )

    search_fields = (
        'module_title',
        'course__course_name',
    )

    list_filter = (
        'status',
        'course',
    )

    ordering = ('course', 'sequence_number')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):

    list_display = (
        'lesson_title',
        'module',
        'sequence_number',
        'duration_minutes',
        'is_free',
        'status',
    )

    search_fields = (
        'lesson_title',
        'module__module_title',
    )

    list_filter = (
        'status',
        'is_free',
        'module',
    )

    ordering = ('module', 'sequence_number')    


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):

    list_display = (
        'material_title',
        'lesson',
        'file_type',
        'uploaded_at',
    )

    search_fields = (
        'material_title',
        'lesson__lesson_title',
    )

    list_filter = (
        'file_type',
        'uploaded_at',
    )

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'course',
        'enrollment_date',
        'enrollment_status',
        'payment_status',
        'completion_date',
    )

    search_fields = (
        'student__username',
        'course__course_name',
    )

    list_filter = (
        'enrollment_status',
        'payment_status',
        'enrollment_date',
    )