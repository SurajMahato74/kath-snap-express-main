from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_otp_email(user, otp):
    subject = 'Your OTP Code - EzeyWay'
    message = f'Your OTP code is: {otp}. This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_verification_email(user, token):
    subject = 'Verify Your Email - EzeyWay'
    verification_url = f"http://127.0.0.1:8000/accounts/verify-email/{token}/"
    message = f'Click the link to verify your email: {verification_url}'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def send_password_reset_email(user, token):
    subject = 'Reset Your Password - EzeyWay'
    reset_url = f"http://127.0.0.1:8000/accounts/reset-password/{token}/"
    message = f'Click the link to reset your password: {reset_url}'
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )