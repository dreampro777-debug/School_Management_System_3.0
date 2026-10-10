from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    class Meta:
        permissions = [
            ("can_access_teacher_dashboard", "Can access teacher dashboard"),
            ("can_access_student_dashboard", "Can access student dashboard"),
        ]

    def __str__(self):
        return self.get_full_name() or self.username


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_courses",
        limit_choices_to={"is_teacher": True},
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="enrolled_courses",
        blank=True,
        limit_choices_to={"is_student": True},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("can_manage_courses", "Can manage courses"),
            ("can_assign_students", "Can assign students to courses"),
        ]

    def __str__(self):
        return self.title


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assignments",
        limit_choices_to={"is_teacher": True},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("can_create_assignments", "Can create assignments"),
            ("can_grade_assignments", "Can grade assignments"),
        ]

    def __str__(self):
        return f"{self.course.title}: {self.title}"


class Submission(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={"is_student": True},
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    content = models.TextField()
    grade = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("student", "assignment")
        permissions = [
            ("can_submit_assignments", "Can submit assignments"),
            ("can_review_submissions", "Can review submissions"),
        ]

    def __str__(self):
        return f"{self.student.username} -> {self.assignment.title}"


class StudyNote(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_notes',
        limit_choices_to={'is_student': True},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        related_name='study_notes',
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        return f'{self.student.username}: {self.title}'
