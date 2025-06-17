from django.urls import path
from . import views

app_name = "trading"  # 프로젝트 레벨의 namespace='trading'

urlpatterns = [
    # 여기에 URL 패턴을 추가할 예정입니다.
    path("", views.index, name="index"),
    path("init/", views.init, name="init"),
    path("impvol/", views.calc_spot_vol, name="impvol"),
    path("historic/", views.historic, name="historic"),
    path("graph/", views.graph, name="graph"),
    path("futures_price/", views.futures_price_view, name="futures_price"),
    path("start_collection/", views.start_collection, name="start_collection"),
    path("stop_collection/", views.stop_collection, name="stop_collection"),
]
