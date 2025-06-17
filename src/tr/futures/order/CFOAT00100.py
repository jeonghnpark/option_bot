import json
import requests
import httpx
import websockets
from api_auth import auth
from tr.futures.market_data.t2105 import get_current_orderbook
import asyncio
from datetime import datetime, timedelta

ACCESS_TOKEN_FUTURES = auth.get_token_futures()


def order_futoption(order_params):
    """
    선물옵션(주간시장) 정상 주문
    """
    tr = "CFOAT00100"
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/order"
    URL = f"{BASE_URL}/{PATH}"

    buysell = {"sell": "1", "buy": "2"}
    ordertype = {"limit": "00", "market": "03"}

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN_FUTURES}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock1": {
            "FnoIsuNo": order_params.get("focode"),
            "BnsTpCode": buysell.get(order_params.get("direction")),
            "FnoOrdprcPtnCode": "00",  # "00"  지정가
            "FnoOrdPrc": order_params.get("price"),
            "OrdQty": order_params.get("quantity"),
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    data = res.json()

    return data


if __name__ == "__main__":

    order_params = {
        "focode": "105V7000",
        "quantity": 5,
        "direction": "sell",
        "ordertype": "limit",
        "price": 381,
    }

    # #동기함수
    data = order_futoption(order_params)

    for key, value in data.items():
        if isinstance(value, dict):
            print(f"dict:{key}")
            for key_, value_ in value.items():
                print(f"  {key_}: {value_}")
        else:
            print(f"{key}: {value}")
