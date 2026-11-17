from django.db import models
from django.conf import settings
import uuid


class Payment(models.Model):
    TYPE_CHOICES = [
        ('Course Fee', 'Course Fee'),
        ('Admission Fee', 'Admission Fee'),
        ('Internship Deposit', 'Internship Deposit'),
        ('Installment', 'Installment Payment'),
    ]

    METHOD_CHOICES = [
        ('UPI', 'UPI / GPay / PhonePe'),
        ('Card', 'Credit / Debit Card'),
        ('NetBanking', 'Internet Banking'),
        ('Cash', 'Cash / Office Receipt'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Course Fee')
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50, choices=METHOD_CHOICES, default='UPI')
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Success')
    receipt_number = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        if not self.receipt_number:
            self.receipt_number = f"REC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - Rs.{self.amount} ({self.student.username})"


class FeeInstallment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Paid', 'Partially Paid'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fee_installments'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    @property
    def remaining_amount(self):
        return max(0, self.total_amount - self.paid_amount)

    def __str__(self):
        return f"{self.student.username} - Due: Rs.{self.total_amount} by {self.due_date}"
