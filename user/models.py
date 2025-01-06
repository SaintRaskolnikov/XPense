
import random
import string
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField, EncryptedEmailField

class CustomUser(AbstractUser):
    LANGUAGES = [
    ('en', 'English'),
    ('pt', 'Portuguese'),
    ('de', 'German'),
    ('fr', 'French'),
    ]
    email = EncryptedEmailField(unique=True)
    profile_picture = CloudinaryField('image', null=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGES, default='en')
    

    def __str__(self):
        return self.username

    @property
    def profile_picture_url(self):
        """
        Returns the full URL to the user's profile picture stored on Cloudinary.
        Falls back to a default Cloudinary-hosted profile picture if not set.
        """
        if self.profile_picture:
            return self.profile_picture.url  # Cloudinary provides the URL dynamically
        # Replace with the URL of your default Cloudinary-hosted profile picture
        return 'https://res.cloudinary.com/dx0hxfr1a/image/upload/v1736191528/media/profile_pictures/iwojciwqlrfgtzwmo9cl.png'

def generate_team_code(length=6):
    """Generate a random 6-character alphanumeric team code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class Team(models.Model):
    team_code = models.CharField(max_length=6, unique=True, blank=True)  # Ensure it's a unique 6-character code
    name = EncryptedCharField(max_length=50)
    description = EncryptedTextField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='created_teams', on_delete=models.CASCADE
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='teams'
    )
    team_picture = CloudinaryField('team_picture', null=True, blank=True)  # Use CloudinaryField for image storage

    @property
    def get_profile_picture(self):
        if self.team_picture:
            return self.team_picture.url  # Return the Cloudinary-hosted image URL
        return 'https://res.cloudinary.com/dx0hxfr1a/image/upload/v1736191528/media/profile_pictures/iwojciwqlrfgtzwmo9cl.png'  # Default picture URL

    def save(self, *args, **kwargs):
        # Generate a unique team code if it doesn't exist
        if not self.team_code:
            self.team_code = generate_team_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.team_code  # Return team_code as the identifier
