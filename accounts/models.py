from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        ADMIN = 'admin', 'Admin'
        HR = 'hr', 'HR / Coordinator'
        TRAINER = 'trainer', 'Trainer'
        TEAM_LEADER = 'team_leader', 'Team Leader'
        STUDENT = 'student', 'Student'
        INTERN = 'intern', 'Intern'
        ACCOUNTANT = 'accountant', 'Accountant'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=150)
    module = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.module} ({self.created_at:%Y-%m-%d %H:%M})"


class SystemSetting(models.Model):
    institute_name = models.CharField(max_length=200, default='Smart LMS & Internship Management System')
    tagline = models.CharField(max_length=255, default='Learn, Intern & Build Industry Careers')
    about_text = models.TextField(default='Smart LMS & Internship Management System is an all-in-one comprehensive educational and career accelerator platform connecting students, trainers, coordinators and industry experts.')
    address = models.TextField(default='A2Z IT HUB Complex, Knowledge Park, Pune, Maharashtra 411057')
    email = models.EmailField(default='contact@smartlms.edu')
    phone = models.CharField(max_length=30, default='+91 98765 43210')
    min_video_completion_pct = models.PositiveIntegerField(default=90)
    min_exam_passing_pct = models.PositiveIntegerField(default=40)
    min_attendance_pct = models.PositiveIntegerField(default=75)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.institute_name
