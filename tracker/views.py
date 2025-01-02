
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import JsonResponse
from .models import Transaction, Contribution, Subscription, Goals
from user.models import Team, CustomUser
from django.http import Http404
from .forms import TransactionForm, ContributionForm, SubscriptionForm
from django.shortcuts import render, get_object_or_404, redirect
import json
from django.contrib import messages
from django.http import HttpResponseForbidden
from datetime import timedelta
from django.utils import timezone
from datetime import datetime
from django.utils.dateparse import parse_datetime


from django.utils.timezone import now

@login_required
def dashboard(request):
    today = now()

    # Set the default start date to the first of the current month
    default_start_date = today.replace(day=1)
    # Set the default end date to today
    default_end_date = today

    # Get the start and end dates from the request or use the defaults
    start_date_str = request.GET.get('start', default_start_date.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end', default_end_date.strftime('%Y-%m-%d'))

    # Parse the dates from the request
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        start_date = default_start_date
        start_date_str = default_start_date.strftime('%Y-%m-%d')

    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
    except (ValueError, TypeError):
        end_date = default_end_date
        end_date_str = default_end_date.strftime('%Y-%m-%d')

    # Fetch transactions and contributions for the user
    transactions_pure = Transaction.objects.filter(user=request.user, team__isnull=True)
    for transaction in transactions_pure:
        print(f' dates {transaction.date}')
    
    contributions = Contribution.objects.filter(user=request.user)

    # Apply date range filter if both start and end dates are provided
    if start_date:
        transactions_pure = transactions_pure.filter(date__gte=start_date)
        contributions = contributions.filter(transaction__date__gte=start_date)
    if end_date:
        transactions_pure = transactions_pure.filter(date__lte=end_date)
        contributions = contributions.filter(transaction__date__lte=end_date)

    transactions_pure = transactions_pure.order_by('-date')

    subs_renewal_warning = []
    subscriptions = Subscription.objects.filter(user=request.user)
    for subscription in subscriptions:
        next = subscription.get_next_transaction_date()
        if next and timezone.is_naive(next):
            next = timezone.make_aware(next)
        if next <= today:
            subs_renewal_warning.append(subscription)

    print(f'{transactions_pure} 2pure')
    contributions = contributions.order_by('-transaction__date')

    # Initialize balance
    current_balance = 0

    # Calculate balance based on transaction type
    for transaction in transactions_pure:
        if transaction.transaction_type == 'add':
            current_balance += transaction.amount
        elif transaction.transaction_type == 'expense':
            current_balance -= transaction.amount

    for contribution in contributions:
        if contribution.transaction.transaction_type == 'add':
            current_balance += contribution.amount
        elif contribution.transaction.transaction_type == 'expense':
            current_balance -= contribution.amount

    # Merge transactions and contributions into one list
    combined_transactions = list(transactions_pure) + list(contributions)

    # Sort combined transactions by date (considering contribution's related transaction date)
    transactions = sorted(
        combined_transactions,
        key=lambda x: x.date if isinstance(x, Transaction) else x.transaction.date,
        reverse=True
    )
    print(transactions)
    # Return the rendered template with the context
    return render(request, 'dashboard.html', {
        'current_balance': current_balance,
        'transactions': transactions,
        'start_date': start_date_str,  # Pass the formatted date for the date input
        'end_date': end_date_str,      # Pass the formatted date for the date input
        'subs_renewal_warning': subs_renewal_warning,
    })


@login_required
def get_balance_data(request):
    # Get today's date
    today = timezone.now()

    # Get the date 30 days ago
    thirty_days_ago = today - timedelta(days=7)

    # Fetch transactions and contributions for the user within the last 30 days
    transactions_pure = Transaction.objects.filter(user=request.user, team__isnull=True, date__gte=thirty_days_ago).order_by('date')
    contributions = Contribution.objects.filter(user=request.user, transaction__date__gte=thirty_days_ago).order_by('transaction__date')

    # Initialize balance
    current_balance = 0
    balance_data = []

    # Calculate balance for each day
    for i in range(7):
        # For each day, filter transactions that occurred on that date
        day = today - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Transactions on the current day
        daily_transactions = transactions_pure.filter(date__range=[day_start, day_end])
        daily_contributions = contributions.filter(transaction__date__range=[day_start, day_end])

        # Update the balance for the day
        for transaction in daily_transactions:
            if transaction.transaction_type == 'add':
                current_balance += transaction.amount
            elif transaction.transaction_type == 'expense':
                current_balance -= transaction.amount

        for contribution in daily_contributions:
            if contribution.transaction.transaction_type == 'add':
                current_balance += contribution.amount
            elif contribution.transaction.transaction_type == 'expense':
                current_balance -= contribution.amount

        # Store the balance for this day
        balance_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'balance': current_balance
        })

    # Reverse the order to show from the earliest date to the most recent
    balance_data.reverse()

    return JsonResponse(balance_data, safe=False)

