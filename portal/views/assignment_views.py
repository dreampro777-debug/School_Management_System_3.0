from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from portal.models import Assignment, Course


@login_required
@permission_required('portal.can_create_assignments', raise_exception=True)
def assignment_list(request):
    query = request.GET.get('q', '').strip()
    assignments = Assignment.objects.filter(created_by=request.user).select_related('course')

    if query:
        assignments = assignments.filter(title__icontains=query)

    paginator = Paginator(assignments, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'assignment_list.html', {'assignments': page_obj, 'query': query})


@login_required
@permission_required('portal.can_create_assignments', raise_exception=True)
def assignment_create(request):
    courses = Course.objects.filter(created_by=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        course_id = request.POST.get('course')
        due_date = request.POST.get('due_date')

        if title and course_id and due_date:
            course = get_object_or_404(courses, pk=course_id)
            assignment = Assignment.objects.create(
                title=title,
                description=description or '',
                course=course,
                created_by=request.user,
                due_date=timezone.datetime.strptime(due_date, '%Y-%m-%dT%H:%M'),
            )
            messages.success(request, f'Assignment "{assignment.title}" created successfully.')
            return redirect('assignment_list')

    return render(request, 'assignment_form.html', {'courses': courses, 'mode': 'create'})


@login_required
@permission_required('portal.can_create_assignments', raise_exception=True)
def assignment_update(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    courses = Course.objects.filter(created_by=request.user)

    if request.method == 'POST':
        assignment.title = request.POST.get('title') or assignment.title
        assignment.description = request.POST.get('description') or assignment.description
        course_id = request.POST.get('course')
        due_date = request.POST.get('due_date')

        if course_id:
            assignment.course = get_object_or_404(courses, pk=course_id)
        if due_date:
            assignment.due_date = timezone.datetime.strptime(due_date, '%Y-%m-%dT%H:%M')

        assignment.save()
        messages.success(request, f'Assignment "{assignment.title}" updated successfully.')
        return redirect('assignment_list')

    return render(request, 'assignment_form.html', {'assignment': assignment, 'courses': courses, 'mode': 'update'})


@login_required
@permission_required('portal.can_create_assignments', raise_exception=True)
@require_POST
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    title = assignment.title
    assignment.delete()
    messages.success(request, f'Assignment "{title}" deleted successfully.')
    return redirect('assignment_list')
