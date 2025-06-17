import json
import requests

from api_auth import auth
import pandas as pd


def get_options_codes(matcode=""):
    """
    상장옵션 마스터
    matcode[opt]: "V2"
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    tr = "t8433"
    ACCESS_TOKEN = auth.get_token_futures()
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "dummy": "",
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    # requset = requests.post(URL,  data=json.dumps(body))
    # print(f"price : {res.json()['t8435OutBlock']}")

    res = res.json()[f"{tr}OutBlock"]
    if matcode:
        filtered = [item for item in res if item["shcode"][3:5] == matcode]
        return filtered
    return res

    # df = pd.DataFrame(res)
    # print(df)


if __name__ == "__main__":
    data = get_options_codes("V9")
    print(pd.DataFrame(data))
