import json
import requests

from api_auth import auth

import psycopg2


def get_maturity_datetime(maturity_code=None):
    with psycopg2.connect(
        host="localhost", database="postgres", user="postgres", password="1234"
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM maturity_set")
            rows = cur.fetchall()
            return rows


def get_listed_future(gubun="MF"):
    """
    상장 선물 마스터(MF)
    """
    ACCESS_TOKEN = auth.get_token_futures()
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    tr = "t8435"
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "gubun": gubun,
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))

    res = res.json()[f"{tr}OutBlock"]
    return res


if __name__ == "__main__":
    shcode_str = {"future_type": "MF", "yymm": "2405"}
    data = get_listed_future("MF")
    print(type(data))
    print(data)
    # print([e.get("shcode") for e in data])
    # shcode = [
    #     e["shcode"]
    #     for e in data
    #     if e["hname"][:2] == shcode_str.get("future_type")
    #     and e["hname"][-4:] == shcode_str.get("yymm")
    # ]
    # 미니 선물
    # print(pd.DataFrame(data))

    # result = get_maturity_datetime()
    # dt = []
    # print(result)
