from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('Deadline', 'Deadline Alert'),
        ('Attendance', 'Attendance Alert'),
        ('Exam', 'Exam Alert'),
        ('Internship', 'Internship Update'),
        ('Certificate', 'Certificate Notification'),
        ('Payment', 'Payment Notification'),
        ('General', 'General Notice'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='General')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class EmailLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs'
    )
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    delivery_status = models.CharField(
        max_length=50,
        choices=[('Sent', 'Sent'), ('Failed', 'Failed'), ('Pending', 'Pending')],
        default='Sent'
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email}: {self.subject} ({self.delivery_status})"
