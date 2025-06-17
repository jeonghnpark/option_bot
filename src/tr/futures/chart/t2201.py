import time
from datetime import datetime, timedelta
import json
import requests

from api_auth import auth
import pandas as pd


def get_hist_chetime(focode, cvolume, stime="", etime=""):
    """
    tr2201 시간대별 체결조회(체결이 없으면 데이터가 없음)
    InBlock : focode, stime[option], etime[option]
    OutBlock : chetime, price
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()
    tr = "t2201"
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "focode": focode,
            "cvolume": cvolume,
            "stime": stime,
            "etime": etime,
            "cts_time": "",
        }
    }

    # pd.set_option("display.max_rows", None)
    # 연속조회
    data = []
    while True:
        response = requests.post(URL, headers=header, data=json.dumps(body))
        time.sleep(0.7)  # 초당 2회
        response_json = response.json()
        data.extend(response_json[f"{tr}OutBlock1"])
        cts_time = response_json[f"{tr}OutBlock"]["cts_time"]

        if cts_time == "":
            break

        print(f"next cts_time{cts_time}")
        body[f"{tr}InBlock"]["cts_time"] = cts_time
        header["tr_cont"] = "Y"

    return data


if __name__ == "__main__":

    def get_time_minus_5_minutes():
        current_time = datetime.now()
        time_minus_5 = current_time - timedelta(minutes=5)
        return time_minus_5.strftime("%H%M")

    stime = get_time_minus_5_minutes()
    print(stime)
    tr = "t2201"

    data = get_hist_chetime("105VC000", cvolume=1, stime=get_time_minus_5_minutes())
    # data = get_hist_chetime("105VA000", cvolume=1, stime="1315", etime="1318")
    # data = get_hist_chetime("105VA000", cvolume=2, stime="1310")
    # print(pd.DataFrame(data[f"t2201OutBlock1"]))
    pd.set_option("display.max_rows", None)

    print(type(data))
    print(pd.DataFrame(data))

    # 최대 최소구하기
    current_time = datetime.now()
    five_min_ago = current_time - timedelta(minutes=1)
    recent_data = [
        d
        for d in data
        if datetime.strptime(d["chetime"][:6], "%H%M%S").time() >= five_min_ago.time()
    ]
    print(pd.DataFrame(recent_data))

    df = pd.DataFrame(recent_data)
    print(f"min of price: {df['price'].min()}")
    print(f"max of price: {df['price'].max()}")

    prices = [float(d["price"]) for d in recent_data]
    print(f"min of price: {min(prices)}")
    print(f"max of price: {max(prices)}")
