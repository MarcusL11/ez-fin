from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest, HttpResponse
from django.views import View
from .forms import CreateUserForm
from .models import CustomUser as User
from .services import decode_uid, get_user_by_uid, send_sign_in_email


def verify_email(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    """
    Verify user email after the user clicks on the email link.
    """

    uid = decode_uid(uidb64)
    user = get_user_by_uid(uid) if uid else None

    if user and default_token_generator.check_token(user, token):
        user.has_verified_email = True
        user.save()
        # subscription, created = Subscription.objects.get_or_create(email=user)
        # subscription.save()
        login(request, user)
        print("Email verification successful")
        return redirect("dashboard")

    print("Email verification failed")
    return redirect("sign_in")


# name of URL path is "sign_in"
class SendSignInEmail(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Takes the an anonymous non-logged-in user to the sign in page.
        """
        if not request.user.is_anonymous and request.user.has_verified_email:
            return redirect("dashboard")
        form = CreateUserForm()
        return render(request, "accounts/sign_in_redirect.html", {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        data = {
            "username": request.POST["email"],
            "email": request.POST["email"],
            "password": request.POST["email"],
        }
        user, created = User.objects.get_or_create(
            email=data["email"],
            defaults={"username": data["email"], "password": data["email"]},
        )
        return self._send_verification_and_respond(user)

    @staticmethod
    def _send_verification_and_respond(user: User) -> HttpResponse:
        send_sign_in_email(user)
        message = (
            f"We've sent an email ✉️ to "
            f'<a href=mailto:{user.email}" target="_blank">{user.email}</a> '
            "Please check your email to verify your account"
        )
        return HttpResponse(message)


def sign_out(request: HttpRequest) -> HttpResponse:
    request.session.flush()
    return redirect("home")
