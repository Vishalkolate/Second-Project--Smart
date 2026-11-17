from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.urls import reverse
from accounts.decorators import role_required
from accounts.models import User, AuditLog
from courses.models import Course
from learning.models import Enrollment
from .models import Payment, FeeInstallment


@role_required('super_admin', 'admin', 'accountant')
def payment_list(request):
    payments = Payment.objects.select_related('student', 'course').all().order_by('-payment_date')
    courses = Course.objects.all()
    students = User.objects.filter(role__in=['student', 'intern'])
    return render(request, 'payments/payment_list.html', {
        'payments': payments,
        'courses': courses,
        'students': students,
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
def process_online_payment(request):
    if request.method == 'POST':
        user = request.user
        amount_str = request.POST.get('amount', '').strip()
        course_id = request.POST.get('course_id')
        payment_type = request.POST.get('payment_type', 'Course Fee')
        payment_method = request.POST.get('payment_method', 'UPI')
        installment_id = request.POST.get('installment_id')

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except Exception:
            messages.error(request, 'Please provide a valid payment amount.')
            return redirect(request.META.get('HTTP_REFERER') or 'student_dashboard')

        course = None
        if course_id:
            course = Course.objects.filter(id=course_id).first()

        payment = Payment.objects.create(
            student=user,
            course=course,
            amount=amount,
            payment_type=payment_type,
            payment_method=payment_method,
            payment_status='Success'
        )

        # Update installment if exists
        if installment_id:
            inst = FeeInstallment.objects.filter(id=installment_id, student=user).first()
            if inst:
                inst.paid_amount += amount
                if inst.paid_amount >= inst.total_amount:
                    inst.status = 'Paid'
                else:
                    inst.status = 'Partially Paid'
                inst.save()
        elif course:
            inst = FeeInstallment.objects.filter(student=user, course=course, status__in=['Pending', 'Partially Paid', 'Overdue']).first()
            if inst:
                inst.paid_amount += amount
                if inst.paid_amount >= inst.total_amount:
                    inst.status = 'Paid'
                else:
                    inst.status = 'Partially Paid'
                inst.save()

        # Update enrollment status if fully paid
        if course:
            total_paid_course = Payment.objects.filter(
                student=user, course=course, payment_status='Success'
            ).aggregate(total=Sum('amount'))['total'] or 0
            if course.course_fees and total_paid_course >= course.course_fees:
                Enrollment.objects.filter(student=user, course=course).update(payment_status='Paid')

        AuditLog.objects.create(
            user=user,
            action=f"Online Payment Completed: Rs.{amount} via {payment_method}",
            module="Payments",
            record_id=str(payment.id)
        )

        success_msg = f'Online payment of Rs. {amount} successful! Official Receipt #{payment.receipt_number} generated.'
        messages.success(request, success_msg)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
            return JsonResponse({
                'status': 'success',
                'message': success_msg,
                'payment_id': payment.id,
                'receipt_number': payment.receipt_number,
                'receipt_url': reverse('payment_receipt', args=[payment.id]),
                'amount': str(amount),
                'method': payment_method,
            })

        redirect_to_receipt = request.POST.get('redirect_to_receipt', 'true') == 'true'
        if redirect_to_receipt:
            return redirect('payment_receipt', id=payment.id)
        return redirect(request.META.get('HTTP_REFERER') or 'student_dashboard')

    return redirect('my_payments')


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
    is_staff = request.user.is_superuser or request.user.role in ['admin', 'accountant']
    target_user = request.user
    student_id = request.GET.get('student_id')
    if is_staff and student_id:
        target_user = User.objects.filter(id=student_id).first() or request.user

    payments = Payment.objects.filter(student=target_user).select_related('course').order_by('-payment_date')
    installments = FeeInstallment.objects.filter(student=target_user).select_related('course').order_by('due_date')

    total_paid = payments.filter(payment_status='Success').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    enrollments = Enrollment.objects.filter(student=target_user).select_related('course')
    total_course_fees = sum([e.course.course_fees for e in enrollments if e.course and e.course.course_fees]) or Decimal('0.00')
    pending_fee = max(Decimal('0.00'), total_course_fees - total_paid)
    all_courses = Course.objects.all()

    return render(request, 'payments/my_payments.html', {
        'target_user': target_user,
        'payments': payments,
        'installments': installments,
        'enrollments': enrollments,
        'total_paid': total_paid,
        'total_course_fees': total_course_fees,
        'pending_fee': pending_fee,
        'all_courses': all_courses,
        'is_staff': is_staff,
    })
