from django.db import models
from django.conf import settings


class InstructorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_profile'
    )
    designation = models.CharField(max_length=150, default='Lead Trainer')
    qualification = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200)
    experience = models.PositiveIntegerField(default=0)
    joining_date = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='instructor_profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.designation})"


class StaffProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    employee_code = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    joining_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.department} ({self.designation})"
