from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates Teacher and Student groups and assigns required permissions.'

    def handle(self, *args, **options):
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group, _ = Group.objects.get_or_create(name='Student')

        teacher_permissions = [
            'view_course',
            'add_course',
            'change_course',
            'delete_course',
            'view_assignment',
            'add_assignment',
            'change_assignment',
            'delete_assignment',
            'view_submission',
            'change_submission',
            'can_manage_courses',
            'can_assign_students',
            'can_create_assignments',
            'can_grade_assignments',
            'can_review_submissions',
            'can_access_teacher_dashboard',
        ]

        student_permissions = [
            'view_course',
            'view_assignment',
            'view_submission',
            'add_submission',
            'change_submission',
            'can_submit_assignments',
            'can_access_student_dashboard',
        ]

        for codename in teacher_permissions:
            permission = Permission.objects.filter(codename=codename).first()
            if permission:
                teacher_group.permissions.add(permission)

        for codename in student_permissions:
            permission = Permission.objects.filter(codename=codename).first()
            if permission:
                student_group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS('Teacher and Student groups have been created successfully.'))
