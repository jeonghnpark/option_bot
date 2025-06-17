from django.contrib import admin
from .models import Portfolio
from .models import Trade

# Register your models here.


@admin.register(Portfolio)
class AdminPortfolio(admin.ModelAdmin):
    pass


@admin.register(Trade)
class AdminPortfolio(admin.ModelAdmin):
    pass
