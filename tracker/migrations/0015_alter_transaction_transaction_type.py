# Generated by Django 5.1.4 on 2025-01-02 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0014_goals_category_alter_subscription_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('expense', 'Expense'), ('expense', 'Take from balance'), ('add', 'Add to balance')], default='expense', max_length=7),
        ),
    ]
