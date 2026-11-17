from django.contrib import admin
from .models import Course, Category


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    list_display = (
        'course_name',
        'course_duration',
        'course_fees',
        'course_status',
        'created_at',
    )

    search_fields = (
        'course_name',
    )

    list_filter = (
        'course_status',
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'category_name',
        'status',
        'created_at',
    )

    search_fields = ('category_name',)

    list_filter = ('status',)