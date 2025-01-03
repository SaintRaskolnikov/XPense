from django import forms
from .models import Transaction, Contribution, Subscription, Goals
from user.models import Team
from django.forms import Select

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['description', 'amount', 'category', 'team', 'transaction_type']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        
        # Dynamically load the CATEGORY_CHOICES into the form
        self.fields['category'].choices = Transaction.load_choices('category.json')

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['user', 'amount']

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['name', 'description', 'category', 'amount', 'periodicity', 'start_date', 'is_active']

from django import forms
from .models import Goals

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goals
        fields = ['name', 'category', 'description', 'target_amount', 'current_amount', 'target_date', 'is_completed']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-primary-500 dark:focus:ring-primary-500',
                'placeholder': 'Enter goal name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-primary-500 dark:focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Enter goal description',
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-primary-500 dark:focus:ring-primary-500',
                'step': '0.01',
                'placeholder': 'Enter target amount',
            }),
            'current_amount': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-primary-500 dark:focus:ring-primary-500',
                'step': '0.01',
                'placeholder': 'Enter current amount',
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-primary-500 dark:focus:ring-primary-500',
                'type': 'date',
            }),
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-gray-300 bg-gray-50 text-primary-600 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:focus:ring-primary-600 dark:ring-offset-gray-800',
            }),
        }

    def clean_target_amount(self):
        target_amount = self.cleaned_data.get('target_amount')
        if target_amount <= 0:
            raise forms.ValidationError("Target amount must be greater than zero.")
        return target_amount

    def clean_current_amount(self):
        current_amount = self.cleaned_data.get('current_amount')
        if current_amount < 0:
            raise forms.ValidationError("Current amount cannot be negative.")
        return current_amount
