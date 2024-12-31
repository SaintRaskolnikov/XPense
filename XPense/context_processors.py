# XPense/context_processors.py

from django.conf import settings
from user.models import CustomUser

def user_info(request):
    if request.user.is_authenticated:
        try:
            profile = CustomUser.objects.get(id=request.user.id)
            profile_picture = profile.get_profile_picture  # Get the profile picture URL
        except CustomUser.DoesNotExist:
            profile_picture = 'media/people/user.png'  # Default profile picture if user doesn't have one
        return {
            'username': request.user.username,
            'email': request.user.email,
            'profile_picture': profile_picture,
        }
    return {}