import sys
import os

# 프로젝트 루트 디렉토리를 Python path에 추가 __main__으로 실행시 필요
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
sys.path.append(project_root)


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


async def get_current_orderbook_async(shcode="105V2000"):
    """
    선옵 호가 정보
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2105"
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
            "shcode": shcode,
        }
    }
    api_manager.wait_for_next_call(tr, time_for_a_call)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(URL, headers=header, data=json.dumps(body)) as res:
                res_json = await res.json()
                if f"{tr}OutBlock" not in res_json:
                    raise KeyError(f"'{tr}OutBlock' not found in response!!")
                return res_json[f"{tr}OutBlock"]

    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"api호출중 에러 발생 :{e}")
        return None


def get_current_orderbook(shcode="105V2000"):
    """
    선옵 호가 정보
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2105"
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
            "shcode": shcode,
        }
    }
    api_manager.wait_for_next_call(tr, time_for_a_call)
    try:
        res = requests.post(URL, headers=header, data=json.dumps(body))
        res.raise_for_status()
        res_json = res.json()
        if f"{tr}OutBlock" not in res_json:
            raise KeyError(f"'{tr}OutBlock' not found in response")
        return res_json[f"{tr}OutBlock"]
    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"api호출중 에러 발생 :{e}")
        return None


if __name__ == "__main__":

    # data = get_current_orderbook("105VB000")
    # if isinstance(data, list):
    #     df = pd.DataFrame([data])
    #     print(df)

    # # 데이터가 single item 사전인 경우: 리스트에 사전을 담아 DataFrame 생성에 사용하여 단일 행 DataFrame 생성
    # elif isinstance(data, dict):
    #     bid = float(data["bidho1"])
    #     ask = float(data.get("offerho1"))
    #     mid = float(data["bidho1"]) / 2.0 + float(data["offerho1"]) / 2.0
    #     print(bid, ask, mid)
    # else:
    #     raise ValueError("Unsupported data type")

    async_data = asyncio.run(get_current_orderbook_async("105VB000"))
    print(async_data)
