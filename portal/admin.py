from django.contrib import admin

from portal.models import Assignment, Course, Submission, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_student', 'is_teacher', 'is_staff', 'is_superuser')
    list_filter = ('is_student', 'is_teacher', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    list_filter = ('created_by',)
    search_fields = ('title', 'description')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_by', 'due_date')
    list_filter = ('course', 'created_by')
    search_fields = ('title', 'description')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'grade', 'submitted_at')
    list_filter = ('student', 'assignment')
    search_fields = ('student__username', 'assignment__title')
