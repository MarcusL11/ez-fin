from typing import Optional
from myproject.settings import env
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import CustomUser as User


def send_sign_in_email(user: User) -> None:
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = f"{env('EMAIL_VERIFICATION_URL')}/{uid}/{token}/"

    subject = "EZFin: Verify your email address to login"
    message = (
        "Hi there 🙂\n"
        "Please click "
        f'<a href="{verification_link}" target="_blank">here</a> '
        "to verify your email address and access EZFin"
    )
    send_mail(subject, "", settings.EMAIL_HOST_USER, [user.email], html_message=message)


def decode_uid(uidb64: str) -> Optional[str]:
    """Decode the base64 encoded UID."""
    try:
        return urlsafe_base64_decode(uidb64).decode()
    except (TypeError, ValueError, OverflowError) as e:
        print(f"{e = }")
        return None


def get_user_by_uid(uid: str) -> Optional[User]:
    """Retrieve user object using UID."""
    try:
        return User.objects.get(pk=uid)
    except User.DoesNotExist as e:
        print(f"{e = }")
        return None
