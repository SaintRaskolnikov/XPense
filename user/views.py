from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm,CustomUserCreationForm, EditProfileForm, TeamCreateForm, JoinTeamForm, TeamEditForm
from django.contrib.auth import logout
from .models import Team
from user.models import CustomUser
from django.contrib.auth.models import  User

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('tracker:dashboard')  # Redirect to the home page after successful registration
    else:
        form = CustomUserCreationForm()

    return render(request, 'user_register.html', {'form': form})

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
    user = request.user  # The currently logged-in user
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('user:edit_profile')  # Stay on the profile page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EditProfileForm(instance=user)

    return render(request, 'user/edit_profile.html', {'form': form})


@login_required
def delete_profile(request):
    user = request.user  # The currently logged-in user

    if request.method == 'POST':
        user.delete()  # Delete the user account
        messages.success(request, "Your account has been deleted successfully.")
        logout(request)  # Log the user out after account deletion
        return redirect('user:login')  # Redirect to the login page after deletion

    return render(request, 'user/delete_profile.html', {'user': user})


@login_required
def create_team(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        name = request.POST.get('name')
        
        # Create the new team
        team = Team.objects.create(name= name, description=description, creator=request.user)
        team.users.add(request.user)
        
        # Get the generated team code
        team_code = team.team_code
        print(team_code)
        
        # Redirect to a confirmation page or display the team code
        return redirect('user:teams_list')
    
    return render(request, 'create_team.html')

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
                    print("You are already part of this team!")
                    return redirect('user:edit_team', team_code=team.team_code)
                
                else:
                # Add the user to the team
                    team.users.add(request.user)
                    print("You have successfully joined the team!")
                    messages.success(request, "You have successfully joined the team!")
                return redirect('user:edit_team', team_code=team.team_code)
            except Team.DoesNotExist:
                messages.error(request, "Invalid team number!")
                print("Invalid team number!")

        else:
            messages.error(request, "Please provide a valid team number.")
            print("Please provide a valid team number.")
    else:
        form = JoinTeamForm()

    return render(request, 'join_team.html', {'form': form})


@login_required
def team_detail(request, team_number):
    try:
        team = Team.objects.get(team_number=team_number)
        return render(request, 'team_detail.html', {'team': team})
    except Team.DoesNotExist:
        messages.error(request, "Team does not exist.")
        return redirect('team:join_team')


@login_required
def teams_list(request):
    # Filter teams where the logged-in user is part of the team
    user_teams = request.user.teams.all()

    return render(request, 'team_list.html', {'user_teams': user_teams})

@login_required
def edit_team(request, team_code):
    team = get_object_or_404(Team, team_code=team_code)
    print(team)
    # Check if the user is the creator
    if request.user != team.creator:
        messages.error(request, "You are not the creator of this Team.")
        return redirect('user:teams_list')  # You can redirect to a team list or error page
    
    if request.method == 'POST':
        form = TeamEditForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('user:teams_list')  # Redirect to team list after saving
    else:
        form = TeamEditForm(instance=team)
    
    return render(request, 'edit_team.html', {'form': form, 'team': team})
    
@login_required
def remove_user_from_team(request, team_number, pk):
    team = get_object_or_404(Team, team_number=team_number)
    user_to_remove = get_object_or_404(team.users, pk=pk)
    
    # Only the team creator can remove users
    if request.user != team.users.first():  # Assuming the first user is the creator
        return redirect('team_list')
    
    # Remove the user from the team
    team.users.remove(user_to_remove)
    
    return redirect('edit_team', team_number=team_number)