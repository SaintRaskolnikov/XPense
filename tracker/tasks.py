from celery import shared_task
from tracker.models import Subscription, Transaction
from django.utils.timezone import now

@shared_task
def process_subscriptions():
    today = now().date()
    subscriptions = Subscription.objects.filter(is_active=True)

    for subscription in subscriptions:
        if subscription.periodicity == 'daily':
            should_create = True
        elif subscription.periodicity == 'weekly' and today.weekday() == 0:
            should_create = True
        elif subscription.periodicity == 'monthly' and today.day == 1:
            should_create = True
        elif subscription.periodicity == 'annually' and today.day == 1 and today.month == 1:
            should_create = True
        else:
            should_create = False

        if should_create:
            Transaction.objects.create(
                user=subscription.user,
                category=subscription.category,
                amount=subscription.amount,
                name=subscription.name,
                description=subscription.description,
                transaction_type='expense',
                date=today,
            )
