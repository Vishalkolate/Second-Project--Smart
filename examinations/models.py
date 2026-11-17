from django.db import models
from django.conf import settings


class Exam(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Closed', 'Closed'),
    ]

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    duration_minutes = models.IntegerField(default=60)
    negative_marking = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Published')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    TYPE_CHOICES = [
        ('MCQ', 'Multiple Choice'),
        ('True_False', 'True / False'),
        ('Short_Answer', 'Short Answer'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='MCQ')
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.exam.title} - Q: {self.question_text[:50]}"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.option_text} ({'Correct' if self.is_correct else 'Wrong'})"


class ExamAttempt(models.Model):
    RESULT_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Passed', 'Passed'),
        ('Failed', 'Failed'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    obtained_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    result_status = models.CharField(max_length=20, choices=RESULT_CHOICES, default='In Progress')
    attempt_number = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} ({self.result_status})"


class ExamAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    answer_text = models.TextField(blank=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Attempt {self.attempt.id} - Q {self.question.id}"
