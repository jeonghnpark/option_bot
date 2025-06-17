# 해외지수/환율/금리 조회
import os
from dotenv import load_dotenv

load_dotenv()
APP_KEY = os.environ.get("EBEST-OPEN-API-APP-KEY-TEST")
APP_SECRET = os.environ.get("EBEST-OPEN-API-SECRET-KEY-TEST")
import json
import requests

from api_auth import auth
import pandas as pd

ACCESS_TOKEN = auth.get_token_futures()


def get_foreign_hist(kind="S", symbol="KIR@CD91", cnt=999, jgbn="0"):
    """
    투자정보> 해외실시간 지수(실시간아님)
    CD금리 과거데이터
    symbol 목록
    CD금리 "KIR@CD91
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "stock/investinfo"
    URL = f"{BASE_URL}/{PATH}"
    tr = "t3518"
    header = {
        "content-type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "kind": kind,
            "symbol": symbol,
            "cnt": cnt,  # 최대 999
            "jgbn": jgbn,  # 0:일간
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    res = res.json()
    if len(res) >= 4:
        # print(pd.DataFrame([res[f"{tr}OutBlock"]]))
        # print(pd.DataFrame(res[f"{tr}OutBlock1"]))
        return res[f"{tr}OutBlock1"]
    else:
        # print(pd.DataFrame([res[f"{tr}OutBlock"]]))
        return [res[f"{tr}OutBlock"]]


if __name__ == "__main__":
    data = get_foreign_hist(kind="S", symbol="KIR@CD91", cnt=999, jgbn="0")
    refdate = "20231227"
    result = [e for e in data if e.get("date") == refdate]
    print(result[0].get("price"))
    # print(pd.DataFrame(data))
