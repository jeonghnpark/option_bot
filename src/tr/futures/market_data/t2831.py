import json
import requests

from api_auth import auth
import pandas as pd

from api_auth.auth import api_manager
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
import logging
import aiohttp


def get_current_orderbook(shcode="105V2000"):
    """
    Eurex 선옵 spot 호가
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()
    tr = "t2831"
    time_for_a_call = 0.51  # 유렉스는 초당 2회
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "shcode": shcode,
        }
    }
    api_manager.wait_for_next_call(tr, time_for_a_call)
    try:
        res = requests.post(URL, headers=header, data=json.dumps(body))
        res.raise_for_status()
        res_json = res.json()
        if f"{tr}OutBlock" not in res_json:
            raise KeyError(f"{tr}OutBlock not found in response")
        return res_json[f"{tr}OutBlock"]
    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"api호출중 에러 발생 :{e}")
        return None


async def get_current_orderbook_async(shcode="105V2000"):
    """
    Eurex 선옵 spot 호가
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()
    tr = "t2831"
    time_for_a_call = 0.51  # 유렉스는 초당 2회
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "shcode": shcode,
        }
    }
    api_manager.wait_for_next_call(tr, time_for_a_call)

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=header, data=json.dumps(body)) as res:
            res_json = await res.json()
            return res_json[f"{tr}OutBlock"]


if __name__ == "__main__":
    data = get_current_orderbook("105VC000")
    print(data)
    # print(pd.DataFrame([data]))
