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
    주간 선물 옵션 잔고
    """
    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/accno"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "CFOFQ02400"
    time_for_a_call = 1.01

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }
    body = {"CFOAQ50600InBlock1": {"RecCnt": 5, "RegMktCode": "99", "BuyDt": ""}}

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
    async 주간 선물 옵션 잔고
    """
    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/accno"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "CFOFQ02400"
    time_for_a_call = 1.01

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {f"{tr}InBlock1": {"RecCnt": 1, "RegMktCode": "99", "BuyDt": ""}}

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
    tr = "CFOFQ02400"
    focode = "105V7000"
    data_async = asyncio.run(get_current_remaining_async())
    print(data_async)

    # data = asyncio.run(get_current_remaining())
    # print(data)

    unstt_qty = None

    if data_async.get(f"{tr}OutBlock4"):
        for item in data_async.get(f"{tr}OutBlock4"):
            if item["IsuNo"] == focode:
                print(f"{item['IsuNo']} 잔고 {item['BalQty']} 방향 {item['BnsTpNm']}")
                break
    else:
        print(f"잔고 0 ")
