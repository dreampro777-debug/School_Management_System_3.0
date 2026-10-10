from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Assignment, Course, Submission

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed realistic demo teachers, students, courses, assignments, and submissions for the school management system.'

    def handle(self, *args, **options):
        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        student_group, _ = Group.objects.get_or_create(name='Student')

        teacher_perm, _ = Permission.objects.get_or_create(codename='can_access_teacher_dashboard', name='Can access teacher dashboard')
        student_perm, _ = Permission.objects.get_or_create(codename='can_access_student_dashboard', name='Can access student dashboard')
        teacher_group.permissions.add(teacher_perm)
        student_group.permissions.add(student_perm)

        demo_users = [
            {'username': 'teacher_alex', 'email': 'alex.teacher@schoolflow.com', 'password': 'Teacher123!', 'first_name': 'Alex', 'last_name': 'Morgan', 'is_teacher': True},
            {'username': 'teacher_lina', 'email': 'lina.teacher@schoolflow.com', 'password': 'Teacher123!', 'first_name': 'Lina', 'last_name': 'Khine', 'is_teacher': True},
            {'username': 'teacher_zayar', 'email': 'zayar.teacher@schoolflow.com', 'password': 'Teacher123!', 'first_name': 'Zayar', 'last_name': 'Tun', 'is_teacher': True},
            {'username': 'student_aye', 'email': 'aye.student@schoolflow.com', 'password': 'Student123!', 'first_name': 'Aye', 'last_name': 'Moe', 'is_student': True},
            {'username': 'student_thura', 'email': 'thura.student@schoolflow.com', 'password': 'Student123!', 'first_name': 'Thura', 'last_name': 'Nay', 'is_student': True},
            {'username': 'student_myo', 'email': 'myo.student@schoolflow.com', 'password': 'Student123!', 'first_name': 'Myo', 'last_name': 'Htet', 'is_student': True},
        ]

        for data in demo_users:
            user, _ = User.objects.get_or_create(username=data['username'])
            user.email = data['email']
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.is_teacher = data.get('is_teacher', False)
            user.is_student = data.get('is_student', False)
            if not user.has_usable_password() or data['username'].startswith('teacher') or data['username'].startswith('student'):
                user.set_password(data['password'])
            user.save()

            if user.is_teacher:
                user.groups.add(teacher_group)
            if user.is_student:
                user.groups.add(student_group)

        teacher1 = User.objects.get(username='teacher_alex')
        teacher2 = User.objects.get(username='teacher_lina')
        teacher3 = User.objects.get(username='teacher_zayar')

        student1 = User.objects.get(username='student_aye')
        student2 = User.objects.get(username='student_thura')
        student3 = User.objects.get(username='student_myo')
        course_data = [
            {
                'title': 'Python Fundamentals',
                'description': 'Build a strong foundation in Python syntax, data structures, and problem solving.',
                'teacher': teacher1,
                'students': [student1, student2, student3],
            },
            {
                'title': 'Web Development Basics',
                'description': 'Create responsive websites with HTML, CSS, JavaScript, and Django.',
                'teacher': teacher2,
                'students': [student1, student3],
            },
            {
                'title': 'Database Design',
                'description': 'Learn SQL, schema planning, normalization, and relational model design.',
                'teacher': teacher3,
                'students': [student2, student3],
            },
            {
                'title': 'UI/UX Prototyping',
                'description': 'Design user-friendly interfaces, wireframes, and modern digital experiences.',
                'teacher': teacher1,
                'students': [student1, student2, student3],
            },
        ]

        created_courses = []
        for item in course_data:
            course, _ = Course.objects.get_or_create(title=item['title'], defaults={'description': item['description'], 'created_by': item['teacher']})
            course.description = item['description']
            course.created_by = item['teacher']
            course.save()
            course.students.set(item['students'])
            created_courses.append(course)

        assignment_specs = [
            {'course': created_courses[0], 'teacher': teacher1, 'title': 'Python Variables and Loops', 'description': 'Write a script that calculates total marks and prints patterns using loops.', 'days': 5},
            {'course': created_courses[0], 'teacher': teacher1, 'title': 'Function Challenge', 'description': 'Build reusable functions for simple data processing.', 'days': 12},
            {'course': created_courses[1], 'teacher': teacher2, 'title': 'Responsive Landing Page', 'description': 'Design a landing page with a hero section, cards, and clear call-to-actions.', 'days': 7},
            {'course': created_courses[1], 'teacher': teacher2, 'title': 'Django Form Practice', 'description': 'Create a small form-based web page and validate user input.', 'days': 18},
            {'course': created_courses[2], 'teacher': teacher3, 'title': 'ER Diagram Exercise', 'description': 'Map a school system into tables and identify key relationships.', 'days': 9},
            {'course': created_courses[2], 'teacher': teacher3, 'title': 'SQL Query Lab', 'description': 'Write queries for joins, filters, and aggregate reports.', 'days': 20},
            {'course': created_courses[3], 'teacher': teacher1, 'title': 'Wireframe Review', 'description': 'Design a low-fi wireframe for a student management dashboard.', 'days': 11},
        ]

        for spec in assignment_specs:
            assignment, _ = Assignment.objects.get_or_create(
                title=spec['title'],
                course=spec['course'],
                defaults={
                    'description': spec['description'],
                    'due_date': timezone.now() + timedelta(days=spec['days']),
                    'created_by': spec['teacher'],
                },
            )
            assignment.description = spec['description']
            assignment.due_date = timezone.now() + timedelta(days=spec['days'])
            assignment.created_by = spec['teacher']
            assignment.save()

        submission_data = [
            (student1, 'Python Variables and Loops', 'Completed code with clear loops and output examples.', 92),
            (student2, 'Python Variables and Loops', 'Strong logic and well-commented solution.', 88),
            (student3, 'Responsive Landing Page', 'Landing page layout matches requirements and uses mobile-friendly styling.', 95),
            (student1, 'ER Diagram Exercise', 'ER diagram was clear and correctly normalized.', 90),
            (student2, 'Wireframe Review', 'Wireframe includes a clean dashboard flow and good hierarchy.', 91),
        ]

        for student, assignment_title, content, grade in submission_data:
            assignment = Assignment.objects.get(title=assignment_title)
            Submission.objects.get_or_create(
                student=student,
                assignment=assignment,
                defaults={
                    'content': content,
                    'grade': grade,
                    'feedback': 'Good work. Please keep improving your structure and clarity.',
                },
            )

        self.stdout.write(self.style.SUCCESS('Realistic demo school data seeded successfully.'))
