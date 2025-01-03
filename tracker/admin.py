from django.contrib import admin
from .models import Transaction, Contribution, Goals

admin.site.register(Transaction)
admin.site.register(Contribution)
admin.site.register(Goals)
# Register your models here.
