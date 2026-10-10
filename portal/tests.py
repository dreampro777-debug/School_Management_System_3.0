from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image


class RegisterUploadTests(TestCase):
    def test_register_page_uses_multipart_form_for_profile_photo(self):
        response = self.client.get('/register/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('enctype="multipart/form-data"', response.content.decode())
        self.assertIn('name="profile_image"', response.content.decode())


class OtpVerificationTests(TestCase):
    def test_register_redirects_to_otp_verification_page(self):
        response = Client(enforce_csrf_checks=False).post('/register/', {
            'username': 'newotpuser',
            'email': 'otp@example.com',
            'role': 'student',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }, follow=True)

        self.assertRedirects(response, '/verify-otp/')
        self.assertContains(response, 'Verify your email')


class AuthMessageTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='demo_teacher',
            email='demo@example.com',
            password='StrongPass123!',
            is_teacher=True,
        )
        self.user.user_permissions.add(Permission.objects.get(codename='can_access_teacher_dashboard'))
        self.csrf_client = Client(enforce_csrf_checks=False)

    def test_invalid_login_shows_error_message(self):
        response = self.csrf_client.post('/accounts/login/', {
            'username': 'missing_user',
            'password': 'wrongpass',
        }, follow=True)

        self.assertContains(response, 'Invalid username or password')
        self.assertContains(response, 'Please try again')

    def test_valid_login_shows_success_message(self):
        response = self.csrf_client.post('/accounts/login/', {
            'username': 'demo_teacher',
            'password': 'StrongPass123!',
        }, follow=True)

        self.assertContains(response, 'Logged in successfully')

    def test_password_reset_redirects_to_done_page(self):
        self.User.objects.create_user(
            username='reset_user',
            email='reset@example.com',
            password='StrongPass123!',
        )

        response = self.client.post('/accounts/password-reset/', {'email': 'reset@example.com'}, follow=True)

        self.assertRedirects(response, '/accounts/password-reset/done/')
        self.assertContains(response, 'Check your email')


class StudentLoginLogoutCsrfTests(TestCase):
    def test_student_can_log_in_and_log_out_with_csrf_checks_enabled(self):
        User = get_user_model()
        student = User.objects.create_user(
            username='csrf_student',
            email='csrf_student@example.com',
            password='StrongPass123!',
            is_student=True,
        )
        student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))
        csrf_client = Client(enforce_csrf_checks=True)

        login_page = csrf_client.get('/accounts/login/')
        self.assertEqual(login_page.status_code, 200)
        csrf_token = csrf_client.cookies['csrftoken'].value
        login_response = csrf_client.post('/accounts/login/', {
            'username': 'csrf_student',
            'password': 'StrongPass123!',
            'csrfmiddlewaretoken': csrf_token,
        })
        self.assertRedirects(login_response, '/', fetch_redirect_response=False)

        dashboard = csrf_client.get('/student/dashboard/')
        self.assertEqual(dashboard.status_code, 200)
        csrf_token = csrf_client.cookies['csrftoken'].value
        logout_response = csrf_client.post('/accounts/logout/', {
            'csrfmiddlewaretoken': csrf_token,
        })
        self.assertRedirects(logout_response, '/accounts/login/', fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', csrf_client.session)


class PanelAccessTests(TestCase):
    def test_admin_teacher_student_panels_and_core_crud_routes_are_accessible(self):
        User = get_user_model()

        admin = User.objects.create_superuser(
            username='admin_panel_check',
            email='admin_panel_check@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin)
        admin_response = self.client.get('/super-admin/')
        self.assertEqual(admin_response.status_code, 200)

        teacher = User.objects.create_user(
            username='teacher_panel_check',
            email='teacher_panel_check@example.com',
            password='StrongPass123!',
            is_teacher=True,
        )
        teacher.user_permissions.add(
            Permission.objects.get(codename='can_access_teacher_dashboard'),
            Permission.objects.get(codename='can_manage_courses'),
            Permission.objects.get(codename='can_create_assignments'),
        )
        self.client.force_login(teacher)
        teacher_dashboard_response = self.client.get('/teacher/dashboard/')
        self.assertEqual(teacher_dashboard_response.status_code, 200)
        self.assertContains(teacher_dashboard_response, 'href="/accounts/profile/"')
        self.assertNotContains(teacher_dashboard_response, 'Delete account')
        course_list_response = self.client.get('/course/list/')
        self.assertEqual(course_list_response.status_code, 200)
        assignment_list_response = self.client.get('/assignment/list/')
        self.assertEqual(assignment_list_response.status_code, 200)

        student = User.objects.create_user(
            username='student_panel_check',
            email='student_panel_check@example.com',
            password='StrongPass123!',
            is_student=True,
        )
        student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))
        self.client.force_login(student)
        student_dashboard_response = self.client.get('/student/dashboard/')
        self.assertEqual(student_dashboard_response.status_code, 200)
        self.assertContains(student_dashboard_response, 'href="/accounts/profile/"')
        self.assertNotContains(student_dashboard_response, 'Delete account')
        self.assertContains(student_dashboard_response, 'aria-label="Account details"')
        self.assertContains(student_dashboard_response, 'bi-person-vcard')
        self.assertContains(student_dashboard_response, 'class="navbar-user-summary"')
        self.assertNotContains(student_dashboard_response, '<a class="navbar-user-summary"')
        self.assertNotContains(student_dashboard_response, 'Hi, student_panel_check')
        self.assertContains(student_dashboard_response, 'Welcome back, student_panel_check.')
        self.assertContains(student_dashboard_response, 'Toggle navigation')
        catalog_response = self.client.get('/student/courses/')
        self.assertEqual(catalog_response.status_code, 200)


class ProfileBrowsingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.teacher = User.objects.create_user(
            username='profile_teacher',
            email='private.teacher@example.com',
            password='StrongPass123!',
            first_name='Taylor',
            last_name='Teacher',
            phone='555-0101',
            address='Private teacher address',
            is_teacher=True,
        )
        self.other_teacher = User.objects.create_user(
            username='other_profile_teacher',
            email='other.private.teacher@example.com',
            password='StrongPass123!',
            is_teacher=True,
        )
        self.student = User.objects.create_user(
            username='profile_student',
            email='private.student@example.com',
            password='StrongPass123!',
            first_name='Sam',
            last_name='Student',
            phone='555-0102',
            address='Private student address',
            is_student=True,
        )
        self.other_student = User.objects.create_user(
            username='other_profile_student',
            email='other.private.student@example.com',
            password='StrongPass123!',
            is_student=True,
        )
        self.teacher.user_permissions.add(Permission.objects.get(codename='can_access_teacher_dashboard'))
        self.other_teacher.user_permissions.add(Permission.objects.get(codename='can_access_teacher_dashboard'))
        self.student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))

        from portal.models import Assignment, Course, Submission

        own_course = Course.objects.create(
            title='Teacher Owned Course',
            description='Public course overview',
            created_by=self.teacher,
        )
        other_course = Course.objects.create(title='Other Teacher Course', created_by=self.other_teacher)
        own_assignment = Assignment.objects.create(
            title='Own Course Assignment',
            description='Private assignment prompt',
            due_date='2026-12-31T12:00:00Z',
            course=own_course,
            created_by=self.teacher,
        )
        other_assignment = Assignment.objects.create(
            title='Other Teacher Assignment',
            description='Other prompt',
            due_date='2026-12-31T12:00:00Z',
            course=other_course,
            created_by=self.other_teacher,
        )
        own_course.students.add(self.student)
        Submission.objects.create(
            student=self.student,
            assignment=own_assignment,
            content='Private student submission answer',
        )
        Submission.objects.create(
            student=self.other_student,
            assignment=other_assignment,
            content='Another student answer',
        )

    def test_teacher_sees_only_students_who_submitted_to_their_courses(self):
        self.client.force_login(self.teacher)

        response = self.client.get('/teacher/students/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sam Student')
        self.assertNotContains(response, 'other_profile_student')
        self.assertContains(response, '1 submission')

    def test_teacher_student_profile_is_scoped_and_hides_private_fields(self):
        self.client.force_login(self.teacher)

        response = self.client.get(f'/teacher/students/{self.student.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Own Course Assignment')
        self.assertNotContains(response, 'Other Teacher Assignment')
        self.assertNotContains(response, 'private.student@example.com')
        self.assertNotContains(response, '555-0102')
        self.assertNotContains(response, 'Private student address')
        self.assertNotContains(response, 'Private student submission answer')

    def test_teacher_cannot_open_a_student_with_no_submission_to_their_courses(self):
        self.client.force_login(self.teacher)

        response = self.client.get(f'/teacher/students/{self.other_student.pk}/')

        self.assertEqual(response.status_code, 404)

    def test_student_can_browse_all_teacher_profiles_without_private_contact_details(self):
        self.client.force_login(self.student)

        directory_response = self.client.get('/student/teachers/')
        profile_response = self.client.get(f'/student/teachers/{self.teacher.pk}/')

        self.assertEqual(directory_response.status_code, 200)
        self.assertContains(directory_response, 'Taylor Teacher')
        self.assertContains(directory_response, 'other_profile_teacher')
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, 'Teacher Owned Course')
        self.assertNotContains(profile_response, 'private.teacher@example.com')
        self.assertNotContains(profile_response, '555-0101')
        self.assertNotContains(profile_response, 'Private teacher address')


