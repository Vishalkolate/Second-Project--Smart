
from django.db import models
from django.conf import settings


class StudentProfile(models.Model):

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    student_code = models.CharField(
        max_length=30,
        unique=True
    )

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    qualification = models.CharField(
        max_length=100,
        blank=True
    )

    college_name = models.CharField(
        max_length=200,
        blank=True
    )

    passing_year = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    profile_photo = models.ImageField(
        upload_to='student_profiles/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_code} - {self.user.username}"
