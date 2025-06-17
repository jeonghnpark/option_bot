# from dotenv import load_dotenv

# load_dotenv()

import json
import requests

from api_auth import auth
from api_auth.auth import api_manager
import pandas as pd

import aiohttp
import asyncio

from requests.exceptions import RequestException
from json.decoder import JSONDecodeError

import logging


def get_current(shcode="105V2000"):
    """
    유렉스 선물 옵션 spot (<->주간상품 t2101 )
    """
    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2830"
    time_for_a_call = 0.34

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "focode": shcode,
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
        logging.error(f"{tr} api 호출중 에러 발생: {e}")
        return None


async def async_get_current(shcode="105V2000"):
    """
    Async 유렉스 선물 옵션 spot (<->주간상품 t2101 )
    요청 건수 초당 2건
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2830"
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "focode": shcode,
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=header, data=json.dumps(body)) as res:
            res_json = await res.json()
            return res_json[f"{tr}OutBlock"]


if __name__ == "__main__":
    data = get_current("105V4000")
    print(data.get("price"))
    print(pd.DataFrame([data]))

    # test async

    # data = asyncio.run(async_get_current("105V2000"))
    # print(data.get("price"))
    # print(pd.DataFrame([data]))
