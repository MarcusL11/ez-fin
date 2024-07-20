from django.urls import path
from . import views

urlpatterns = [
    path("sign_in/", views.SendSignInEmail.as_view(), name="sign_in"),
    path("sign_out/", views.sign_out, name="sign_out"),
    path("verify-email/<uidb64>/<token>/", views.verify_email, name="verify_email"),
]
