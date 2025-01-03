# Generated by Django 5.1.4 on 2025-01-02 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0013_alter_transaction_transaction_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='goals',
            name='category',
            field=models.CharField(choices=[('food', 'Food'), ('transport', 'Transport'), ('entertainment', 'Entertainment'), ('utilities', 'Utilities'), ('clothing', 'Clothing'), ('health', 'Health'), ('education', 'Education'), ('gifts', 'Gifts'), ('savings', 'Savings'), ('investment', 'Investment'), ('insurance', 'Insurance'), ('taxes', 'Taxes'), ('rent', 'Rent'), ('credit', 'Credit'), ('salary', 'Salary'), ('interest', 'Interest'), ('other', 'Other')], default='salary', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subscription',
            name='category',
            field=models.CharField(choices=[('food', 'Food'), ('transport', 'Transport'), ('entertainment', 'Entertainment'), ('utilities', 'Utilities'), ('clothing', 'Clothing'), ('health', 'Health'), ('education', 'Education'), ('gifts', 'Gifts'), ('savings', 'Savings'), ('investment', 'Investment'), ('insurance', 'Insurance'), ('taxes', 'Taxes'), ('rent', 'Rent'), ('credit', 'Credit'), ('salary', 'Salary'), ('interest', 'Interest'), ('other', 'Other')], max_length=255),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='category',
            field=models.CharField(choices=[('food', 'Food'), ('transport', 'Transport'), ('entertainment', 'Entertainment'), ('utilities', 'Utilities'), ('clothing', 'Clothing'), ('health', 'Health'), ('education', 'Education'), ('gifts', 'Gifts'), ('savings', 'Savings'), ('investment', 'Investment'), ('insurance', 'Insurance'), ('taxes', 'Taxes'), ('rent', 'Rent'), ('credit', 'Credit'), ('salary', 'Salary'), ('interest', 'Interest'), ('other', 'Other')], max_length=50),
        ),
    ]
