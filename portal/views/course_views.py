from datetime import timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST

from portal.models import Assignment, Course


@login_required
@permission_required('portal.can_manage_courses', raise_exception=True)
def course_list(request):
    query = request.GET.get('q', '').strip()
    courses = Course.objects.filter(created_by=request.user).prefetch_related('students')

    if query:
        courses = courses.filter(title__icontains=query)

    paginator = Paginator(courses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'course_list.html', {'courses': page_obj, 'query': query})


@login_required
@permission_required('portal.can_manage_courses', raise_exception=True)
def course_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title:
            course = Course.objects.create(
                title=title,
                description=description or '',
                created_by=request.user,
            )
            Assignment.objects.create(
                title=f'{course.title} Review',
                description='Complete this assignment for the course. Please submit your work before the due date.',
                due_date=timezone.now() + timedelta(days=7),
                course=course,
                created_by=request.user,
            )
            messages.success(request, f'Course "{course.title}" created successfully.')
            return redirect('course_list')

    return render(request, 'course_form.html', {'mode': 'create'})


@login_required
@permission_required('portal.can_manage_courses', raise_exception=True)
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk, created_by=request.user)

    if request.method == 'POST':
        course.title = request.POST.get('title') or course.title
        course.description = request.POST.get('description') or course.description
        course.save()
        messages.success(request, f'Course "{course.title}" updated successfully.')
        return redirect('course_list')

    return render(request, 'course_form.html', {'course': course, 'mode': 'update'})


@login_required
@permission_required('portal.can_manage_courses', raise_exception=True)
@require_POST
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, created_by=request.user)
    course_title = course.title
    course.delete()
    messages.success(request, f'Course "{course_title}" deleted successfully.')
    return redirect('course_list')
