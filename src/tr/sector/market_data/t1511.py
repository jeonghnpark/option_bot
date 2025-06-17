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


def get_sector_spot(upcode="205"):
    """
    업종코드(spot)
    205: vkospi
    """
    ACCESS_TOKEN = auth.get_token_futures()

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"
    PATH = "indtp/market-data"
    URL = f"{BASE_URL}/{PATH}"
    tr = "t1511"

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "upcode": upcode,
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    # requset = requests.post(URL,  data=json.dumps(body))
    res_json = res.json()
    return res_json[f"{tr}OutBlock"]
    # print(f"vkospi {res_json[f'{tr}OutBlock']['pricejisu']}")
    # print(pd.DataFrame(res_json))

    # res=res.json()
    # df=pd.DataFrame(res)
    # df=pd.DataFrame(res)
    # print(df)


if __name__ == "__main__":
    data = get_sector_spot("205")
    print(data["pricejisu"])
