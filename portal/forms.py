from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from portal.models import StudyNote

User = get_user_model()


class SchoolFlowAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, label='Remember me')


class VerifyOTPForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=5,
        label='Verification Code',
        widget=forms.TextInput(attrs={'placeholder': 'Enter 5-digit code', 'inputmode': 'numeric'}),
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        initial='student',
        label='Role',
    )
    profile_image = forms.ImageField(required=False, label='Profile Photo')

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'profile_image', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.profile_image = self.cleaned_data.get('profile_image')
        user.is_student = self.cleaned_data['role'] == 'student'
        user.is_teacher = self.cleaned_data['role'] == 'teacher'

        if commit:
            user.save()
            group_name = 'Teacher' if user.is_teacher else 'Student'
            group = user.groups.model.objects.get_or_create(name=group_name)[0]
            user.groups.add(group)

        return user


class AccountProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'address', 'profile_image')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'profile_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class AdminUserForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[('student', 'Student'), ('teacher', 'Teacher')])
    password1 = forms.CharField(widget=forms.PasswordInput, required=False, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, required=False, label='Confirm password')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'address', 'profile_image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_create = self.instance.pk is None
        self.fields['password1'].required = self.is_create
        self.fields['password2'].required = self.is_create
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-select' if field_name == 'role' else 'form-control'
        self.fields['address'].widget.attrs['rows'] = 3
        self.fields['profile_image'].widget.attrs['accept'] = 'image/*'
        self.fields['password1'].help_text = 'Required for a new account. Leave blank to keep the current password.'
        if self.instance.pk:
            self.fields['role'].initial = 'teacher' if self.instance.is_teacher else 'student'

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 != password2:
            self.add_error('password2', 'The passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data['role']
        user.is_teacher = role == 'teacher'
        user.is_student = role == 'student'
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
            role_group, _ = Group.objects.get_or_create(name='Teacher' if user.is_teacher else 'Student')
            user.groups.set([role_group])
        return user


class StudyNoteForm(forms.ModelForm):
    class Meta:
        model = StudyNote
        fields = ('title', 'course', 'content')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }

    def __init__(self, *args, student, **kwargs):
        super().__init__(*args, **kwargs)
        enrolled_courses = student.enrolled_courses.order_by('title')
        if self.instance.pk and self.instance.course_id:
            enrolled_courses = (enrolled_courses | enrolled_courses.model.objects.filter(
                pk=self.instance.course_id,
            )).distinct().order_by('title')
        self.fields['course'].queryset = enrolled_courses
        self.fields['course'].required = False
        self.fields['course'].empty_label = 'Personal note (no course)'
