from django.db import models
from django.conf import settings


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Closed', 'Closed'),
    ]

    task_title = models.CharField(max_length=200)
    task_description = models.TextField()
    batch = models.ForeignKey(
        'internships.InternshipBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    marks = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    class Meta:
        ordering = ['-assigned_date']

    def __str__(self):
        return self.task_title


class TaskAssignment(models.Model):
    SUBMISSION_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Submitted', 'Submitted'),
        ('Late Submitted', 'Late Submitted'),
        ('Reviewed', 'Reviewed'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    submission_status = models.CharField(max_length=30, choices=SUBMISSION_STATUS_CHOICES, default='Pending')
    submission_date = models.DateTimeField(null=True, blank=True)
    obtained_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tasks')
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ('task', 'student')

    def __str__(self):
        return f"{self.task.task_title} -> {self.student.username} ({self.submission_status})"


class TaskSubmission(models.Model):
    task_assignment = models.ForeignKey(TaskAssignment, on_delete=models.CASCADE, related_name='submissions')
    submission_text = models.TextField(blank=True)
    attachment = models.FileField(upload_to='task_submissions/', null=True, blank=True)
    github_url = models.URLField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    version_number = models.IntegerField(default=1)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Submission v{self.version_number} for {self.task_assignment.task.task_title}"


class DailyReport(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_reports')
    batch = models.ForeignKey('internships.InternshipBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='daily_reports')
    report_date = models.DateField()
    today_task = models.CharField(max_length=255)
    completed_work = models.TextField()
    pending_work = models.TextField(blank=True)
    github_url = models.URLField(blank=True)
    screenshot = models.ImageField(upload_to='daily_reports/', null=True, blank=True)
    tomorrow_plan = models.TextField(blank=True)
    team_leader_remarks = models.TextField(blank=True)
    trainer_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date']

    def __str__(self):
        return f"{self.student.username} Report ({self.report_date})"
