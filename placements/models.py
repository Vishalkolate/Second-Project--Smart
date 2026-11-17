from django.db import models
from django.conf import settings


class Company(models.Model):
    company_name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name


class JobVacancy(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='vacancies')
    job_title = models.CharField(max_length=200)
    description = models.TextField()
    eligibility = models.TextField()
    salary_package = models.CharField(max_length=100, blank=True)
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[('Open', 'Open'), ('Closed', 'Closed')],
        default='Open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_title} at {self.company.company_name}"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
    ]

    vacancy = models.ForeignKey(JobVacancy, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    resume = models.FileField(upload_to='job_resumes/', null=True, blank=True)
    application_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vacancy', 'student')

    def __str__(self):
        return f"{self.student.username} -> {self.vacancy.job_title} ({self.application_status})"


class MockInterview(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mock_interviews')
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conducted_interviews'
    )
    interview_date = models.DateTimeField()
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')

    def __str__(self):
        return f"Mock: {self.student.username} with {self.interviewer.username} ({self.status})"
