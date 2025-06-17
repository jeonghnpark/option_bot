# fastapi_app/app/schemas/orders.py
from pydantic import BaseModel
from typing import Optional


class OrderCreate(BaseModel):
    focode: str
    direction: str  # "buy" or "sell"
    price: float
    quantity: int


class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: Optional[str] = None
