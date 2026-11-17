
from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        'student_code',
        'user',
        'gender',
        'qualification',
        'college_name',
        'passing_year',
    )

    search_fields = (
        'student_code',
        'user__username',
        'user__email',
        'college_name',
    )

    list_filter = (
        'gender',
        'passing_year',
    )
