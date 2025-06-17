import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import FuturesPrice, FuturesOrderbook
from src.tr.futures.real import FC0, FH0, EC0, EH0
import asyncio
from collections import deque


class FuturesPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("FuturesPriceConsumer: connect called")
        await self.accept()
        self.shcode = self.scope["url_route"]["kwargs"]["shcode"]
        print(f"FuturesPriceConsumer: shcode {self.shcode}")
        import datetime

        current_time = datetime.datetime.now().time()
        if current_time >= datetime.time(18, 0):  # 오후 6시 이후
            pass
            # self.fc0_task = asyncio.create_task(
            #     EC0.connect(self.shcode, self.save_price)
            # )
            # self.fh0_task = asyncio.create_task(
            #     EH0.connect(self.shcode, self.save_orderbook)
            # )
        else:
            print("주간 데이터 수집")
            self.fc0_task = asyncio.create_task(
                FC0.connect(self.shcode, self.save_price)
            )
            # self.fh0_task = asyncio.create_task(
            #     FH0.connect(self.shcode, self.save_orderbook)
            # )

        self.price_queue = deque()
        self.last_save_time = asyncio.get_event_loop().time()
        self.save_interval = 3.0  # 3초

    async def disconnect(self, close_code):
        self.fc0_task.cancel()
        # self.fh0_task.cancel()
        await self._bulk_save_prices()  # 연결 종료 시 남은 데이터 저장

    #
    async def save_price(self, data):
        if data["body"] is not None:
            current_time = asyncio.get_event_loop().time()
            self.price_queue.append(data["body"])

            if current_time - self.last_save_time >= self.save_interval:
                await self._bulk_save_prices()
                self.last_save_time = current_time

            await self.send(
                text_data=json.dumps({"type": "price_update", "data": data})
            )

    async def _bulk_save_prices(self):
        if not self.price_queue:
            return

        bulk_create_data = [
            FuturesPrice(
                shcode=self.shcode,
                price=item["price"],
                volume=item["cvolume"],
                bidho1=item["bidho1"],
                offerho1=item["offerho1"],
            )
            for item in self.price_queue
        ]

        await FuturesPrice.objects.abulk_create(bulk_create_data)
        self.price_queue.clear()

    async def save_orderbook(self, data):
        # print(f"save_orderbook: data {data}")
        if data["body"] is not None:
            pass
            # print(f"saving_orderbook: data======================")
            # await FuturesOrderbook.objects.acreate(
            #     shcode=self.shcode,
            #     bid_price=data["bidho1"],
            #     bid_volume=data["bidrem1"],
            #     ask_price=data["offerho1"],
            #     ask_volume=data["offerrem1"],
            # )
            # await self.send(
            #     text_data=json.dumps({"type": "orderbook_update", "data": data})
            # )
