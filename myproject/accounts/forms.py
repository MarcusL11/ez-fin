# accounts/forms.py
from django.forms import ModelForm
from .models import CustomUser


class CreateUserForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password"]
