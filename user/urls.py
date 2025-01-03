from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('delete-profile/', views.delete_profile, name='delete_profile'),
    path('create/', views.create_team, name='create_team'),
    path('join/', views.join_team, name='join_team'),
    path('team/list/', views.teams_list, name='teams_list'),
    path('team/edit/<str:team_code>/', views.edit_team, name='edit_team'),
    path('team/remove/<str:team_code>/<int:pk>/', views.remove_user_from_team, name='remove_user_from_team'),
    path('change-password/', views.change_password, name='change_password'),

]