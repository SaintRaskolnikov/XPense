from django.core.management.base import BaseCommand
from django.utils.timezone import now
from tracker.models import Subscription, Transaction

class Command(BaseCommand):
    help = "Processes active subscriptions and creates transactions."

    def handle(self, *args, **kwargs):
        today = now().date()
        subscriptions = Subscription.objects.filter(is_active=True)

        for subscription in subscriptions:
            # Determine if a transaction should be created today
            if subscription.periodicity == 'daily':
                should_create = True
            elif subscription.periodicity == 'weekly' and today.weekday() == 0:  # Monday
                should_create = True
            elif subscription.periodicity == 'monthly' and today.day == 1:  # First of the month
                should_create = True
            elif subscription.periodicity == 'annually' and today.day == 1 and today.month == 1:  # January 1
                should_create = True
            else:
                should_create = False

            if should_create:
                # Create a new transaction
                Transaction.objects.create(
                    user=subscription.user,
                    category=subscription.category,
                    amount=subscription.amount,
                    name=subscription.name,
                    description=subscription.description,
                    transaction_type='expense',
                    date=today,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Created transaction for subscription: {subscription.name}")
                )
