from dataclasses import dataclass
from typing import List, Optional
import asyncio


@dataclass
class Order:
    focode: str
    quantity: int
    direction: str
    order_type: str
    price: Optional[float] = None
    order_id: Optional[str] = None
    status: str = "pending"
    order_id_future: Optional[asyncio.Future] = None
    websocket_open_event: Optional[asyncio.Event] = None
    message_ready_event: Optional[asyncio.Event] = None
    description: Optional[str] = None  # 설명 필드 추가

    def to_dict(self):
        return {
            "focode": self.focode,
            "quantity": self.quantity,
            "direction": self.direction,
            "orderType": self.order_type,
            "price": self.price,
        }


class OrderManager:
    def __init__(
        self, order_category="new", portfolio_id=None, target_profit=None, strategy=None
    ):

        self.order_category = order_category  # 'new', 'liquidation', 'correction'
        self.portfolio_id = portfolio_id
        self.target_profit = target_profit
        self.strategy = strategy  # 'manual_order', 'volatility_strategy'
        self.orders: List[Order] = []
        self.completed_orders = []
        self.cancelled_orders = []
        self.partially_filled_orders = []

    def add_order(self, order: Order):
        self.orders.append(order)

    def get_pending_orders(self):
        return [order for order in self.orders if order.status == "pending"]

    def get_completed_orders(self):
        return [order for order in self.orders if order.status == "completed"]

    def get_cancelled_orders(self):
        return [order for order in self.orders if order.status == "cancelled"]

    def get_partially_filled_orders(self):
        return [order for order in self.orders if order.status == "partially_filled"]

    def update_order_status(self, order_id: str, status: str):
        for order in self.orders:
            if order.order_id == order_id:
                order.status = status
                break
