# t8418 업종 챠트

# import os
# from dotenv import load_dotenv

# load_dotenv()
# APP_KEY = os.environ.get("EBEST-OPEN-API-APP-KEY-TEST")
# APP_SECRET = os.environ.get("EBEST-OPEN-API-SECRET-KEY-TEST")
import json
import requests

from api_auth import auth
import pandas as pd
import time

ACCESS_TOKEN = auth.get_token_futures()


def get_sector_hist(shcode="205", ncnt=0, sdate="", edate=""):
    """
    업종코드
       205: vkospi
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "indtp/chart"
    URL = f"{BASE_URL}/{PATH}"
    tr = "t8418"
    header = {
        "content-type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "shcode": shcode,  # vkospit
            "ncnt": ncnt,
            "sdate": sdate,  # 종료일(필수)
            "edate": edate,  # 종료일(필수)
            "comp_yn": "N",  # 반드시 입력할것
        }
    }

    # 연속조회 필요시
    data = []
    while True:
        response = requests.post(URL, headers=header, data=json.dumps(body))
        time.sleep(1.1)

        response_json = response.json()

        data[:0] = response_json[f"{tr}OutBlock1"]

        cts_time = response_json[f"{tr}OutBlock"]["cts_time"]
        cts_date = response_json[f"{tr}OutBlock"]["cts_date"]

        if cts_time == "" and cts_date == "":
            # print(pd.DataFrame(data))
            break

        # print(pd.DataFrame(data))
        # print(f"next cts_date{cts_date} next cts_time{cts_time}")

        body[f"{tr}InBlock"]["cts_time"] = cts_time
        body[f"{tr}InBlock"]["cts_date"] = cts_date
        header["tr_cont"] = "Y"

    return data


# res = requests.post(URL, headers=header, data=json.dumps(body))

# res = res.json()
# df = pd.DataFrame(res[f"{tr}OutBlock1"])
# print(df)

if __name__ == "__main__":
    data = get_sector_hist("205", 0, "20231227", "20231227")
    print(pd.DataFrame(data))
