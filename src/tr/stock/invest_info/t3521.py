# 해외지수/환율/선물
import os
from dotenv import load_dotenv

load_dotenv()
APP_KEY = os.environ.get("EBEST-OPEN-API-APP-KEY-TEST")
APP_SECRET = os.environ.get("EBEST-OPEN-API-SECRET-KEY-TEST")
import json
import requests

from api_auth import auth
import pandas as pd
import time


def get_cd_rate():
    """
    해외지수 spot
    symbol
    cd금리 KIR@CD91
    """
    ACCESS_TOKEN = auth.get_token_futures()

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "stock/investinfo"
    URL = f"{BASE_URL}/{PATH}"
    tr = "t3521"
    header = {
        "content-type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "kind": "S",
            "symbol": "KIR@CD91",
        }
    }

    res = requests.post(URL, headers=header, data=json.dumps(body))
    res_json = res.json()
    if f"{tr}OutBlock" not in res_json:
        raise KeyError(f"'{tr}OutBlock' not found in response")
    return res_json[f"{tr}OutBlock"]


if __name__ == "__main__":
    data = get_cd_rate()
    print(data)
