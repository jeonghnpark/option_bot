from django.contrib import admin

from .models import VolatilityData, FuturesPrice, FuturesOrderbook


# Register your models here.
@admin.register(VolatilityData)
class VolatilityDataAdmin(admin.ModelAdmin):

    list_display = ["date_time", "future_code", "option_code", "iv_20"]
    list_filter = ["date_time", "future_code", "option_code"]
    date_hierarchy = "date_time"
    search_fields = ["future_code", "option_code"]


@admin.register(FuturesPrice)
class FuturesPriceAdmin(admin.ModelAdmin):
    list_display = [
        "formatted_timestamp",
        "shcode",
        "price",
        "volume",
        "bidho1",
        "offerho1",
    ]
    list_filter = ["timestamp", "shcode"]
    search_fields = ["shcode"]

    def formatted_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    formatted_timestamp.short_description = "Timestamp"


@admin.register(FuturesOrderbook)
class FuturesOrderbookAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "shcode",
        "bid_price",
        "bid_volume",
        "ask_price",
        "ask_volume",
    ]
    list_filter = ["timestamp", "shcode"]
    date_hierarchy = "timestamp"
    search_fields = ["shcode"]
