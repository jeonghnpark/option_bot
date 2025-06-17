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

PATH = "stock/chart"
URL = f"{BASE_URL}/{PATH}"
tr = "t8412"
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
        "ncnt": 30,
        "sdate": "20231212",
        "edate": "20231218",
    }
}
res = requests.post(URL, headers=header, data=json.dumps(body))

res = res.json()
print(res["t8412OutBlock"])
# df = pd.DataFrame(res["t8412OutBlock"])
# print(df)
# df = pd.DataFrame(res["t8412OutBlock"])
# print(df)
