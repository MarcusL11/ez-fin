from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    has_verified_email = models.BooleanField(default=False)
    admin_status = models.BooleanField(default=False)
    credits = models.IntegerField(default=0)

    def __str__(self):
        return self.username
