import json
import requests

from api_auth import auth
from api_auth.auth import api_manager
import pandas as pd
from datetime import datetime, timedelta


def get_hist_fut(
    shcode=None, ncnt=1, sdate=None, edate=None, period_min=5, qrycnt=None
):
    """
    선물옵션차트(틱/n틱)

    """

    global api_manager
    dtnow = datetime.now()
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/chart"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()
    tr = "t8414"
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

        # Get current time
        # current_time = datetime.now().strftime("%H%M%S")

        # Calculate time 'period_min' minutes ago
        time_threshold = (dtnow - timedelta(minutes=period_min)).time()
        # cts_time을 datetime 객체로 변환
        cts_time_dt = datetime.strptime(cts_time[:6], "%H%M%S").time()

        # cts_time이 time_threshold보다 빠르면 while 루프 종료
        if cts_time_dt < time_threshold:
            break
        if qrycnt:
            break
        else:
            header["tr_cont"] = "Y"
        print(cts_time, cts_date)

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
    data = get_hist_fut(
        shcode="105VB000",
        ncnt=0,
        sdate=date_str,
        edate=date_str,
        period_min=30,
        qrycnt=None,
    )

    print(pd.DataFrame(data))
