from django.contrib import admin
from .models import InstructorProfile


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'qualification',
        'specialization',
        'experience',
        'joining_date',
    )

    search_fields = (
        'user__username',
        'user__email',
        'specialization',
    )

    list_filter = (
        'specialization',
        'joining_date',
    )