from django.db import models
from django.conf import settings
from django.utils import timezone


class InternshipProgram(models.Model):
    program_name = models.CharField(max_length=200)
    description = models.TextField()
    technology = models.CharField(max_length=200)
    duration_days = models.PositiveIntegerField(default=90)
    start_date = models.DateField()
    end_date = models.DateField()
    application_deadline = models.DateField()
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    eligibility = models.TextField(default='BE/B.Tech/MCA/BCA/Diploma/Graduate in CS/IT or relevant background.')
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Upcoming', 'Upcoming'), ('Closed', 'Closed')],
        default='Active'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.program_name


class InternshipBatch(models.Model):
    batch_name = models.CharField(max_length=150)
    program = models.ForeignKey(
        InternshipProgram,
        on_delete=models.CASCADE,
        related_name='batches'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(default='09:00:00')
    end_time = models.TimeField(default='18:00:00')
    team_leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_batches'
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trained_batches'
    )
    status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Completed', 'Completed'), ('Upcoming', 'Upcoming')],
        default='Active'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch_name} ({self.program.program_name})"


class InternshipApplication(models.Model):
    SELECTION_STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
        ('Onboarding', 'Onboarding'),
        ('Active', 'Active'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Terminated', 'Terminated'),
    ]

    INTERVIEW_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cleared', 'Cleared'),
        ('Failed', 'Failed'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internship_applications'
    )
    program = models.ForeignKey(
        InternshipProgram,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    application_date = models.DateField(auto_now_add=True)
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_status = models.CharField(
        max_length=30,
        choices=INTERVIEW_STATUS_CHOICES,
        default='Pending'
    )
    selection_status = models.CharField(
        max_length=30,
        choices=SELECTION_STATUS_CHOICES,
        default='Applied'
    )
    admin_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.program.program_name} ({self.selection_status})"


class InternshipEnrollment(models.Model):
    application = models.ForeignKey(
        InternshipApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollment'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internship_enrollments'
    )
    program = models.ForeignKey(
        InternshipProgram,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    batch = models.ForeignKey(
        InternshipBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='intern_enrollments'
    )
    joining_date = models.DateField(null=True, blank=True)
    internship_start_date = models.DateField(null=True, blank=True)
    internship_end_date = models.DateField(null=True, blank=True)
    completion_status = models.CharField(
        max_length=30,
        choices=[('Active', 'Active'), ('On Hold', 'On Hold'), ('Completed', 'Completed'), ('Terminated', 'Terminated')],
        default='Active'
    )
    certificate_status = models.CharField(
        max_length=30,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Issued', 'Issued')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.program.program_name}"


class InternshipDocument(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internship_documents'
    )
    document_type = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='internship_documents/')
    verification_status = models.CharField(
        max_length=30,
        choices=[('Pending', 'Pending'), ('Verified', 'Verified'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.document_type} ({self.verification_status})"


class InternshipDeposit(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internship_deposits'
    )
    program = models.ForeignKey(
        InternshipProgram,
        on_delete=models.CASCADE,
        related_name='deposits'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_reference = models.CharField(max_length=100)
    payment_date = models.DateField(auto_now_add=True)
    refund_status = models.CharField(
        max_length=30,
        choices=[('Pending', 'Pending'), ('Refunded', 'Refunded'), ('Non-Refundable', 'Non-Refundable')],
        default='Pending'
    )
    refund_date = models.DateField(null=True, blank=True)
    refund_reference = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.student.username} - Rs.{self.amount} ({self.refund_status})"


class DailyWorkTracking(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_work_trackings'
    )
    date = models.DateField(default=timezone.now)

    # Work Start
    work_start_time = models.TimeField(null=True, blank=True)
    work_expected_end_time = models.TimeField(null=True, blank=True)
    work_start_photo = models.ImageField(upload_to='work_tracking/start/', null=True, blank=True)

    # Morning Tea Break
    morning_tea_start = models.TimeField(null=True, blank=True)
    morning_tea_end = models.TimeField(null=True, blank=True)
    no_morning_tea = models.BooleanField(default=False)

    # Lunch Break
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)

    # Evening Tea Break
    evening_tea_start = models.TimeField(null=True, blank=True)
    evening_tea_end = models.TimeField(null=True, blank=True)
    no_evening_tea = models.BooleanField(default=False)

    # Work Stop
    work_stop_time = models.TimeField(null=True, blank=True)
    work_stop_photo = models.ImageField(upload_to='work_tracking/stop/', null=True, blank=True)
    work_stop_remarks = models.TextField(blank=True)

    # Daily Custom Message / Status
    daily_message = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.username} Work Tracking ({self.date})"

