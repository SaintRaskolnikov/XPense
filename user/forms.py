from django import forms
from .models import CustomUser, Team
from django.core.exceptions import ValidationError
import re



class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm', 'profile_picture', 'language']
        profile_picture = forms.ImageField(required=False)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Check for minimum length
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters long.")
        # Check for uppercase letter, number, and special character
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contain at least one special character.")
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        # Check if passwords match
        if password != password_confirm:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        # Save the user and hash the password
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()  # Save the user to the database
        return user
    


class EditProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_picture', 'language']

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Old Password'}),
        label="Old Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        label="New Password"
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}),
        label="Confirm New Password"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if new_password != new_password_confirm:
            raise ValidationError("New passwords do not match.")

        return cleaned_data

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("Incorrect password.")
        return old_password

    
class CustomLoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        # No need to authenticate in the form; leave it to the view
        return cleaned_data

    def get_user(self):
        return self.user

class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description', 'team_picture']

class JoinTeamForm(forms.Form):
    team_code = forms.CharField(max_length=6, required=True)

    def clean_team_code(self):
        team_code = self.cleaned_data.get('team_code')
        # Example validation: Check if the team_code has a valid length or format
        if len(team_code) != 6:  # assuming team code should be 6 characters long
            raise ValidationError("Team code must be exactly 6 characters long.")
        # You can add other validation logic here, e.g., checking if the team code matches a certain pattern.
        return team_code

class TeamEditForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description', 'team_picture']  # You can include more fields if needed