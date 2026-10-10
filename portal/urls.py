from django.contrib.auth import views as auth_views
from django.urls import path

from .views.assignment_views import (
    assignment_create,
    assignment_delete,
    assignment_list,
    assignment_update,
)
from .views.auth_views import (
    CustomLoginView,
    CustomLogoutView,
    account_profile,
    delete_account,
    register_view,
    verify_otp_view,
)
from .views.base_views import (
    admin_dashboard,
    admin_delete_user,
    admin_user_create,
    admin_user_update,
    home,
)
from .views.course_views import course_create, course_delete, course_list, course_update
from .views.student_views import (
    drop_course,
    enroll_course,
    student_course_catalog,
    student_dashboard,
    student_teacher_directory,
    student_teacher_profile,
    student_note_create,
    student_note_delete,
    student_note_detail,
    student_note_update,
    student_notes,
)
from .views.submission_views import delete_submission, grade_submission, review_submissions, submit_assignment
from .views.teacher_views import teacher_dashboard, teacher_student_directory, teacher_student_profile

urlpatterns = [
    path('', home, name='home'),
    path('super-admin/', admin_dashboard, name='admin_dashboard'),
    path('super-admin/delete-user/<int:user_id>/', admin_delete_user, name='admin_delete_user'),
    path('super-admin/users/create/', admin_user_create, name='admin_user_create'),
    path('super-admin/users/<int:user_id>/update/', admin_user_update, name='admin_user_update'),
    path('register/', register_view, name='register'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('teacher/dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', teacher_student_directory, name='teacher_student_directory'),
    path('teacher/students/<int:student_id>/', teacher_student_profile, name='teacher_student_profile'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
    path('student/courses/', student_course_catalog, name='student_course_catalog'),
    path('student/teachers/', student_teacher_directory, name='student_teacher_directory'),
    path('student/teachers/<int:teacher_id>/', student_teacher_profile, name='student_teacher_profile'),
    path('student/courses/enroll/<int:course_id>/', enroll_course, name='enroll_course'),
    path('student/courses/drop/<int:course_id>/', drop_course, name='drop_course'),
    path('student/notes/', student_notes, name='student_notes'),
    path('student/notes/create/', student_note_create, name='student_note_create'),
    path('student/notes/<int:pk>/', student_note_detail, name='student_note_detail'),
    path('student/notes/<int:pk>/edit/', student_note_update, name='student_note_update'),
    path('student/notes/<int:pk>/delete/', student_note_delete, name='student_note_delete'),
    path('course/list/', course_list, name='course_list'),
    path('course/create/', course_create, name='course_create'),
    path('course/update/<int:pk>/', course_update, name='course_update'),
    path('course/delete/<int:pk>/', course_delete, name='course_delete'),
    path('assignment/list/', assignment_list, name='assignment_list'),
    path('assignment/create/', assignment_create, name='assignment_create'),
    path('assignment/update/<int:pk>/', assignment_update, name='assignment_update'),
    path('assignment/delete/<int:pk>/', assignment_delete, name='assignment_delete'),
    path('submission/submit/<int:assignment_id>/', submit_assignment, name='submit_assignment'),
    path('submission/delete/<int:submission_id>/', delete_submission, name='delete_submission'),
    path('submission/review/', review_submissions, name='review_submissions'),
    path('submission/grade/<int:submission_id>/', grade_submission, name='grade_submission'),
    path('accounts/login/', CustomLoginView.as_view(next_page='home'), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/profile/', account_profile, name='account_profile'),
    path('accounts/delete/', delete_account, name='delete_account'),
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', success_url='/accounts/password-reset/done/'), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html', success_url='/accounts/reset/done/'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
