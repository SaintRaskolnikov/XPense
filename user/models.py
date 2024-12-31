
import random
import string
from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django_cryptography.fields import encrypt

class CustomUser(AbstractUser):
    email = encrypt(models.EmailField(unique=True))
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    

    def __str__(self):
        return self.username

    @property
    def get_profile_picture(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/media/people/user.png'
    

def generate_team_code(length=6):
    """Generate a random 6-character alphanumeric team code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class Team(models.Model):
    team_code = models.CharField(max_length=6, unique=True, blank=True)  # Ensure it's a unique 6-character code
    name = encrypt(models.CharField(max_length=50))
    description = encrypt(models.TextField())
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='created_teams', on_delete=models.CASCADE
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='teams'
    )

    def save(self, *args, **kwargs):
        # Generate a unique team code if it doesn't exist
        if not self.team_code:
            self.team_code = generate_team_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.team_code  # Return team_code as the identifier