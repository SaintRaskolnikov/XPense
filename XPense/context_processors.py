# XPense/context_processors.py
from user.models import CustomUser 
from user.models import CustomUser
import json
from django.utils.translation import get_language
from django.conf import settings

def user_info(request):
    if request.user.is_authenticated:
        try:
            # Fetch the user profile and retrieve the profile picture URL
            profile = CustomUser.objects.get(id=request.user.id)
            profile_picture = profile.profile_picture_url if profile.profile_picture_url else None  # Ensure it gets the Cloudinary URL
            print(profile_picture)
        except CustomUser.DoesNotExist:
            profile_picture = None  # Handle case where user profile doesn't exist
        
        return {
            'username': request.user.username,
            'email': request.user.email,
            'profile_picture': profile_picture,
        }
    return {}


def load_translations(language):
    with open(f'locale/{language}/translation.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def translation_context_processor(request):
    try:
        translations = load_translations(request.user.language)
    except:
        translations = load_translations('en')

    return {'t': translations}