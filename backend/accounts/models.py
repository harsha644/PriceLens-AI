from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+?[1-9]\d{7,14}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True, validators=[phone_validator])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"
