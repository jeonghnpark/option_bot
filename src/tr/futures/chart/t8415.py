import json
import requests

from api_auth import auth
from api_auth.auth import api_manager
import pandas as pd
from datetime import datetime


def get_hist_fut(shcode=None, ncnt=1, sdate=None, edate=None, qrycnt=None):
    """
    선물/옵션 차트(N분)
    과거날짜 연속조회 가능(최대 5개월까지) t2209는 과거x, 현재 시점기준 과거
    ncnt 0:30초, 1:1분, ..
    호출제한 : 1건/1초

    InBlock :shcode, ncnt, sdate, edate, qrycnt
    ncnt : N분 간격
    qrycnt는 반복조회시 한번에 받는 데이터의 개수를 나타내나 구현상 금지해놓았음(jh)
    qrycnt를 입력하는 경우는 소수의 데이터를 받을때
    긴데이터를 받는 경우 qrycnt는 입력하지 말고 default값인 500으로 받을것(비압축인경우)

    OutBlock : date, time, open, high, low, close
    """

    global api_manager

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/chart"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()
    tr = "t8415"
    time_for_a_call = 1.2  # 초당 1회면 1.0, 초당 3회면 0.34
    header = {
        "content-type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock": {
            "shcode": shcode,
            "ncnt": ncnt,
            "qrycnt": qrycnt,
            "sdate": sdate,
            "edate": edate,
            "comp_yn": "N",
        }
    }

    # 연속조회
    data = []
    while True:
        # current_time = time.time()
        # if last_api_call_time is not None:
        #     elapsed_time = current_time - last_api_call_time
        #     if elapsed_time < 1.0:
        #         time.sleep(1.0 - elapsed_time)
        # # 이 경우에 너무 tight하게 호출하는 것인가? time.sleep(1.01) 로 호출해볼것
        # last_api_call_time = time.time()

        api_manager.wait_for_next_call(tr, time_for_a_call)
        response = requests.post(URL, headers=header, data=json.dumps(body))

        response_json = response.json()
        data[:0] = response_json[f"{tr}OutBlock1"]
        cts_time = response_json[f"{tr}OutBlock"]["cts_time"]
        cts_date = response_json[f"{tr}OutBlock"]["cts_date"]

        if cts_time == "" and cts_date == "":
            break

        body[f"{tr}InBlock"]["cts_time"] = cts_time
        body[f"{tr}InBlock"]["cts_date"] = cts_date
        if qrycnt:
            break
        else:
            header["tr_cont"] = "Y"

    return data


if __name__ == "__main__":
    date_str = datetime.now().strftime("%Y%m%d")
    print(date_str)
    # tod = datetime.date.today().strftime("%Y%m%d")
    # print(tod)
    # tod = datetime.now().strftime("%Y%m%d")
    # print(tod)

    # 호출 예시
    # 5분간격 금일 모든 데이터 (연속조회, qrycnt를 입력하지 않는다. None)
    # data = get_hist_fut("105V9000", 5, date_str, date_str)

    # 1분간격으로 최근 데이터 소수만 받는다. qrycnt를 입력하는 경우는 반복조회를 하지 않는다.
    data = get_hist_fut(shcode="101VC000", ncnt=1, sdate=date_str, edate=date_str)

    print(pd.DataFrame(data))
