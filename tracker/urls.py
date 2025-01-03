from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [

    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('edit-transaction/<str:transaction_hash>/', views.edit_transaction, name='edit_transaction'),
    path('delete-transaction/<str:transaction_hash>/', views.delete_transaction, name='delete_transaction'),
    path('get-team-members/<int:pk>/', views.get_team_members, name='get_team_members'),
    path('add_contribution/<str:transaction_hash>/', views.add_contribution, name='add_contribution'),
    path('balance_data/', views.get_balance_data, name='balance_data'), 
    path('get-graph-data/', views.get_graph_data, name='get_graph_data'),
    path('create-subscriptions/', views.create_subscriptions, name='create_subscription'),
    path('edit-subscription/<int:subscription_id>/', views.edit_subscription, name='edit_subscription'),
    path('subscriptions/', views.user_subscriptions, name='user_subscriptions'),
    path('subscriptions/delete/<int:subscription_id>/', views.delete_subscription, name='delete_subscription'),
    path('export-transactions/<str:interval>/', views.export_transactions, name='export_transactions'),
    path('renew-subscription/<int:pk>/', views.renew_subscription, name='renew_subscription'),
    path('cancel-subscription/<int:pk>/', views.cancel_subscription, name='cancel_subscription'),
    path('goals-progress/', views.goals_progress, name='goals_progress'),
    path('goals-create/', views.create_goal, name='create_goal'),
    path('goals-edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('goals-delete/<int:pk>/', views.delete_goal, name='delete_goal'),
    path('monthly-report/', views.get_monthly_balance_data, name='monthly_report'),
    path('category-report/', views.get_expense_per_category, name='category_report'),
    path('integrated-position/', views.graphs, name='integrated_position'),

]