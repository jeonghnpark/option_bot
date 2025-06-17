from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote_plus
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

ACCESS_TOKEN = auth.get_token_futures()

BASE_URL = "https://openapi.ls-sec.co.kr:8080"

PATH = "stock/market-data"
URL = f"{BASE_URL}/{PATH}"
tr = "t1301"
header = {
    "content-type": "application/json; charset=utf-8",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "tr_cd": tr,
    "tr_cont": "N",
    "tr_cont_key": "",
}

body = {
    f"{tr}InBlock": {
        "shcode": "005930",
        "cvolume": 0,
        "starttime": "0900",
        "endtime": "1000",
        "cts_time": "",
    }
}
# res = requests.post(URL, headers=header, data=json.dumps(body))
# res = res.json()

# if res[f"{tr}OutBlock"]["cts_time"]:
#     print("oh")

# if len(res) >= 4:
#     print(pd.DataFrame([res[f"{tr}OutBlock"]]))
#     print(pd.DataFrame(res[f"{tr}OutBlock1"]))
# else:
#     print(pd.DataFrame([res[f"{tr}OutBlock"]]))

# 결과를 저장할 리스트
data = []

# 데이터 요청 및 합치기
while True:
    response = requests.post(URL, headers=header, data=json.dumps(body))

    response_json = response.json()

    # 받아온 데이터 추가
    data.extend(response_json[f"{tr}OutBlock1"])

    # cts_time 업데이트
    cts_time = response_json[f"{tr}OutBlock"]["cts_time"]
    if cts_time == "":
        break

    # 다음 요청을 위한 설정
    body[f"{tr}InBlock"]["cts_time"] = cts_time
    header["tr_cont"] = "Y"
    time.sleep(0.6)  # t1301 초당 2건
    print(cts_time)

print(pd.DataFrame(data))
