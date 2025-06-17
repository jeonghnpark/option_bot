import os
import django

# Django 설정 모듈 경로 설정
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "mysite.settings"
)  # mysite는 프로젝트 이름에 맞게 변경하세요

# Django 설정 초기화
django.setup()

import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from tr.futures.chart.t8415 import get_hist_fut
from tr.futures.real.FH0 import connect
from tr.futures.order.CFOAT00100 import order_futoption
from tr.futures.order.CFOAT00300 import order_fut

from order.views import place_orders, generate_portfolio_id
from order.order_manager import OrderManager, Order
from order.models import Portfolio


class BuyDipStrategy:
    def __init__(self, shcode, interval=5):
        self.shcode = shcode
        self.interval = interval
        self.historical_data = None
        self.current_price = None
        self.position = None

    async def run(self):
        await self.get_historical_data()
        await self.monitor_real_time_data()

    async def get_historical_data(self):
        end_date = datetime.now().strftime("%Y%m%d")
        # start_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        data = get_hist_fut(self.shcode, self.interval, end_date, end_date)
        self.historical_data = pd.DataFrame(data)
        self.historical_data["date"] = pd.to_datetime(
            self.historical_data["date"] + self.historical_data["time"]
        )
        self.historical_data.set_index("date", inplace=True)
        self.historical_data["close"] = self.historical_data["close"].astype(float)
        print(self.historical_data)

    async def monitor_real_time_data(self):
        await connect(self.shcode, self.on_price_update)

    async def on_price_update(self, price_data):
        self.current_price = (
            float(price_data["bidho1"]) + float(price_data["offerho1"])
        ) / 2
        await self.check_signal()

    async def check_signal(self):
        if self.position is not None:
            await self.check_exit()
        else:
            await self.check_entry()

    async def check_entry(self):
        # 최근 5분 데이터 가져오기
        recent_data = self.historical_data.iloc[-5:].copy()
        # 데이터 타입을 float으로 변환
        recent_data["high"] = recent_data["high"].astype(float)
        recent_data["low"] = recent_data["low"].astype(float)

        # 가격 범위 계산
        price_range = recent_data["high"].max() - recent_data["low"].min()
        print(f"price_range {price_range:2f}")
        # 하한 임계값 계산
        lower_threshold = recent_data["low"].min() + price_range * 0.1
        print(
            f"lower_threshold {lower_threshold:.2f} vs self.current_price {self.current_price:.2f}"
        )

        # 현재 가격이 하한 임계값 이하인 경우 포지션 진입
        if self.current_price <= lower_threshold:
            await self.enter_position()

    async def enter_position(self):
        order_params = {
            "focode": self.shcode,
            "quantity": 1,
            "direction": "buy",
            "order_type": "market",
            "price": None,
        }
        order_manager = OrderManager(
            portfolio_id=generate_portfolio_id(), strategy="buydip"
        )
        order = Order(**order_params)

        order_manager.add_order(order)

        order_result, portfolio_id = await place_orders(order_manager)

        print(f"order_result {order_result}")

        all_completed = all(result["status"] == "completed" for result in order_result)

        portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
        portfolio.status = "Active" if all_completed else "Pending"
        portfolio.description = (
            "Holding on strategy buy dip"
            if all_completed
            else "Pending by incompleted trades"
        )
        await portfolio.asave()

    async def check_exit(self):
        if datetime.now() - self.position["entry_time"] >= timedelta(minutes=5):
            await self.exit_position()

    async def exit_position(self):
        order_result = order_fut(self.shcode, self.position["order_id"])
        if order_result["status"] == "success":
            self.position = None


async def main():
    strategy = BuyDipStrategy(shcode="105V9000")  # 코스피200 선물 코드
    await strategy.run()


if __name__ == "__main__":
    asyncio.run(main())
