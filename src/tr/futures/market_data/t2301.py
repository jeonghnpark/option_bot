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


def get_current_screen(yyyymm="202402", gubun="G"):
    """
    옵션 전광판
    gubun: "G" 정규장, "M" 미니, "W" 위클리
    """
    global api_manager
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()

    tr = "t2301"
    time_for_a_call = 0.55  # 초당 2회
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "yyyymm": yyyymm,
            "gubun": gubun,
        }
    }
    api_manager.wait_for_next_call(tr, time_for_a_call)
    try:
        res = requests.post(URL, headers=header, data=json.dumps(body))
        res.raise_for_status()

        res_json = res.json()
        if (
            f"{tr}OutBlock" not in res_json
            or f"{tr}OutBlock1" not in res_json
            or f"{tr}OutBlock2" not in res_json
        ):
            raise KeyError(f"{tr}OutBlock[] not found in response")
        return (
            res_json[f"{tr}OutBlock"],
            res_json[f"{tr}OutBlock1"],
            res_json[f"{tr}OutBlock2"],
        )
    except (RequestException, JSONDecodeError, KeyError) as e:
        logging.error(f"{tr}api호출중 에러 발생 :{e}")
        return None


# async버전 테스트중
async def async_get_current_screen(yyyymm="202402", gubun="G"):
    """
    ASYNC 옵션 전광판
    gubun: "G" 정규장, "M" 미니, "W" 위클리
    """

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"

    tr = "t2301"

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "yyyymm": yyyymm,
            "gubun": gubun,
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=header, data=json.dumps(body)) as res:
            res_json = await res.json()
            return (
                res_json[f"{tr}OutBlock"],
                res_json[f"{tr}OutBlock1"],
                res_json[f"{tr}OutBlock2"],
            )


if __name__ == "__main__":
    data = get_current_screen("202404", "G")

    print(pd.DataFrame(data[1]))

    # Test for async
    # async_data = asyncio.run(async_get_current_screen("202402", "G"))
    # print(f"async data :  {pd.DataFrame(data[2])}")
