from django.urls import path
from . import views


app_name = "order"

urlpatterns = [
    path("", views.index, name="index"),
    path("price/", views.get_price, name="getprice"),
    path("manual_order/", views.manual_order, name="manual_order"),
    path("portfolios/", views.portfolio_list, name="portfolio_list"),
    # path("fetchPortfolios/", views.fetchPortfolios, name="fetchPortfolios"),
    path(
        "fetchPortfolios_async/",
        views.fetchPortfolios_async,
        name="fetchPortfolios_async",
    ),
    path(
        "portfolios/<str:portfolio_id>/",
        views.portfolio_detail,
        name="portfolio_detail",
    ),
    path(
        "liquidate/<str:portfolio_id>/",
        views.manual_liquidate_portfolio,
        name="manual_liquidate_portfolio",
    ),
    path(
        "run_volatility_strategy/",
        views.run_volatility_strategy,
        name="run_volatility_strategy",
    ),
    path("set_vol_threshold/", views.set_vol_threshold, name="set_vol_threshold"),
    path(
        "check_auto_liquidation_status/",
        views.check_auto_liquidation_status,
        name="check_auto_liquidation_status",
    ),
    path(
        "start_auto_liquidation_task/",
        views.start_auto_liquidation_task,
        name="start_auto_liquidation_task",
    ),
    path(
        "start_flexswitch_strategy/",
        views.start_flexswitch_strategy,
        name="start_flexswitch_strategy",
    ),
    path(
        "check_strategy_status/",
        views.check_strategy_status,
        name="check_strategy_status",
    ),
    path("portfolio_stream/", views.portfolio_stream, name="portfolio_stream"),
    path(
        "start_portfolio_monitor_task/",
        views.start_portfolio_monitor_task,
        name="start_portfolio_monitor_task",
    ),
    path(
        "check_portfolio_monitor_status/",
        views.check_portfolio_monitor_status,
        name="check_portfolio_monitor_status",
    ),
]