@login_required
def add_transaction(request):
    category_choices = Transaction.load_choices('category.json')  # Assuming you're loading categories from a JSON
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        print(form)  # For debugging, remove in production


        if form.is_valid():

            with db_transaction.atomic():  # Ensure atomicity
                # Create the transaction object but don't save it yet
                transaction = form.save(commit=False)
                transaction.user = request.user  # Assign current user as creator
                transaction.save()  # Save transaction first
                transaction_hash = transaction.transaction_hash
                if transaction.team:
                    return redirect('tracker:add_contribution', transaction_hash=transaction_hash)  # Replace with your URL name for success page

        return redirect('tracker:dashboard')

    else:
        form = TransactionForm()

    teams = Team.objects.filter(users=request.user)  # Assuming teams the user belongs to
    return render(request, 'add_transaction.html', {'form': form, 'teams': teams, 'category_choices': category_choices})


@login_required
def add_contribution(request, transaction_hash):
    transaction = Transaction.objects.get(transaction_hash=transaction_hash)
    members = transaction.team.users.all()  # Assuming team.users is a related manager
    members_count = members.count()
    amount_per_member = transaction.amount / members_count

    if request.method == 'POST':
        for member in members:
            # Get the amount for each member from the POST data
            amount = request.POST.get(f'amount_{member.id}')
            if amount:
                # Check if a contribution for this user and transaction already exists
                existing_contribution = Contribution.objects.filter(transaction=transaction, user=member).first()
                if existing_contribution:
                    # Delete the existing contribution
                    existing_contribution.delete()
                    print(f"Deleted existing contribution for {member.username}")

                # Prepare the form data to create the contribution
                form_data = {
                    'amount': amount,
                    'transaction': transaction.id,
                    'user': member.id,
                }

                # Create a new form with the provided data
                form = ContributionForm(form_data)

                # Check if the form is valid before saving
                if form.is_valid():
                    print(f"Saving contribution for {member.username} with amount {amount}")
                    contribution = form.save(commit=False)
                    contribution.user = member
                    contribution.transaction = transaction
                    contribution.save()
                else:
                    print(f"Form invalid for {member.username}, errors: {form.errors}")

        # After saving all contributions, redirect to the dashboard
        return redirect('tracker:dashboard')  # Redirect to a success page after saving

    else:
        form = ContributionForm()

    # Pass the form and necessary context data to the template
    return render(request, 'add_contribution.html', {
        'form': form,
        'members': members,
        'amount_per_member': amount_per_member,
        'transaction': transaction,
    })



@login_required
def get_team_members(request, pk):
    try:
        team = Team.objects.get(pk=pk)
        members = team.users.all()  # Assuming a ManyToMany relationship named 'users'
        members_data = [{"id": member.id, "username": member.username} for member in members]
        print(members_data)
        return JsonResponse({"members": members_data}, status=200)
    except Team.DoesNotExist:
        return JsonResponse({"error": "Team not found."}, status=404)

@login_required
def edit_transaction(request, transaction_hash):
    # Get the transaction object or return a 404 if not found
    transaction = get_object_or_404(Transaction, transaction_hash=transaction_hash)

    # Check if the current user is allowed to edit this transaction
    if transaction.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this transaction.")

    # If the form is submitted
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.save()
            if transaction.team:
                    return redirect('tracker:add_contribution', transaction_hash=transaction_hash)  # Redirect to the dashboard or another page
    else:
        # Pre-fill the form with the transaction's current data
        form = TransactionForm(instance=transaction)

    teams = Team.objects.filter(users=request.user)  # Fetch teams the user is part of
    category_choices = Transaction.CATEGORY_CHOICES  # Assuming you have category choices in the model

    return render(request, "edit_transaction.html", {
        "form": form,
        "transaction": transaction,
        "teams": teams,
        "category_choices": category_choices,
    })


