from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render

from portal.models import Assignment, Course, Submission

User = get_user_model()


@permission_required('portal.can_access_teacher_dashboard', raise_exception=True)
def teacher_dashboard(request):
    courses = Course.objects.filter(created_by=request.user).prefetch_related('students')
    assignments = Assignment.objects.filter(created_by=request.user).select_related('course')
    recent_submissions = Submission.objects.filter(
        assignment__course__created_by=request.user
    ).select_related('student', 'assignment__course').order_by('-submitted_at')[:6]
    graded_count = Submission.objects.filter(
        assignment__course__created_by=request.user,
        grade__isnull=False,
    ).count()

    total_courses = courses.count()
    total_assignments = assignments.count()
    total_submissions = recent_submissions.count()

    context = {
        'courses': courses,
        'assignments': assignments,
        'recent_submissions': recent_submissions,
        'graded_count': graded_count,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
    }
    return render(request, 'teacher_dashboard.html', context)


@permission_required('portal.can_access_teacher_dashboard', raise_exception=True)
def teacher_student_directory(request):
    if not request.user.is_teacher:
        return redirect('home')

    query = request.GET.get('q', '').strip()
    teacher_submissions = Q(submissions__assignment__course__created_by=request.user)
    students = User.objects.filter(
        is_student=True,
        is_active=True,
        submissions__assignment__course__created_by=request.user,
    ).annotate(
        submission_count=Count('submissions', filter=teacher_submissions, distinct=True),
        latest_submission=Max('submissions__submitted_at', filter=teacher_submissions),
    )
    if query:
        students = students.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    students = students.order_by('last_name', 'first_name', 'username')
    return render(request, 'teacher_student_directory.html', {
        'students': students,
        'query': query,
    })


@permission_required('portal.can_access_teacher_dashboard', raise_exception=True)
def teacher_student_profile(request, student_id):
    if not request.user.is_teacher:
        return redirect('home')

    student = get_object_or_404(
        User.objects.filter(
            is_student=True,
            is_active=True,
            submissions__assignment__course__created_by=request.user,
        ).distinct(),
        pk=student_id,
    )
    submissions = Submission.objects.filter(
        student=student,
        assignment__course__created_by=request.user,
    ).select_related('assignment__course').order_by('-submitted_at')
    return render(request, 'public_profile.html', {
        'profile_user': student,
        'profile_role': 'Student',
        'student_submissions': submissions,
    })
