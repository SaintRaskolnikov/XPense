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
from django.core.exceptions import ValidationError



class Transaction(models.Model):
    @staticmethod
    def load_choices(file_name, language):
        choices_file = os.path.join(settings.BASE_DIR,'locale', str(language), 'choices', file_name)
        if not os.path.exists(choices_file):
            return []
        try:
            with open(choices_file, 'r') as f:
                choices_list = json.load(f)
            return [(item['code'], item['description']) for item in choices_list]
        except (json.JSONDecodeError, KeyError):
            return []

    CATEGORY_CHOICES = load_choices.__func__('category.json', 'en') 

    TRANSACTION_TYPES = [
        ('expense', 'Expense'),
        ('expense', 'Take from balance'),
        ('add', 'Add to balance')
        
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = EncryptedCharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    excluded = models.BooleanField(default=False)

    def exclude(self):
        self.excluded = True
        self.save()

class ActiveSubscriptionManager(models.Manager):
    """Custom manager to filter active subscriptions."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class Subscription(models.Model):
    """Model for managing user subscriptions."""

    @staticmethod
    def load_choices(file_name, language):
        choices_file = os.path.join(settings.BASE_DIR,'locale', str(language), 'choices', file_name)
        if not os.path.exists(choices_file):
            return []
        try:
            with open(choices_file, 'r') as f:
                choices_list = json.load(f)
            return [(item['code'], item['description']) for item in choices_list]
        except (json.JSONDecodeError, KeyError):
            return []

    CATEGORY_CHOICES = load_choices.__func__('category.json', 'en') 

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
    renewed_at = models.DateTimeField(blank=True, null=True)

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
        if self.is_active:
            if self.renewed_at:
                if self.periodicity == 'daily':
                    return self.renewed_at + timedelta(days=1)
                elif self.periodicity == 'weekly':
                    return self.renewed_at + timedelta(weeks=1)
                elif self.periodicity == 'monthly':
                    next_month = self.renewed_at.replace(day=28) + timedelta(days=4)
                    return next_month.replace(day=1)
                elif self.periodicity == 'annually':
                    # Move to January 1st of the next year
                    return self.renewed_at.replace(year=self.start_date.year + 1)
                return None  # Default if periodicity is invalid or missing
            else:
                if self.periodicity == 'daily':
                    return self.start_date + timedelta(days=1)
                elif self.periodicity == 'weekly':
                    return self.start_date + timedelta(weeks=1)
                elif self.periodicity == 'monthly':
                    if self.start_date.day == 1:
                        return self.start_date
                    next_month = self.start_date.replace(day=28) + timedelta(days=4)
                    return next_month.replace(day=1)
                elif self.periodicity == 'annually':
        # If already January 1st, return the same date
                    if self.start_date.month == 1 and self.start_date.day == 1:
                        return self.start_date
                    # Otherwise, move to January 1st of the next year
                    return self.start_date.replace(year=self.start_date.year + 1, month=1, day=1)

                return None  # Default if periodicity is invalid or missing
        else:
            return None
        
    def renew(self):
        """Renew the subscription for the next period."""
        if self.is_active:
            self.renewed_at = self.get_next_transaction_date()
            self.save()

        else: 
            return None

    def cancel(self):
        """Cancel the subscription."""
        self.is_active = False
        self.save()

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
    

class Goals(models.Model):
    @staticmethod
    def load_choices(file_name, language):
        choices_file = os.path.join(settings.BASE_DIR,'locale', str(language), 'choices', file_name)
        if not os.path.exists(choices_file):
            return []
        try:
            with open(choices_file, 'r') as f:
                choices_list = json.load(f)
            return [(item['code'], item['description']) for item in choices_list]
        except (json.JSONDecodeError, KeyError):
            return []

    CATEGORY_CHOICES = load_choices.__func__('category.json', 'en') 

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = EncryptedCharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = EncryptedTextField(blank=True, null=True)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Goal"
        verbose_name_plural = "Goals"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def get_progress(self):
        """Calculate the progress percentage of the goal."""
        #if self.current_amount >= self.target_amount:
            #return 100
        return round((self.current_amount / self.target_amount) * 100, 2)
    
    def save(self, *args, **kwargs):
        # Ensure category is not empty before proceeding
        if not self.category:
            raise ValidationError("Category cannot be empty.")

        # Ensure only one active goal per category for each user
    # Check if we are creating a new goal, not updating an existing one
        if not self.pk:  # Only validate for active goals if this is a new goal
            # Ensure only one active goal per category for each user
            if not self.is_completed:
                existing_goals = Goals.objects.filter(user=self.user, category=self.category, is_completed=False)
                if existing_goals.exists():
                    raise ValidationError(f"You already have an active goal in the '{self.category}' category.")

        # Automatically mark the goal as completed if the current_amount reaches or exceeds the target_amount
        if self.current_amount >= self.target_amount:
            self.is_completed = True

        super().save(*args, **kwargs)