class AccountDeletionTests(TestCase):
    def test_admin_deleting_user_removes_the_profile_image_file(self):
        User = get_user_model()
        admin = User.objects.create_superuser(
            username='image_delete_admin',
            email='image_delete_admin@example.com',
            password='StrongPass123!',
        )
        user = User.objects.create_user(
            username='image_delete_student',
            password='StrongPass123!',
            is_student=True,
        )
        image = BytesIO()
        Image.new('RGB', (32, 32), color='red').save(image, format='PNG')
        image.seek(0)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            user.profile_image.save(
                'profile.png',
                SimpleUploadedFile('profile.png', image.read(), content_type='image/png'),
            )
            image_path = user.profile_image.path
            self.client.force_login(admin)

            response = self.client.post(f'/super-admin/delete-user/{user.pk}/')

            self.assertRedirects(response, '/super-admin/')
            self.assertFalse(User.objects.filter(pk=user.pk).exists())
            self.assertFalse(Path(image_path).exists())

    def test_student_can_confirm_and_delete_account_and_related_records(self):
        User = get_user_model()
        teacher = User.objects.create_user(username='delete_teacher', password='StrongPass123!', is_teacher=True)
        student = User.objects.create_user(username='delete_student', password='StrongPass123!', is_student=True)
        from portal.models import Assignment, Course, StudyNote, Submission

        course = Course.objects.create(title='Delete Course', created_by=teacher)
        course.students.add(student)
        assignment = Assignment.objects.create(
            title='Delete Assignment',
            description='Answer',
            due_date='2026-12-31T12:00:00Z',
            course=course,
            created_by=teacher,
        )
        submission = Submission.objects.create(student=student, assignment=assignment, content='Answer')
        note = StudyNote.objects.create(student=student, course=course, title='Delete Note', content='Notes')

        self.client.force_login(student)
        confirmation = self.client.get('/accounts/delete/')
        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, 'Permanently delete account')

        response = self.client.post('/accounts/delete/')

        self.assertRedirects(response, '/accounts/login/', fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=student.pk).exists())
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())
        self.assertFalse(StudyNote.objects.filter(pk=note.pk).exists())
        self.assertFalse(course.students.filter(pk=student.pk).exists())

    def test_teacher_deletion_removes_owned_courses_and_assignments(self):
        User = get_user_model()
        teacher = User.objects.create_user(username='delete_teacher_owner', password='StrongPass123!', is_teacher=True)
        student = User.objects.create_user(username='delete_teacher_student', password='StrongPass123!', is_student=True)
        from portal.models import Assignment, Course, Submission

        course = Course.objects.create(title='Owned Course', created_by=teacher)
        course.students.add(student)
        assignment = Assignment.objects.create(
            title='Owned Assignment',
            description='Answer',
            due_date='2026-12-31T12:00:00Z',
            course=course,
            created_by=teacher,
        )
        submission = Submission.objects.create(student=student, assignment=assignment, content='Answer')

        self.client.force_login(teacher)
        response = self.client.post('/accounts/delete/')

        self.assertRedirects(response, '/accounts/login/', fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=teacher.pk).exists())
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())
        self.assertFalse(Assignment.objects.filter(pk=assignment.pk).exists())
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())

    def test_admin_cannot_use_self_delete_endpoint(self):
        admin = get_user_model().objects.create_superuser(
            username='delete_admin',
            email='delete_admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin)

        response = self.client.get('/accounts/delete/')

        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertTrue(get_user_model().objects.filter(pk=admin.pk).exists())


class AccountProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='profile_student',
            email='profile@example.com',
            password='StrongPass123!',
            is_student=True,
        )
        self.client.force_login(self.user)

    def test_student_can_update_profile_and_photo(self):
        image = BytesIO()
        Image.new('RGB', (80, 80), color='green').save(image, format='PNG')
        image.seek(0)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post('/accounts/profile/', {
                'form_type': 'profile',
                'username': 'updated_profile_student',
                'first_name': 'Taylor',
                'last_name': 'Student',
                'email': 'updated@example.com',
                'phone': '555-0100',
                'address': '12 School Road',
                'profile_image': SimpleUploadedFile('profile.png', image.read(), content_type='image/png'),
            })

            self.assertRedirects(response, '/accounts/profile/')
            self.user.refresh_from_db()
            self.assertEqual(self.user.username, 'updated_profile_student')
            self.assertEqual(self.user.email, 'updated@example.com')
            self.assertEqual(self.user.phone, '555-0100')
            self.assertTrue(self.user.profile_image)

    def test_student_can_change_password_without_being_logged_out(self):
        response = self.client.post('/accounts/profile/', {
            'form_type': 'password',
            'old_password': 'StrongPass123!',
            'new_password1': 'DifferentStrong456!',
            'new_password2': 'DifferentStrong456!',
        })

        self.assertRedirects(response, '/accounts/profile/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('DifferentStrong456!'))
        self.assertEqual(self.client.get('/accounts/profile/').status_code, 200)

    def test_admin_cannot_access_profile_page(self):
        admin = get_user_model().objects.create_superuser(
            username='profile_admin',
            email='profile_admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin)

        response = self.client.get('/accounts/profile/')

        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_account_deletion_is_available_from_profile_settings(self):
        response = self.client.get('/accounts/profile/')

        self.assertContains(response, 'Danger zone')
        self.assertContains(response, 'Delete account')


class GradeSubmissionFlowTests(TestCase):
    def test_course_creation_creates_default_assignment_for_enrolled_students(self):
        User = get_user_model()

        teacher = User.objects.create_user(
            username='teacher_default_assignment',
            email='teacher_default@example.com',
            password='StrongPass123!',
            is_teacher=True,
        )
        teacher.user_permissions.add(
            Permission.objects.get(codename='can_access_teacher_dashboard'),
            Permission.objects.get(codename='can_manage_courses'),
            Permission.objects.get(codename='can_create_assignments'),
        )

        student = User.objects.create_user(
            username='student_default_assignment',
            email='student_default@example.com',
            password='StrongPass123!',
            is_student=True,
        )
        student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))

        from portal.models import Assignment, Course

        course = Course.objects.create(
            title='Intro to Biology',
            description='Biology basics',
            created_by=teacher,
        )
        course.students.add(student)

        self.assertTrue(Assignment.objects.filter(course=course, created_by=teacher).exists())
        self.assertEqual(course.assignments.count(), 1)

        self.client.force_login(student)
        response = self.client.get('/student/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Intro to Biology')

    def test_student_dashboard_shows_teacher_grade_and_feedback(self):
        User = get_user_model()

        teacher = User.objects.create_user(
            username='teacher_grade',
            email='teacher_grade@example.com',
            password='StrongPass123!',
            is_teacher=True,
        )
        teacher.user_permissions.add(
            Permission.objects.get(codename='can_access_teacher_dashboard'),
            Permission.objects.get(codename='can_grade_assignments'),
            Permission.objects.get(codename='can_review_submissions'),
        )

        student = User.objects.create_user(
            username='student_grade',
            email='student_grade@example.com',
            password='StrongPass123!',
            is_student=True,
        )
        student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))

        from portal.models import Assignment, Course, Submission

        course = Course.objects.create(title='Math 101', created_by=teacher)
        course.students.add(student)

        assignment = Assignment.objects.create(
            title='Quiz 1',
            description='Solve the quiz',
            due_date='2026-12-31T12:00:00Z',
            course=course,
            created_by=teacher,
        )

        submission = Submission.objects.create(
            student=student,
            assignment=assignment,
            content='I completed the quiz.',
            grade=88,
            feedback='Excellent work. Keep improving.',
        )

        self.client.force_login(student)
        response = self.client.get('/student/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grade: 88 / 100')
        self.assertContains(response, 'Excellent work. Keep improving.')

    def test_teacher_registration_keeps_uploaded_profile_image(self):
        User = get_user_model()

        image = BytesIO()
        Image.new('RGB', (120, 120), color='blue').save(image, format='PNG')
        image.seek(0)

        register_response = self.client.post('/register/', {
            'username': 'teacher_with_photo',
            'email': 'teacherphoto@example.com',
            'role': 'teacher',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'Teacher',
            'last_name': 'Profile',
            'profile_image': SimpleUploadedFile('teacher.png', image.read(), content_type='image/png'),
        }, follow=True)

        self.assertRedirects(register_response, '/verify-otp/')
        self.assertIn('pending_registration', self.client.session)

        pending = self.client.session['pending_registration']
        otp = self.client.session['pending_otp']
        verify_response = self.client.post('/verify-otp/', {'otp_code': otp}, follow=True)

        self.assertRedirects(verify_response, '/teacher/dashboard/')
        user = User.objects.get(username='teacher_with_photo')
        self.assertTrue(user.profile_image)
        self.assertIn('teacher', user.profile_image.name.lower())


class StudentSubmissionCrudTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(
            username='submission_owner',
            password='StrongPass123!',
            is_student=True,
        )
        self.student.user_permissions.add(
            Permission.objects.get(codename='can_submit_assignments'),
            Permission.objects.get(codename='can_access_student_dashboard'),
        )
        self.teacher = User.objects.create_user(
            username='submission_teacher',
            password='StrongPass123!',
            is_teacher=True,
        )
        from portal.models import Assignment, Course, Submission

        course = Course.objects.create(title='CRUD Course', created_by=self.teacher)
        course.students.add(self.student)
        assignment = Assignment.objects.create(
            title='CRUD Assignment',
            description='Answer the question.',
            due_date='2026-12-31T12:00:00Z',
            course=course,
            created_by=self.teacher,
        )
        self.submission = Submission.objects.create(
            student=self.student,
            assignment=assignment,
            content='My answer',
        )

    def test_student_dashboard_shows_amber_submit_and_update_actions(self):
        from portal.models import Assignment

        Assignment.objects.create(
            title='Pending CRUD Assignment',
            description='A new task.',
            due_date='2026-12-31T12:00:00Z',
            course=self.submission.assignment.course,
            created_by=self.teacher,
        )
        self.client.force_login(self.student)

        response = self.client.get('/student/dashboard/')

        self.assertContains(response, 'btn-student-action btn-dashboard-compact">Update')
        self.assertContains(response, 'btn-student-action">Submit</a>')
        self.assertNotContains(response, 'Submit work')

    def test_student_can_read_update_and_delete_own_submission(self):
        self.client.force_login(self.student)
        response = self.client.get('/student/dashboard/')
        self.assertContains(response, 'CRUD Assignment')

        response = self.client.get(f'/submission/submit/{self.submission.assignment_id}/')
        self.assertContains(response, 'My answer')

        response = self.client.post(
            f'/submission/submit/{self.submission.assignment_id}/',
            {'content': 'Updated answer'},
        )
        self.assertRedirects(response, '/student/dashboard/')
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.content, 'Updated answer')

        response = self.client.post(
            f'/submission/delete/{self.submission.pk}/',
            follow=True,
        )
        self.assertRedirects(response, '/student/dashboard/')
        self.assertFalse(self.submission.__class__.objects.filter(pk=self.submission.pk).exists())

    def test_student_cannot_delete_another_students_submission_or_delete_by_get(self):
        other_student = get_user_model().objects.create_user(
            username='other_submission_student',
            password='StrongPass123!',
            is_student=True,
        )
        other_student.user_permissions.add(Permission.objects.get(codename='can_submit_assignments'))
        self.client.force_login(other_student)

        response = self.client.get(f'/submission/delete/{self.submission.pk}/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.submission.__class__.objects.filter(pk=self.submission.pk).exists())

        response = self.client.post(f'/submission/delete/{self.submission.pk}/')
        self.assertEqual(response.status_code, 404)


class StudentStudyNoteCrudTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(
            username='notes_owner',
            password='StrongPass123!',
            is_student=True,
        )
        self.student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))
        self.other_student = User.objects.create_user(
            username='other_notes_owner',
            password='StrongPass123!',
            is_student=True,
        )
        self.other_student.user_permissions.add(Permission.objects.get(codename='can_access_student_dashboard'))
        self.teacher = User.objects.create_user(
            username='notes_teacher',
            password='StrongPass123!',
            is_teacher=True,
        )
        from portal.models import Course

        self.course = Course.objects.create(title='Note Course', created_by=self.teacher)
        self.course.students.add(self.student)

    def test_student_can_create_read_update_search_and_delete_note(self):
        self.client.force_login(self.student)
        response = self.client.get('/student/notes/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/student/notes/create/', {
            'title': 'Revision points',
            'course': str(self.course.pk),
            'content': 'Review the key ideas before the quiz.',
        })
        note = self.student.study_notes.get(title='Revision points')
        self.assertRedirects(response, f'/student/notes/{note.pk}/')
        self.assertEqual(note.course, self.course)
        self.assertContains(self.client.get(f'/student/notes/{note.pk}/'), 'Review the key ideas before the quiz.')

        response = self.client.post(f'/student/notes/{note.pk}/edit/', {
            'title': 'Updated revision points',
            'course': str(self.course.pk),
            'content': 'Review the updated ideas.',
        })
        self.assertRedirects(response, f'/student/notes/{note.pk}/')
        note.refresh_from_db()
        self.assertEqual(note.title, 'Updated revision points')

        response = self.client.get('/student/notes/?q=updated')
        self.assertContains(response, 'Updated revision points')
        response = self.client.post(f'/student/notes/{note.pk}/delete/', follow=True)
        self.assertRedirects(response, '/student/notes/')
        self.assertFalse(self.student.study_notes.filter(pk=note.pk).exists())

    def test_student_notes_are_private_and_course_choices_are_limited(self):
        self.client.force_login(self.student)
        response = self.client.post('/student/notes/create/', {
            'title': 'Private note',
            'course': '',
            'content': 'Only my account should see this.',
        })
        note = self.student.study_notes.get(title='Private note')
        self.assertRedirects(response, f'/student/notes/{note.pk}/')

        self.client.force_login(self.other_student)
        self.assertEqual(self.client.get(f'/student/notes/{note.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/student/notes/{note.pk}/edit/').status_code, 404)
        self.assertEqual(self.client.get(f'/student/notes/{note.pk}/delete/').status_code, 405)
        self.assertEqual(self.client.post(f'/student/notes/{note.pk}/delete/').status_code, 404)

        response = self.client.post('/student/notes/create/', {
            'title': 'Invalid course note',
            'course': str(self.course.pk),
            'content': 'This course is not enrolled by the current student.',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.other_student.study_notes.filter(title='Invalid course note').exists())


class AdminUserCrudTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username='crud_admin',
            email='crud_admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(self.admin)

    def test_admin_can_create_update_and_delete_a_role_user(self):
        response = self.client.get('/super-admin/users/create/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/super-admin/users/create/', {
            'username': 'managed_teacher',
            'first_name': 'Managed',
            'last_name': 'Teacher',
            'email': 'managed_teacher@example.com',
            'phone': '555-0123',
            'address': 'School Street',
            'role': 'teacher',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, '/super-admin/')
        managed_user = get_user_model().objects.get(username='managed_teacher')
        self.assertTrue(managed_user.is_teacher)
        self.assertFalse(managed_user.is_student)
        self.assertTrue(managed_user.check_password('StrongPass123!'))

        response = self.client.post(f'/super-admin/users/{managed_user.pk}/update/', {
            'username': 'managed_teacher',
            'first_name': 'Managed',
            'last_name': 'Student',
            'email': 'managed_student@example.com',
            'phone': '',
            'address': '',
            'role': 'student',
            'password1': '',
            'password2': '',
        })
        self.assertRedirects(response, '/super-admin/')
        managed_user.refresh_from_db()
        self.assertFalse(managed_user.is_teacher)
        self.assertTrue(managed_user.is_student)
        self.assertTrue(managed_user.check_password('StrongPass123!'))

        response = self.client.get(f'/super-admin/delete-user/{managed_user.pk}/')
        self.assertEqual(response.status_code, 405)
        response = self.client.post(f'/super-admin/delete-user/{managed_user.pk}/')
        self.assertRedirects(response, '/super-admin/')
        self.assertFalse(get_user_model().objects.filter(pk=managed_user.pk).exists())


class TeacherAssignmentSuccessMessageTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.teacher = User.objects.create_user(
            username='assignment_message_teacher',
            password='StrongPass123!',
            is_teacher=True,
        )
        self.teacher.user_permissions.add(Permission.objects.get(codename='can_create_assignments'))
        from portal.models import Course

        self.course = Course.objects.create(title='Message Course', created_by=self.teacher)
        self.client.force_login(self.teacher)

    def test_assignment_create_update_delete_show_success_messages(self):
        response = self.client.post('/assignment/create/', {
            'title': 'First Draft',
            'description': 'Write a short response.',
            'course': str(self.course.pk),
            'due_date': '2026-12-31T12:00',
        }, follow=True)
        self.assertContains(response, 'First Draft')
        self.assertContains(response, 'created successfully')
        from portal.models import Assignment

        assignment = Assignment.objects.get(title='First Draft', created_by=self.teacher)
        response = self.client.post(f'/assignment/update/{assignment.pk}/', {
            'title': 'Final Draft',
            'description': 'Write a revised response.',
            'course': str(self.course.pk),
            'due_date': '2027-01-10T12:00',
        }, follow=True)
        self.assertContains(response, 'Final Draft')
        self.assertContains(response, 'updated successfully')

        response = self.client.post(f'/assignment/delete/{assignment.pk}/', follow=True)
        self.assertContains(response, 'Final Draft')
        self.assertContains(response, 'deleted successfully')
