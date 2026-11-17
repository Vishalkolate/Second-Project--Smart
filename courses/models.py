from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    category_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        default='Active'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.category_name


class Course(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught'
    )
    course_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True, null=True)
    course_description = models.TextField()
    course_duration = models.CharField(max_length=100)
    course_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    level = models.CharField(
        max_length=30,
        choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')],
        default='Beginner'
    )
    thumbnail = models.ImageField(upload_to='courses/', blank=True, null=True)
    syllabus_file = models.FileField(upload_to='course_syllabi/', blank=True, null=True)
    course_status = models.CharField(
        max_length=20,
        default='Active'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.course_name:
            self.slug = slugify(self.course_name)
        super().save(*args, **kwargs)

    @property
    def title(self):
        return self.course_name

    @property
    def description(self):
        return self.course_description

    @property
    def duration(self):
        return self.course_duration

    @property
    def fees(self):
        return self.course_fees

    def __str__(self):
        return self.course_name
