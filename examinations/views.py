from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
from accounts.decorators import role_required
from accounts.models import AuditLog
from courses.models import Course
from .models import Exam, Question, Option, ExamAttempt, ExamAnswer


@login_required
def exam_list(request):
    is_admin = request.user.is_superuser or request.user.role in ['super_admin', 'admin', 'trainer']
    if is_admin:
        exams = Exam.objects.select_related('course').all()
        courses = Course.objects.all()
        return render(request, 'examinations/exam_list.html', {'exams': exams, 'courses': courses})
    else:
        exams = Exam.objects.filter(status='Published').select_related('course')
        attempts = ExamAttempt.objects.filter(student=request.user).select_related('exam')
        attempted_exam_ids = [a.exam_id for a in attempts]
        return render(request, 'examinations/my_exams.html', {
            'exams': exams,
            'attempts': attempts,
            'attempted_exam_ids': attempted_exam_ids,
        })


@role_required('super_admin', 'admin', 'trainer')
def exam_create(request):
    if request.method == 'POST':
        c_id = request.POST.get('course')
        course = Course.objects.filter(id=c_id).first() if c_id else None

        exam = Exam.objects.create(
            course=course,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            total_marks=int(request.POST.get('total_marks', 100)),
            passing_marks=int(request.POST.get('passing_marks', 40)),
            duration_minutes=int(request.POST.get('duration_minutes', 60)),
            negative_marking=Decimal(request.POST.get('negative_marking', '0.00')),
            start_datetime=request.POST.get('start_datetime'),
            end_datetime=request.POST.get('end_datetime'),
            status=request.POST.get('status', 'Published')
        )
        AuditLog.objects.create(user=request.user, action="Created Exam", module="Examinations", record_id=str(exam.id))
        messages.success(request, 'Exam created successfully! Now add questions.')
        return redirect('exam_questions', exam_id=exam.id)

    courses = Course.objects.all()
    return render(request, 'examinations/exam_form.html', {'courses': courses})


@role_required('super_admin', 'admin', 'trainer')
def exam_questions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        q_text = request.POST.get('question_text')
        q_marks = Decimal(request.POST.get('marks', '1.00'))
        q_neg = Decimal(request.POST.get('negative_marks', '0.00'))
        explanation = request.POST.get('explanation', '')

        question = Question.objects.create(
            exam=exam,
            question_text=q_text,
            question_type='MCQ',
            marks=q_marks,
            negative_marks=q_neg,
            explanation=explanation
        )

        options = request.POST.getlist('option_text')
        correct_index = request.POST.get('correct_option')

        for idx, opt_text in enumerate(options):
            if opt_text.strip():
                Option.objects.create(
                    question=question,
                    option_text=opt_text.strip(),
                    is_correct=(str(idx) == correct_index)
                )

        messages.success(request, 'Question added successfully!')
        return redirect('exam_questions', exam_id=exam.id)

    questions = exam.questions.prefetch_related('options').all()
    return render(request, 'examinations/questions.html', {'exam': exam, 'questions': questions})


@role_required('super_admin', 'admin', 'trainer')
@require_POST
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    exam_id = question.exam_id
    question.delete()
    messages.success(request, 'Question removed.')
    return redirect('exam_questions', exam_id=exam_id)


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.prefetch_related('options').all()
    if not questions.exists():
        messages.warning(request, 'This exam has no questions yet.')
        return redirect('exam_list')

    attempt = ExamAttempt.objects.filter(exam=exam, student=request.user, result_status='In Progress').first()
    if not attempt:
        attempt_count = ExamAttempt.objects.filter(exam=exam, student=request.user).count()
        attempt = ExamAttempt.objects.create(
            exam=exam,
            student=request.user,
            attempt_number=attempt_count + 1
        )

    return render(request, 'examinations/take_exam.html', {
        'exam': exam,
        'questions': questions,
        'attempt': attempt,
    })


@login_required
@require_POST
def submit_exam(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
    if attempt.result_status != 'In Progress':
        return redirect('exam_result', attempt_id=attempt.id)

    exam = attempt.exam
    total_score = Decimal('0.00')

    for question in exam.questions.prefetch_related('options').all():
        selected_opt_id = request.POST.get(f'question_{question.id}')
        if selected_opt_id:
            opt = Option.objects.filter(id=selected_opt_id, question=question).first()
            if opt and opt.is_correct:
                marks_earned = question.marks
                total_score += marks_earned
            else:
                marks_earned = -question.negative_marks
                total_score += marks_earned

            ExamAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=opt,
                marks_obtained=marks_earned
            )

    attempt.obtained_marks = max(Decimal('0.00'), total_score)
    attempt.end_time = timezone.now()
    attempt.result_status = 'Passed' if attempt.obtained_marks >= exam.passing_marks else 'Failed'
    attempt.save()

    AuditLog.objects.create(user=request.user, action="Completed Exam", module="Examinations", record_id=str(exam.id))
    messages.success(request, f'Exam submitted! Score: {attempt.obtained_marks} / {exam.total_marks}')
    return redirect('exam_result', attempt_id=attempt.id)


@login_required
def exam_result(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id)
    if attempt.student != request.user and not (request.user.is_superuser or request.user.role in ['admin', 'trainer']):
        messages.error(request, 'Unauthorized.')
        return redirect('exam_list')

    answers = attempt.answers.select_related('question', 'selected_option').all()
    pct = int((attempt.obtained_marks / attempt.exam.total_marks * 100)) if attempt.exam.total_marks > 0 else 0
    return render(request, 'examinations/exam_result.html', {
        'attempt': attempt,
        'answers': answers,
        'percentage': pct,
    })
