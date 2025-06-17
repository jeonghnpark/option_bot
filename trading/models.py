from django.db import models


class VolatilityData(models.Model):
    date_time = models.DateTimeField(unique=True)
    iv_20 = models.FloatField()
    option_code = models.CharField(max_length=50)
    option_price = models.FloatField()
    option_delta = models.FloatField()
    option_gamma = models.FloatField(default=0)
    option_vega = models.FloatField(default=0)
    option_theta = models.FloatField(default=0)
    future_code = models.CharField(max_length=50)
    future_price = models.FloatField()

    def __str__(self):
        return str(self.date_time) + "-" + self.future_code


class FuturesPrice(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    shcode = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    bidho1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    offerho1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    volume = models.IntegerField()


class FuturesOrderbook(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    shcode = models.CharField(max_length=10)
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)
    bid_volume = models.IntegerField()
    ask_price = models.DecimalField(max_digits=10, decimal_places=2)
    ask_volume = models.IntegerField()
