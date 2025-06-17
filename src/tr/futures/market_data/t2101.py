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


async def get_current_async(shcode="105V2000"):
    """
    async 선물 옵션 spot
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2101"
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


def get_current(shcode="105V2000"):
    """
    선물 옵션 spot
    """
    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2101"
    time_for_a_call = 0.34  # krx는 초당 3회

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
        res.raise_for_status()  # http에러시 예외 발생
        res_json = res.json()
        if f"{tr}OutBlock" not in res_json:
            raise KeyError(f"'{tr}OutBlock' not found in response")
        return res_json[f"{tr}OutBlock"]
    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"api호출중 에러 발생 :{e}")
        return None


if __name__ == "__main__":
    data = get_current("105V4000")
    # 데이터가 multiple item이 있는 list인 경우
    if isinstance(data, list):
        df = pd.DataFrame(data)
        print(df)

    # 데이터가 single item 사전인 경우: 리스트에 사전을 담아 DataFrame 생성에 사용하여 단일 행 DataFrame 생성
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
        print(df)
    else:
        raise ValueError("Unsupported data type")

    # async_data = asyncio.run(async_get_current("105V4000"))
    # print(async_data)
    # # print(f"async return {pd.DataFrame([async_data])}")