@login_required
def delete_transaction(request, transaction_hash):
    # Fetch the transaction by transaction_hash
    transaction = get_object_or_404(Transaction, transaction_hash=transaction_hash, user=request.user)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        return redirect('tracker:dashboard')  # Redirect to dashboard after delete

    return render(request, 'delete_transaction.html', {'transaction': transaction})

@login_required
def goals_view(request):
    goals = Goals.objects.filter(user=request.user)

    return render(request, 'goals.html')

@login_required
def get_graph_data(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    print(f"Start Date: {start_date}, End Date: {end_date}")

    # Parse the start and end date if provided
    if start_date and end_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')
        print(f"Parsed Start Date: {start_date}, Parsed End Date: {end_date}")
    else:
        # Default to the last 7 days if no date range is provided
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

    # Get the selected team IDs from the request
    selected_team_ids = request.GET.getlist('team_ids')
    selected_team_ids = [int(team_id) for team_id in selected_team_ids]
    print(f"Selected Team IDs: {selected_team_ids}")

    # Filter transactions and contributions based on the selected date range and teams
    transactions_pure = Transaction.objects.filter(
        user=request.user,
        team__id__in=selected_team_ids,
        date__range=[start_date, end_date]
    ).order_by('date')

    print(f"Transactions Query: {transactions_pure.query}")

    contributions = Contribution.objects.filter(
        user=request.user,
        transaction__date__range=[start_date, end_date],
        transaction__team__id__in=selected_team_ids
    ).order_by('transaction__date')

    print(f"Contributions Query: {contributions.query}")

    # Initialize team totals (remove category handling)
    team_totals = {team.id: 0 for team in Team.objects.filter(id__in=selected_team_ids)}

    # Loop through transactions and contributions to accumulate the total spent per team
    for transaction in transactions_pure:
        if transaction.transaction_type == 'add':
            team_totals[transaction.team.id] += transaction.amount
        elif transaction.transaction_type == 'expense':
            team_totals[transaction.team.id] -= transaction.amount

    for contribution in contributions:
        if contribution.transaction.transaction_type == 'add':
            team_totals[contribution.transaction.team.id] += contribution.amount
        elif contribution.transaction.transaction_type == 'expense':
            team_totals[contribution.transaction.team.id] -= contribution.amount

    # Prepare the final data for the response
    total_spent_per_team = [
        {
            'team': Team.objects.get(id=team_id).name,  # Assuming you want the team name
            'total_spent': team_totals[team_id]
        }
        for team_id in selected_team_ids
    ]

    print(f"Total Spent Per Team: {total_spent_per_team}")

    return JsonResponse({
        'total_spent_per_team': total_spent_per_team
    })

@login_required
def create_subscriptions(request):
    category_choices = Subscription.load_choices('category.json')
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.save()
            return redirect('tracker:user_subscriptions')
    else:
        form = SubscriptionForm()

    subscriptions = Subscription.objects.filter(user=request.user)
    return render(request, 'add_subscription.html', {'form': form, 'subscriptions': subscriptions, 'category_choices': category_choices})

@login_required
def edit_subscription(request, subscription_id):
    # Get the subscription object or raise a 404 if not found
    category_choices = Subscription.load_choices('category.json')
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    # Check if the subscription belongs to the current user
    if subscription.user != request.user:
        raise Http404("You are not authorized to edit this subscription.")

    # If the form is submitted
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            return redirect('tracker:user_subscriptions')
    else:
        form = SubscriptionForm(instance=subscription)

    return render(request, 'edit_subscription.html', {
        'form': form,
        'subscription': subscription,
        'category_choices': category_choices,
    })

@login_required
def renew_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if subscription.user != request.user:
        raise Http404("You are not authorized to renew this subscription.")
    else:

        if request.method == 'POST':
            subscription.renew()
            Transaction.objects.create(
                user=subscription.user,
                category=subscription.category,
                amount=subscription.amount,
                description=subscription.name,
                transaction_type='expense',
                date=subscription.get_next_transaction_date(),
            )
            return redirect('tracker:dashboard')  # Redirect to the dashboard or another page


@login_required
def cancel_subscription(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    if subscription.user != request.user:
        raise Http404("You are not authorized to cancel this subscription.")
    else:
        if request.method == 'POST':
            subscription.cancel()
            return redirect('tracker:dashboard')


@login_required
def user_subscriptions(request):
    # Fetch all subscriptions that belong to the logged-in user
    subscriptions = Subscription.objects.filter(user=request.user, is_active=True)
    
    # Calculate monthly and annual expected spend
    daily_spend = 0
    weekly_spend = 0
    monthly_spend = 0
    annual_spend = 0

    for subscription in subscriptions:
        if subscription.periodicity == 'daily':
            daily_spend += subscription.amount * 30
        elif subscription.periodicity == 'weekly':
            weekly_spend += subscription.amount * 4
        elif subscription.periodicity == 'monthly':
            monthly_spend += subscription.amount
        elif subscription.periodicity == 'annual':
            annual_spend += subscription.amount / 12  # Divide by 12 to get monthly equivalent

    # Calculate annual total spend (monthly spend + annual subscriptions)
    total_annual_spend = monthly_spend * 12 + annual_spend

    return render(request, 'list_subscriptions.html', {
        'subscriptions': subscriptions,
        'daily_spend': daily_spend,
        'weekly_spend': weekly_spend,
        'monthly_spend': monthly_spend,
        'annual_spend': annual_spend,
        'total_annual_spend': total_annual_spend,
    })


@login_required
def delete_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    
    if request.method == 'POST':
        subscription.delete()
        return redirect('tracker:user_subscriptions')  # Redirect to subscription list or desired page

    return render(request, 'delete_subscription.html', {'subscription': subscription})

@login_required
def delete_transaction(request, transaction_hash):
    transaction = get_object_or_404(Transaction, transaction_hash=transaction_hash)
    
    if request.method == 'POST':
        transaction.delete()
        return redirect('tracker:dashboard')  # Redirect to subscription list or desired page

    return render(request, 'delete_transaction.html', {'transaction': transaction})

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from django.utils.timezone import localtime

@login_required
def export_transactions(request, interval):
    # Get the start and end dates based on the interval
    if interval == 'current_month':
        start_date = timezone.now().replace(day=1)
    elif interval == 'current_year':
        start_date = timezone.now().replace(month=1, day=1)
    elif interval == 'last_year':
        start_date = timezone.now().replace(year=timezone.now().year - 1, month=1, day=1)
    elif interval == 'last_month':
        start_date = timezone.now().replace(month=timezone.now().month - 1, day=1)
    else:
        start_date = None

    # Filter transactions and contributions based on the interval
    transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date,
        team__isnull=True
    ).order_by('-date')

    contributions = Contribution.objects.filter(
        user=request.user,
        transaction__date__gte=start_date
    ).order_by('transaction__date')

    full_list_transactions = list(transactions) + list(contributions)
    transactions = sorted(
        full_list_transactions,
        key=lambda x: x.date if isinstance(x, Transaction) else x.transaction.date,  # Check if it's a Transaction or Contribution and use the appropriate date
        reverse=True
    )
    # Create a workbook and sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # Write headers
    headers = ['Description', 'Amount', 'Category', 'Date', 'Transaction Type']
    ws.append(headers)

    # Write data
    for item in transactions:
        # Ensure the date is naive (removing tzinfo if it's timezone-aware)
        date_value = item.date if isinstance(item, Transaction) else item.transaction.date
        if date_value.tzinfo:
            date_value = localtime(date_value).replace(tzinfo=None)  # Convert to naive datetime

        row = [
            item.description if isinstance(item, Transaction) else item.transaction.description,
            item.amount if isinstance(item, Transaction) else item.transaction.amount,
            item.category if isinstance(item, Transaction) else item.transaction.category,
            date_value,
            item.transaction_type if isinstance(item, Transaction) else item.transaction.transaction_type,
        ]
        ws.append(row)

    # Set column widths for better readability
    for col in range(1, len(headers) + 1):
        col_letter = get_column_letter(col)
        max_length = 0
        for row in ws.iter_rows(min_col=col, max_col=col):
            for cell in row:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[col_letter].width = adjusted_width

    # Create an HTTP response with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="transactions_{interval}.xlsx"'

    # Save the workbook to the response
    wb.save(response)
    return response
