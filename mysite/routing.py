from django.urls import re_path
from trading import consumers

websocket_urlpatterns = [
    re_path(r"ws/futures/(?P<shcode>\w+)/$", consumers.FuturesPriceConsumer.as_asgi()),
]
