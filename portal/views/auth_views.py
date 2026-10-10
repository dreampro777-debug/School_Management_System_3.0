import random
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from portal.forms import AccountProfileForm, RegisterForm, SchoolFlowAuthenticationForm, VerifyOTPForm

User = get_user_model()


@login_required
@require_http_methods(["GET", "POST"])
def account_profile(request):
    if request.user.is_superuser or not (request.user.is_teacher or request.user.is_student):
        return redirect('home')

    if request.method == 'POST' and request.POST.get('form_type') == 'profile':
        profile_form = AccountProfileForm(request.POST, request.FILES, instance=request.user)
        password_form = PasswordChangeForm(request.user)
        if profile_form.is_valid():
            old_profile_image = request.user.profile_image
            updated_user = profile_form.save()
            new_image_name = updated_user.profile_image.name if updated_user.profile_image else None
            if old_profile_image and old_profile_image.name != new_image_name:
                old_profile_image.delete(save=False)
            messages.success(request, 'Your account details have been updated.')
            return redirect('account_profile')
    elif request.method == 'POST' and request.POST.get('form_type') == 'password':
        profile_form = AccountProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            updated_user = password_form.save()
            update_session_auth_hash(request, updated_user)
            messages.success(request, 'Your password has been changed.')
            return redirect('account_profile')
    elif request.method == 'GET':
        profile_form = AccountProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
    else:
        messages.error(request, 'Choose which account information you want to update.')
        return redirect('account_profile')

    for field in password_form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    return render(request, 'account_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    if request.user.is_superuser or not (request.user.is_teacher or request.user.is_student):
        return redirect('home')

    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('login')

    return render(request, 'account_delete.html')


def generate_otp_code():
    return str(random.randint(10000, 99999))


def save_pending_profile_image(uploaded_file):
    if not uploaded_file:
        return ''

    extension = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else 'png'
    filename = f'pending_profiles/{uuid.uuid4()}.{extension}'
    saved_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
    return saved_path


def send_otp_email(user_email, otp_code):
    subject = 'SchoolFlow email verification code'
    text_message = (
        f'Your SchoolFlow verification code is: {otp_code}\n\n'
        'Use this code on the OTP verification page to complete your registration.\n'
        'This code expires in 10 minutes.'
    )

    html_message = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>SchoolFlow Verification</title>
    </head>
    <body style="margin: 0; padding: 0; background: linear-gradient(180deg, #eef4ff 0%, #f8fafc 100%); font-family: Arial, Helvetica, sans-serif; color: #122033;">
        <div style="max-width: 640px; margin: 40px auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 22px; overflow: hidden; box-shadow: 0 20px 45px rgba(15, 23, 42, 0.10);">
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 52%, #60a5fa 100%); padding: 30px 32px; position: relative;">
                <div style="position: absolute; inset: 0; background: radial-gradient(circle at top right, rgba(255,255,255,0.22), transparent 28%); pointer-events: none;"></div>
                <div style="position: relative; z-index: 1;">
                    <div style="display: inline-block; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.8); font-weight: bold;">SchoolFlow</div>
                    <div style="margin-top: 6px; font-size: 10px; letter-spacing: 1.4px; color: rgba(255,255,255,0.72);">by Aung Myin Ye Yint</div>
                    <h2 style="margin: 12px 0 0; font-size: 30px; line-height: 1.2; color: #ffffff;">Verify your account</h2>
                </div>
            </div>

            <div style="padding: 34px 30px 28px; background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);">
                <p style="margin: 0 0 14px; font-size: 16px; line-height: 1.7; color: #334155;">Hello there,</p>
                <p style="margin: 0 0 24px; font-size: 16px; line-height: 1.7; color: #475569;">
                    Use the verification code below to complete your registration and continue into your dashboard.
                </p>

                <div style="background: #f8fbff; border: 1px solid #d9e7ff; border-radius: 16px; padding: 22px 18px; text-align: center; margin: 0 0 20px;">
                    <div style="font-size: 11px; letter-spacing: 2.5px; text-transform: uppercase; color: #64748b; font-weight: bold; margin-bottom: 12px;">Your code</div>
                    <div style="font-size: 38px; font-weight: 700; letter-spacing: 10px; color: #0f172a;">{otp_code}</div>
                </div>

                <p style="margin: 0; font-size: 14px; line-height: 1.8; color: #475569;">
                    This code expires in 10 minutes. If you did not request this email, you can ignore it safely.
                </p>

                <div style="margin-top: 28px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 13px; line-height: 1.8; color: #64748b;">
                    Best regards,<br />
                    <strong style="color: #1e293b;">SchoolFlow by AungMyinYeYint</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

    print(f'\n[OTP CODE] Email target: {user_email}\n[OTP CODE] Code: {otp_code}\n')

    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        email = EmailMultiAlternatives(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
        )
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    authentication_form = SchoolFlowAuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        name = user.get_full_name() or user.username
        remember_me = self.request.POST.get('remember_me') == 'on'
        if remember_me:
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(0)
        messages.success(self.request, f'Logged in successfully. Welcome back, {name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = 'login'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            pending = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'role': form.cleaned_data['role'],
                'password': form.cleaned_data['password1'],
                'first_name': form.cleaned_data.get('first_name', ''),
                'last_name': form.cleaned_data.get('last_name', ''),
                'profile_image': save_pending_profile_image(request.FILES.get('profile_image')),
            }
            otp_code = generate_otp_code()
            request.session['pending_registration'] = pending
            request.session['pending_otp'] = otp_code
            request.session['otp_expires_at'] = (timezone.now() + timedelta(minutes=10)).isoformat()
            send_otp_email(pending['email'], otp_code)
            messages.info(request, f'Verification code sent to {pending["email"]}. Please check your inbox.')
            return redirect('verify_otp')
        messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def verify_otp_view(request):
    pending = request.session.get('pending_registration')
    if not pending:
        messages.error(request, 'Your session expired or the registration was not started correctly.')
        return redirect('register')

    otp_expires_at = request.session.get('otp_expires_at')
    if otp_expires_at:
        expires_at = timezone.datetime.fromisoformat(otp_expires_at)
        if timezone.now() > expires_at:
            request.session.pop('pending_registration', None)
            request.session.pop('pending_otp', None)
            request.session.pop('otp_expires_at', None)
            messages.error(request, 'Your OTP code has expired. Please register again.')
            return redirect('register')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['otp_code']
            saved_otp = request.session.get('pending_otp')
            if entered_code == saved_otp:
                user = User.objects.create_user(
                    username=pending['username'],
                    email=pending['email'],
                    password=pending['password'],
                    first_name=pending.get('first_name', ''),
                    last_name=pending.get('last_name', ''),
                )
                user.is_student = pending['role'] == 'student'
                user.is_teacher = pending['role'] == 'teacher'

                pending_image_path = pending.get('profile_image')
                if pending_image_path:
                    user.profile_image.name = pending_image_path

                user.save()

                group_name = 'Teacher' if user.is_teacher else 'Student'
                group = user.groups.model.objects.get_or_create(name=group_name)[0]
                user.groups.add(group)

                request.session.pop('pending_registration', None)
                request.session.pop('pending_otp', None)
                request.session.pop('otp_expires_at', None)

                login(request, user)
                messages.success(request, 'Your account was created and verified successfully!')
                if user.is_teacher:
                    return redirect('teacher_dashboard')
                return redirect('student_dashboard')

            messages.error(request, 'The OTP code is invalid. Please try again.')
    else:
        form = VerifyOTPForm()

    return render(request, 'verify_otp.html', {'form': form, 'email': pending.get('email')})
