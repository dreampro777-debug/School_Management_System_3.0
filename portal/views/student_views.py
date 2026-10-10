from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from portal.forms import StudyNoteForm
from portal.models import Assignment, Course, StudyNote, Submission

User = get_user_model()


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_dashboard(request):
    enrolled_courses = Course.objects.filter(students=request.user).prefetch_related('assignments')
    assignments = Assignment.objects.filter(course__students=request.user).select_related('course').order_by('due_date')
    submissions = Submission.objects.filter(student=request.user).select_related('assignment__course')
    notes = StudyNote.objects.filter(student=request.user).select_related('course')
    submission_by_assignment = {submission.assignment_id: submission for submission in submissions}
    assignment_rows = []
    for assignment in assignments:
        assignment_rows.append({
            'assignment': assignment,
            'submission': submission_by_assignment.get(assignment.pk),
        })
    available_courses = Course.objects.exclude(students=request.user).select_related('created_by').order_by('-created_at')[:3]

    total_courses = enrolled_courses.count()
    total_assignments = assignments.count()
    total_submissions = submissions.count()

    context = {
        'enrolled_courses': enrolled_courses,
        'assignments': assignments,
        'assignment_rows': assignment_rows,
        'submissions': submissions,
        'recent_notes': notes[:3],
        'available_courses': available_courses,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'total_notes': notes.count(),
    }
    return render(request, 'student_dashboard.html', context)


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_course_catalog(request):
    query = request.GET.get('q', '').strip()
    enrolled_courses = Course.objects.filter(students=request.user)
    available_courses = Course.objects.exclude(students=request.user).select_related('created_by').order_by('-created_at')

    if query:
        available_courses = available_courses.filter(
            title__icontains=query
        ) | available_courses.filter(
            created_by__username__icontains=query
        ) | available_courses.filter(
            created_by__first_name__icontains=query
        ) | available_courses.filter(
            created_by__last_name__icontains=query
        )
        available_courses = available_courses.distinct()

    context = {
        'enrolled_courses': enrolled_courses,
        'available_courses': available_courses,
        'query': query,
    }
    return render(request, 'student_course_catalog.html', context)


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_teacher_directory(request):
    if not request.user.is_student:
        return redirect('home')

    query = request.GET.get('q', '').strip()
    teachers = User.objects.filter(is_teacher=True, is_active=True).annotate(
        course_count=Count('created_courses', distinct=True),
    )
    if query:
        teachers = teachers.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(created_courses__title__icontains=query)
        ).distinct()

    teachers = teachers.order_by('last_name', 'first_name', 'username')
    return render(request, 'student_teacher_directory.html', {
        'teachers': teachers,
        'query': query,
    })


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_teacher_profile(request, teacher_id):
    if not request.user.is_student:
        return redirect('home')

    teacher = get_object_or_404(User, pk=teacher_id, is_teacher=True, is_active=True)
    courses = Course.objects.filter(created_by=teacher).order_by('title')
    return render(request, 'public_profile.html', {
        'profile_user': teacher,
        'profile_role': 'Teacher',
        'teacher_courses': courses,
    })


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_notes(request):
    query = request.GET.get('q', '').strip()
    notes = StudyNote.objects.filter(student=request.user).select_related('course')
    if query:
        notes = notes.filter(Q(title__icontains=query) | Q(content__icontains=query))
    return render(request, 'student_notes.html', {'notes': notes, 'query': query})


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_note_detail(request, pk):
    note = get_object_or_404(StudyNote.objects.select_related('course'), pk=pk, student=request.user)
    return render(request, 'student_note_detail.html', {'note': note})


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_note_create(request):
    form = StudyNoteForm(request.POST or None, student=request.user)
    if request.method == 'POST' and form.is_valid():
        note = form.save(commit=False)
        note.student = request.user
        note.save()
        messages.success(request, 'Study note created.')
        return redirect('student_note_detail', pk=note.pk)
    return render(request, 'student_note_form.html', {'form': form, 'mode': 'create'})


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
def student_note_update(request, pk):
    note = get_object_or_404(StudyNote, pk=pk, student=request.user)
    form = StudyNoteForm(request.POST or None, instance=note, student=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Study note updated.')
        return redirect('student_note_detail', pk=note.pk)
    return render(request, 'student_note_form.html', {'form': form, 'mode': 'update', 'note': note})


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
@require_POST
def student_note_delete(request, pk):
    note = get_object_or_404(StudyNote, pk=pk, student=request.user)
    note.delete()
    messages.success(request, 'Study note deleted.')
    return redirect('student_notes')


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
@require_POST
def enroll_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if course.students.filter(pk=request.user.pk).exists():
        messages.info(request, 'You are already enrolled in this course.')
    else:
        course.students.add(request.user)
        messages.success(request, f'You have successfully enrolled in {course.title}.')

    return redirect('student_course_catalog')


@login_required
@permission_required('portal.can_access_student_dashboard', raise_exception=True)
@require_POST
def drop_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    if course.students.filter(pk=request.user.pk).exists():
        course.students.remove(request.user)
        messages.success(request, f'You have dropped {course.title}.')
    else:
        messages.info(request, 'You are not enrolled in this course.')

    return redirect('student_course_catalog')
