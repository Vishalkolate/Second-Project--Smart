from django.db import models
from django.conf import settings
import uuid


class CertificateTemplate(models.Model):
    name = models.CharField(max_length=100)
    title_text = models.CharField(max_length=200, default='Certificate of Completion')
    body_template = models.TextField(default='This is to certify that {student_name} has successfully completed {program_title} on {date}.')
    signatory_name = models.CharField(max_length=100, default='Program Director')
    signatory_title = models.CharField(max_length=100, default='Director & Technical Lead')

    def __str__(self):
        return self.name


class Certificate(models.Model):
    TYPE_CHOICES = [
        ('Course Completion', 'Course Completion Certificate'),
        ('Internship', 'Internship Completion Certificate'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates'
    )
    internship_program = models.ForeignKey(
        'internships.InternshipProgram',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates'
    )
    certificate_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Course Completion')
    certificate_number = models.CharField(max_length=60, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    qr_code_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    is_verified = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            prefix = 'LMS-CERT' if self.certificate_type == 'Course Completion' else 'INT-CERT'
            self.certificate_number = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def recipient_name(self):
        return self.student.get_full_name() or self.student.username

    @property
    def target_title(self):
        if self.course:
            return self.course.course_name
        if self.internship_program:
            return self.internship_program.program_name
        return "Professional Development Program"

    def __str__(self):
        return f"{self.certificate_number} - {self.student.username}"
