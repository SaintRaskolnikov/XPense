from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import CustomLoginForm,CustomUserCreationForm, EditProfileForm, JoinTeamForm, TeamEditForm, ChangePasswordForm,TeamCreateForm
from django.contrib.auth import logout
from .models import Team
from django.conf import settings
import os


from cloudinary.api import resources
from cloudinary.exceptions import Error

def get_profile_pictures():
    try:
        folder_path = "media/profile_pictures"  # Your Cloudinary folder
        response = resources(type="upload", prefix=folder_path, max_results=100)  # Fetch resources in the folder
        images = [item["secure_url"] for item in response.get("resources", [])]
        print(images)
        return images
    except Error as e:
        print(f"Error fetching profile pictures: {e}")
        return []

def register(request):

    profile_pictures = get_profile_pictures()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            selected_picture = request.POST.get('selected_profile_picture')
            if selected_picture:
                user.profile_picture = selected_picture  # Save the selected image URL
                print(f'{user.profile_picture} pic selected')
            login(request, user)
            return redirect('tracker:dashboard')  # Redirect to the home page after successful registration
    else:
        form = CustomUserCreationForm()

    return render(request, 'user_register.html', {'form': form, 'profile_pictures': profile_pictures})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')  # Redirect if already logged in
    
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authenticate the user
            user = authenticate(username=username, password=password)
            
            if user is not None:  # If authentication is successful
                login(request, user)  # Log the user in
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('tracker:dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def edit_profile(request):
    # Get the list of available profile pictures
    profile_pictures = get_profile_pictures()

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            selected_picture = request.POST.get('selected_profile_picture')
            if selected_picture:
                user.profile_picture = selected_picture  # Save the selected image URL
                print(f'{user.profile_picture} pic selected')
            user.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('tracker:dashboard')  # Redirect to profile view or dashboard page
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = EditProfileForm(instance=request.user)  # Pre-populate the form with the current user's data

    return render(request, 'edit_user.html', {'form': form, 'profile_pictures': profile_pictures})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keeps user logged in after password change
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('tracker:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangePasswordForm(user=request.user)

    return render(request, 'change_password.html', {'form': form})


@login_required
def delete_profile(request):
    user = request.user  # The currently logged-in user

    if request.method == 'POST':
        user.delete()  # Delete the user account
        messages.success(request, "Your account has been deleted successfully.")
        logout(request)  # Log the user out after account deletion
        return redirect('user:login')  # Redirect to the login page after deletion

    return render(request, 'delete_user.html', {'user': user})

@login_required
def delete_team(request, team_code):
    team = get_object_or_404(Team, team_code=team_code)
    if request.user != team.creator:
        messages.error(request, "You are not authorized to delete this team.")
        return redirect('user:teams_list')
    if request.method == 'POST':
        team.delete()
        messages.success(request, "The team has been deleted successfully.")
        return redirect('user:teams_list')

    return render(request, 'delete_team.html', {'team': team})


@login_required
def create_team(request):
    profile_pictures = get_profile_pictures()
    
    if request.method == 'POST':
        form = TeamCreateForm(request.POST)
        
        if form.is_valid():
            # Create the team instance (don't save yet)
            team = form.save(commit=False)  # Avoid saving immediately
            
            selected_picture = request.POST.get('selected_team_picture')
            print(f'{selected_picture} pic selected')

            if selected_picture:
                team.team_picture = selected_picture  # Set the selected picture
                
            team.creator = request.user  # Set the creator to the current user
            team.save()  # Save the team object to the database

            team.users.add(request.user)  # Add the creator as a user to the team

            # Redirect to the teams list or another confirmation page
            return redirect('user:teams_list')
    else:
        form = TeamCreateForm()  # Initialize the form if the request method is not POST

    return render(request, 'create_team.html', context={'team_pictures': profile_pictures, 'form': form})



@login_required
def logout_view(request):
    """Logs out the user and redirects to the homepage or login page."""
    logout(request)
    return redirect('user:login')

@login_required
def join_team(request):
    if request.method == 'POST':
        form = JoinTeamForm(request.POST)
        if form.is_valid():
            team_code = form.cleaned_data['team_code']
            try:
                team = Team.objects.get(team_code=team_code)
                # Check if user is already in the team
                if request.user in team.users.all():
                    messages.info(request, "You are already part of this team!")
                    return redirect('user:edit_team', team_code=team.team_code)
                
                else:
                # Add the user to the team
                    team.users.add(request.user)
                    messages.success(request, "You have successfully joined the team!")
                return redirect('user:edit_team', team_code=team.team_code)
            except Team.DoesNotExist:
                messages.error(request, "Invalid team number!")

        else:
            messages.error(request, "Please provide a valid team number.")

    else:
        form = JoinTeamForm()

    return render(request, 'join_team.html', {'form': form})


@login_required
def teams_list(request):
    # Filter teams where the logged-in user is part of the team
    user_teams = request.user.teams.all()
    for user_team in user_teams:
        print(f'{user_team.team_picture} team list')

    return render(request, 'team_list.html', {'user_teams': user_teams})

@login_required
def edit_team(request, team_code):
    team = get_object_or_404(Team, team_code=team_code)
    profile_pictures = get_profile_pictures()

    if request.method == 'POST':
        form = TeamCreateForm(request.POST, instance=team)
        if form.is_valid():
            # Avoid saving immediately to modify fields
            team = form.save(commit=False)

            selected_picture = request.POST.get('selected_team_picture')
            print(f'{selected_picture} pic selected edit')

            if selected_picture:
                team.team_picture = selected_picture  # Assign the selected picture URL

            team.save()  # Save the team object to the database

            return redirect('user:teams_list')  # Redirect to team list after saving
    else:
        form = TeamCreateForm(instance=team)
    
    return render(request, 'edit_team.html', {'form': form, 'team': team, 'team_pictures': profile_pictures})

    
@login_required
def remove_user_from_team(request, team_code, pk):
    team = get_object_or_404(Team, team_code=team_code)
    user_to_remove = get_object_or_404(team.users, pk=pk)
    
    if request.user != team.creator and user_to_remove != request.user:

        messages.error(request, "You are not authorized to remove this user.")
        return redirect('user:teams_list')
    
    # Remove the user from the team
    team.users.remove(user_to_remove)
    
    return redirect('user:teams_list')