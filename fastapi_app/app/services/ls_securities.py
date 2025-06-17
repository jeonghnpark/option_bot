# fastapi_app/app/services/ls_securities.py
from app.schemas.orders import OrderCreate
import httpx
from typing import Dict
from api_auth import auth  # shared/api_auth


class LSSecuritiesClient:
    def __init__(self):
        self.base_url = "https://openapi.ls-sec.co.kr:8080"
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:

        return auth.get_token_futures()

    def _prepare_order_body(self, order: OrderCreate) -> Dict:
        buysell = {"sell": "1", "buy": "2"}

        return {
            "CFOAT00100InBlock1": {
                "FnoIsuNo": order.focode,
                "BnsTpCode": buysell.get(order.direction),
                "FnoOrdprcPtnCode": "00",  # 지정가
                "FnoOrdPrc": order.price,
                "OrdQty": order.quantity,
            }
        }

    async def place_order(self, order: OrderCreate):
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "tr_cd": "CFOAT00100",
            "tr_cont": "N",
            "tr_cont_key": "",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/futureoption/order",
                headers=headers,
                json=self._prepare_order_body(order),
            )
            return response.json()
