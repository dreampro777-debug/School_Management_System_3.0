from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from portal.forms import AdminUserForm
from portal.models import Assignment, Course, Submission, User


@login_required
def home(request):
    if getattr(request.user, 'is_superuser', False):
        return redirect('admin_dashboard')
    if getattr(request.user, 'is_teacher', False):
        return redirect('teacher_dashboard')
    if getattr(request.user, 'is_student', False):
        return redirect('student_dashboard')

    return render(request, 'home.html')


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('home')

    teachers = User.objects.filter(is_teacher=True).order_by('username')
    students = User.objects.filter(is_student=True).order_by('username')
    courses = Course.objects.select_related('created_by').order_by('-created_at')
    assignments = Assignment.objects.select_related('course', 'created_by').order_by('-created_at')
    submissions = Submission.objects.select_related('student', 'assignment__course').order_by('-submitted_at')

    context = {
        'teachers': teachers,
        'students': students,
        'courses': courses,
        'assignments': assignments,
        'submissions': submissions,
        'total_teachers': teachers.count(),
        'total_students': students.count(),
        'total_courses': courses.count(),
        'total_assignments': assignments.count(),
        'total_submissions': submissions.count(),
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@require_POST
def admin_delete_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    user = get_object_or_404(User, pk=user_id, is_superuser=False)
    if user.pk == request.user.pk:
        messages.error(request, 'You cannot delete your own administrator account.')
        return redirect('admin_dashboard')
    username = user.get_full_name() or user.username
    user.delete()
    messages.success(request, f'User {username} deleted successfully.')
    return redirect('admin_dashboard')


@login_required
def admin_user_create(request):
    if not request.user.is_superuser:
        return redirect('home')

    form = AdminUserForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'{user.get_full_name() or user.username} created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_user_form.html', {'form': form, 'mode': 'create'})


@login_required
def admin_user_update(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')

    user = get_object_or_404(User, pk=user_id, is_superuser=False)
    form = AdminUserForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        updated_user = form.save()
        messages.success(request, f'{updated_user.get_full_name() or updated_user.username} updated successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_user_form.html', {'form': form, 'mode': 'update', 'managed_user': user})
