from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from portal.models import Assignment, Submission


@login_required
@permission_required('portal.can_submit_assignments', raise_exception=True)
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id, course__students=request.user)
    existing_submission = Submission.objects.filter(student=request.user, assignment=assignment).first()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            submission, created = Submission.objects.get_or_create(
                student=request.user,
                assignment=assignment,
            )
            submission.content = content
            submission.save()
            messages.success(request, f'Your submission for "{assignment.title}" was saved successfully.')
            return redirect('student_dashboard')

    return render(request, 'submission_form.html', {
        'assignment': assignment,
        'existing_submission': existing_submission,
    })


@login_required
@permission_required('portal.can_submit_assignments', raise_exception=True)
@require_POST
def delete_submission(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, student=request.user)
    submission.delete()
    messages.success(request, 'Your submission was deleted.')
    return redirect('student_dashboard')


@login_required
@permission_required('portal.can_review_submissions', raise_exception=True)
def review_submissions(request):
    submissions = Submission.objects.filter(
        assignment__course__created_by=request.user
    ).select_related('student', 'assignment__course').order_by('-submitted_at')
    return render(request, 'submission_review.html', {'submissions': submissions})


@login_required
@permission_required('portal.can_grade_assignments', raise_exception=True)
def grade_submission(request, submission_id):
    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        assignment__course__created_by=request.user,
    )

    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '').strip()
        if grade:
            submission.grade = int(grade)
            submission.feedback = feedback
            submission.save()
            messages.success(request, f'Grade saved for {submission.student.get_full_name() or submission.student.username}.')
            return redirect('teacher_dashboard')
        messages.error(request, 'Please enter a valid grade between 0 and 100.')

    return render(request, 'grade_submission.html', {'submission': submission})
