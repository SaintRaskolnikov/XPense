from django import forms
from .models import Transaction, Contribution, Subscription
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