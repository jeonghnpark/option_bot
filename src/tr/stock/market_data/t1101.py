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

ACCESS_TOKEN = auth.get_token_futures()

BASE_URL = "https://openapi.ls-sec.co.kr:8080"

PATH = "stock/market-data"
URL = f"{BASE_URL}/{PATH}"
tr = "t1101"
header = {
    "content-type": "application/json; charset=utf-8",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "tr_cd": tr,
    "tr_cont": "N",
    "tr_cont_key": "",
}

body = {
    f"{tr}InBlock": {
        "shcode": "078020",
    }
}
res = requests.post(URL, headers=header, data=json.dumps(body))
res = res.json()
if len(res) >= 4:
    print(pd.DataFrame([res[f"{tr}OutBlock"]]))
    print(pd.DataFrame(res[f"{tr}OutBlock1"]))
else:
    print(pd.DataFrame([res[f"{tr}OutBlock"]]))
