import json
import requests

from api_auth import auth
import pandas as pd

import aiohttp
import asyncio

from api_auth.auth import api_manager

from requests.exceptions import RequestException
from json.decoder import JSONDecodeError

import logging


def get_current_remaining():
    """
    선물 옵션 spot
    """
    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/accno"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "CEXAQ31100"
    time_for_a_call = 1.01

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        "CEXAQ31100InBlock1": {
            "RecCnt": 1,
            "IsuCode": "",
            "BalEvalTp": "1",
            "FutsPrcEvalTp": "2",
        }
    }

    api_manager.wait_for_next_call(tr, time_for_a_call)
    try:
        res = requests.post(URL, headers=header, data=json.dumps(body))
        res.raise_for_status()  # http에러시 예외 발생
        res_json = res.json()
        return res_json
    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"api호출중 에러 발생 :{e}")
        return None


async def get_current_remaining_async():
    """
    선물 옵션
    """
    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/accno"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "CEXAQ31100"
    time_for_a_call = 1.01

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        "CEXAQ31100InBlock1": {
            "RecCnt": 1,
            "IsuCode": "",
            "BalEvalTp": "1",
            "FutsPrcEvalTp": "2",
        }
    }

    api_manager.wait_for_next_call(tr, time_for_a_call)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(URL, headers=header, data=json.dumps(body)) as res:
                res_json = await res.json()
                return res_json
    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"api호출중 에러 발생 :{e}")
        return None


import asyncio

if __name__ == "__main__":
    # data = get_current_remaining()
    focode = "105V7000"
    data_async = asyncio.run(get_current_remaining_async())
    print(data_async)

    unstt_qty = None
    for item in data_async["CEXAQ31100OutBlock3"]:
        if item["FnoIsuNo"] == focode:
            unstt_qty = item["UnsttQty"]
            break
    print(f"{focode} 미결제 수량 {unstt_qty}")
