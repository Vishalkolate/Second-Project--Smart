from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from courses.models import Course
from .models import Payment, FeeInstallment


@login_required
def payment_list(request):
    user = request.user
    is_finance = user.is_superuser or user.role in ['super_admin', 'admin', 'accountant']
    if is_finance:
        payments = Payment.objects.select_related('student', 'course').all().order_by('-payment_date')
        courses = Course.objects.all()
        students = User.objects.filter(role__in=['student', 'intern'])
        return render(request, 'payments/payment_list.html', {
            'payments': payments,
            'courses': courses,
            'students': students,
        })
    else:
        # Student / Intern view of their fee ledger, receipts and installments
        payments = Payment.objects.filter(student=user).select_related('course').order_by('-payment_date')
        installments = FeeInstallment.objects.filter(student=user).select_related('course')
        return render(request, 'payments/my_payments.html', {
            'payments': payments,
            'installments': installments,
        })


@role_required('super_admin', 'admin', 'accountant')
def payment_create(request):
    if request.method == 'POST':
        student = get_object_or_404(User, id=request.POST.get('student'))
        course = Course.objects.filter(id=request.POST.get('course')).first() if request.POST.get('course') else None

        payment = Payment.objects.create(
            student=student,
            course=course,
            amount=request.POST.get('amount'),
            payment_type=request.POST.get('payment_type', 'Course Fee'),
            payment_method=request.POST.get('payment_method', 'UPI'),
            payment_status=request.POST.get('payment_status', 'Success')
        )
        AuditLog.objects.create(user=request.user, action="Recorded Payment", module="Payments", record_id=str(payment.id))
        messages.success(request, f'Payment recorded with Receipt #{payment.receipt_number}')
    return redirect('payment_list')


@login_required
def payment_receipt(request, id):
    payment = get_object_or_404(Payment, id=id)
    if payment.student != request.user and not (request.user.is_superuser or request.user.role in ['admin', 'accountant']):
        messages.error(request, 'Unauthorized.')
        return redirect('dashboard')
    return render(request, 'payments/receipt.html', {'payment': payment})


@role_required('super_admin', 'admin', 'accountant')
def installment_list(request):
    installments = FeeInstallment.objects.select_related('student', 'course').all()
    courses = Course.objects.all()
    students = User.objects.filter(role__in=['student', 'intern'])
    return render(request, 'payments/installments.html', {
        'installments': installments,
        'courses': courses,
        'students': students,
    })


@role_required('super_admin', 'admin', 'accountant')
def installment_create(request):
    if request.method == 'POST':
        student = get_object_or_404(User, id=request.POST.get('student'))
        course = Course.objects.filter(id=request.POST.get('course')).first() if request.POST.get('course') else None

        FeeInstallment.objects.create(
            student=student,
            course=course,
            total_amount=request.POST.get('total_amount'),
            paid_amount=request.POST.get('paid_amount', 0),
            due_date=request.POST.get('due_date'),
            status=request.POST.get('status', 'Pending')
        )
        messages.success(request, 'Installment schedule recorded!')
    return redirect('installment_list')


@login_required
def my_payments(request):
    payments = Payment.objects.filter(student=request.user).select_related('course').order_by('-payment_date')
    installments = FeeInstallment.objects.filter(student=request.user).select_related('course')
    return render(request, 'payments/my_payments.html', {
        'payments': payments,
        'installments': installments,
    })
