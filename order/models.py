from django.db import models
import json
from datetime import datetime
from tr.futures.market_data.t2831 import (
    get_current_orderbook as get_current_orderbook_eurex,
    get_current_orderbook_async as get_current_orderbook_eurex_async,
)
from tr.futures.market_data.t2105 import (
    get_current_orderbook as get_current_orderbook,
    get_current_orderbook_async as get_current_orderbook_async,
)

import uuid
from django.utils import timezone

import logging

logger = logging.getLogger(__name__)


class Portfolio(models.Model):
    portfolio_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default="")

    pnl = models.FloatField(default=0.0)
    target_profit = models.FloatField(null=True, blank=True)
    strategy = models.CharField(
        max_length=50, default="manual_order"
    )  # 새로운 필드 추가
    description = models.CharField(max_length=255, default="")
    liquidation_condition = models.CharField(
        max_length=10,
        choices=[
            ("pl", "PL"),
            ("time", "Time"),
            ("pl_or_time", "PL or Time"),
            (None, "None"),
        ],
        default=None,
        null=True,
        blank=True,
    )
    liquidation_value = models.FloatField(null=True, blank=True)  # 이 필드를 추가

    liquidation_time_in_second = models.IntegerField(
        null=True, blank=True, default=300
    )  # 새로운 필드 추가

    async def ato_dict(self):
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "pnl": self.pnl,
            "target_profit": self.target_profit,
            "strategy": self.strategy,
            "description": self.description,
            "liquidation_condition": self.liquidation_condition,
            "liquidation_value": self.liquidation_value,
            "liquidation_time_in_second": self.liquidation_time_in_second,
            # 필요한 다른 필드들도 여기에 추가
        }

    def to_dict(self):
        return {
            "id": self.id,
            "portfolio_id": self.portfolio_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "pnl": self.pnl,
            "target_profit": self.target_profit,
            "strategy": self.strategy,
            "description": self.description,
            "liquidation_condition": self.liquidation_condition,
            "liquidation_value": self.liquidation_value,
            "liquidation_time_in_second": self.liquidation_time_in_second,
            # 필요한 다른 필드들도 여기에 추가
        }

    async def acalculate_final_pnl(self):
        trades_by_focode = {}
        async for (
            trade
        ) in self.trades.all():  # 포트폴리오 내의 모든 trade (foreign key)
            if trade.focode not in trades_by_focode:
                trades_by_focode[trade.focode] = {
                    "buy_volume": 0,
                    "sell_volume": 0,
                    "buy_total": 0,
                    "sell_total": 0,
                    "multiplier": trade.multiplier,
                }
            if trade.direction == "buy":
                trades_by_focode[trade.focode]["buy_volume"] += trade.volume
                trades_by_focode[trade.focode]["buy_total"] += (
                    trade.price * trade.volume
                )
            else:
                trades_by_focode[trade.focode]["sell_volume"] += trade.volume
                trades_by_focode[trade.focode]["sell_total"] += (
                    trade.price * trade.volume
                )

        # assure quantity is matched
        total_pnl = 0
        for focode, data in trades_by_focode.items():  # focode별로
            if data["buy_volume"] != data["sell_volume"]:
                logger.warning(
                    f"Portfolio {self.portfolio_id}의 {focode} 수량 불일치로 청산 불능: "
                    f"매수량 {data['buy_volume']}, 매도량 {data['sell_volume']}"
                )
                return None
            pnl = (data["sell_total"] - data["buy_total"]) * data["multiplier"]
            total_pnl += pnl

        return total_pnl

    async def acalculate_pnl(self, current_prices):
        total_pnl = 0
        trades = [trade async for trade in self.trades.all()]
        for trade in trades:
            # current_price = current_prices.get(trade.focode)
            prices = current_prices.get(trade.focode)
            if prices is None:
                print(f"{trade.focode} 가격조회 안됨")
                continue

            if trade.direction == "buy":
                trade_pnl = (
                    (prices["mid"] - trade.price) * trade.volume * trade.multiplier
                )
            else:  # sell
                trade_pnl = (
                    (trade.price - prices["mid"]) * trade.volume * trade.multiplier
                )
            total_pnl += trade_pnl
        return total_pnl

    # def calculate_pnl(self, current_prices):
    #     total_pnl = 0
    #     for trade in self.trades.all():
    #         prices = current_prices.get(trade.focode)
    #         if prices is None:
    #             print(f"{trade.focode}가격조회 안됨")
    #             continue

    #         if trade.direction == "buy":
    #             trade_pnl = (
    #                 (prices["bid"] - trade.price) * trade.volume * trade.multiplier
    #             )
    #         else:  # sell
    #             trade_pnl = (
    #                 (trade.price - prices["ask"]) * trade.volume * trade.multiplier
    #             )
    #         total_pnl += trade_pnl
    #         # if self.portfolio_id == "p0828200031_a0798069":
    #         #     print(
    #         #         f"current price of {self.portfolio_id}  : {current_price} direction {trade.direction} "
    #         #     )
    #         #     print(
    #         #         f"trade.price {trade.price}  trade.volume {trade.volume} trade.multiplier{trade.multiplier}"
    #         #     )
    #         #     print(total_pnl)
    #     return total_pnl

    def __str__(self):
        return f"{self.portfolio_id}"

    @classmethod
    def get_all_unique_codes(cls):
        unique_codes = set(Trade.objects.values_list("focode", flat=True).distinct())
        return unique_codes

    @classmethod
    async def aget_all_unique_codes(cls):
        unique_codes = set()
        async for code in Trade.objects.values_list("focode", flat=True).distinct():
            unique_codes.add(code)
        return unique_codes

    async def aget_unique_focode(self):
        unique_codes = set()
        async for trade in self.trades.all():
            unique_codes.add(trade.focode)
        return unique_codes

    # @staticmethod
    # def get_current_prices(codes):
    #     current_time = datetime.now().time()
    #     if current_time.hour >= 18 or current_time.hour < 5:
    #         get_orderbook = get_current_orderbook_eurex
    #     else:
    #         get_orderbook = get_current_orderbook

    #     prices = {}
    #     for code in codes:
    #         try:
    #             orderbook = get_orderbook(code)
    #             mid_price = (
    #                 float(orderbook["bidho1"]) + float(orderbook["offerho1"])
    #             ) / 2
    #             prices[code] = mid_price
    #         except Exception as e:
    #             print(
    #                 f"Error fetching price for {code} in def get_current_prices: {str(e)}"
    #             )
    #             prices[code] = None

    #     return prices

    @staticmethod
    async def aget_current_prices(codes):
        # current_time = datetime.now().time()
        # if current_time.hour >= 18 or current_time.hour < 5:
        #     get_orderbook = get_current_orderbook_eurex_async
        # else:
        #     get_orderbook = get_current_orderbook_async
        current_time = datetime.now().time()
        prices = {}
        for code in codes:
            try:

                if current_time.hour >= 18 or current_time.hour < 5:
                    orderbook = await get_current_orderbook_eurex_async(code)
                else:
                    orderbook = await get_current_orderbook_async(code)

                bid_price = float(orderbook["bidho1"])
                ask_price = float(orderbook["offerho1"])
                mid_price = (bid_price + ask_price) / 2

                # orderbook = get_orderbook(code)
                # mid_price = (
                #     float(orderbook["bidho1"]) + float(orderbook["offerho1"])
                # ) / 2
                prices[code] = {"bid": bid_price, "ask": ask_price, "mid": mid_price}
            except Exception as e:
                print(
                    f"Error fetching price for {code} in async aget_current_prices: {str(e)}"
                )
                prices[code] = None

        return prices


class Trade(models.Model):
    portfolio = models.ForeignKey(
        "Portfolio", related_name="trades", on_delete=models.CASCADE
    )
    order_id = models.CharField(max_length=50)
    focode = models.CharField(max_length=20)
    price = models.FloatField()
    volume = models.IntegerField()
    multiplier = models.IntegerField(default=1)
    direction = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Trade {self.focode} for Portfolio {self.portfolio.portfolio_id}"
