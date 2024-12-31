from django.db import models
from user.models import Team
from django.conf import settings
from datetime import timedelta
from django.db import models
from django.utils.timezone import now
import json
import os
import uuid
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField



class Transaction(models.Model):
    @staticmethod
    def load_choices(file_name):
        choices_file = os.path.join(settings.BASE_DIR, 'choices', file_name)
        if not os.path.exists(choices_file):
            return []
        try:
            with open(choices_file, 'r') as f:
                choices_list = json.load(f)
            return [(item['code'], item['description']) for item in choices_list]
        except (json.JSONDecodeError, KeyError):
            return []

    CATEGORY_CHOICES = load_choices.__func__('category.json')

    TRANSACTION_TYPES = [
        ('add', 'Add to balance'),
        ('expense', 'Expense')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = EncryptedCharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    transaction_hash = models.CharField(max_length=32, unique=True, editable=False)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, blank=True, null=True)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES, default='expense')

    def save(self, *args, **kwargs):
        if not self.transaction_hash:
            self.transaction_hash = str(uuid.uuid4().hex)

        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.description} - {self.amount}'

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['team']),
            models.Index(fields=['transaction_hash']),
        ]

class Contribution(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='contributions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

class ActiveSubscriptionManager(models.Manager):
    """Custom manager to filter active subscriptions."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Subscription(models.Model):
    """Model for managing user subscriptions."""

    @staticmethod
    def load_choices(file_name):
        """Loads choices dynamically from a JSON file."""
        choices_file = os.path.join(settings.BASE_DIR, 'choices', file_name)
        if not os.path.exists(choices_file):
            return []
        try:
            with open(choices_file, 'r') as f:
                choices_list = json.load(f)
            return [(item['code'], item['description']) for item in choices_list]
        except (json.JSONDecodeError, KeyError):
            return []

    CATEGORY_CHOICES = load_choices.__func__('category.json') or [
        ('default', 'Default Category')  # Fallback option if JSON fails
    ]

    PERIODICITY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annually', 'Annually'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    name = EncryptedCharField(max_length=255)
    description = EncryptedTextField(blank=True, null=True)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES)
    start_date = models.DateField(default=now)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()  # Default manager
    active = ActiveSubscriptionManager()  # Custom manager for active subscriptions

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.periodicity}) - {self.user.username}"


    def get_next_transaction_date(self):
        """Calculate the next transaction date based on periodicity."""
        if self.periodicity == 'daily':
            return self.start_date + timedelta(days=1)
        elif self.periodicity == 'weekly':
            return self.start_date + timedelta(weeks=1)
        elif self.periodicity == 'monthly':
            # Move to the first of the next month
            next_month = self.start_date.replace(day=28) + timedelta(days=4)
            return next_month.replace(day=1)
        elif self.periodicity == 'annually':
            # Move to January 1st of the next year
            return self.start_date.replace(year=self.start_date.year + 1)

        return None  # Default if periodicity is invalid or missing