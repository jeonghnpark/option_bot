import time

from datetime import datetime, timedelta
import json
import requests

# from api_auth import auth
import pandas as pd
import sys
import os

# 프로젝트 루트 디렉토리를 시스템 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)
print(project_root)
from api_auth import auth


def get_eurex_time_tick(focode="", cvolume=1, stime="", etime=""):
    """
    eurex 선물옵션 시간대별 체결 조회 (체결tick)
    당일 조회
    """
    # # from api_auth import auth
    # import pandas as pd
    # import sys
    # import os

    # # 프로젝트 루트 디렉토리를 시스템 경로에 추가
    # project_root = os.path.abspath(
    #     os.path.join(os.path.dirname(__file__), "../../../..")
    # )
    # sys.path.append(project_root)
    # print(project_root)
    # from api_auth import auth

    ACCESS_TOKEN = auth.get_token_futures()

    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/market-data"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN = auth.get_token_futures()
    tr = "t2832"
    header = {
        "content-type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    ## 연속데이터 조회필요시 OutBlock key에 cts_date, cts_time에 정보가 들어옴
    ## 연속 조회 필요없을시 "" 가 들어옴
    # 예시1:
    # sdate를 입력하는 경우 qrycnt=500으로 자동 설정됨
    # sdate를 20230701로 설정하였으나 20230714까지만 조회
    body = {
        f"{tr}InBlock": {
            "focode": focode,
            "cvolume": cvolume,
            "stime": stime,
            "etime": etime,
            "cts_time": "",
        }
    }
    # 예시2:
    # sdate를 입력하지 않고 qrycnt=300으로 설정, 이 경우 6개월 전부터 edate까지 ncnt분 간격으로 qrycnt씩 조회함
    # body = {
    #     f"{tr}InBlock": {
    #         "focode": "105V1000",
    #         "ncnt": 3,
    #         "qrycnt": 300,
    #         "edate": "20231001",
    #         "comp_yn": "N",
    #     }
    # }

    # 연속조회
    data = []
    while True:
        response = requests.post(URL, headers=header, data=json.dumps(body))
        time.sleep(0.6)  # 초당 2회
        response_json = response.json()
        # data[:0] = response_json[f"{tr}OutBlock1"]
        data.extend(response_json[f"{tr}OutBlock1"])
        cts_time = response_json[f"{tr}OutBlock"]["cts_time"]
        # cts_date = response_json[f"{tr}OutBlock"]["cts_date"]

        if cts_time == "":
            # print(pd.DataFrame(data))
            break

        # print(pd.DataFrame(data))
        print(f"next cts_time{cts_time}")
        body[f"{tr}InBlock"]["cts_time"] = cts_time
        header["tr_cont"] = "Y"
    return data


if __name__ == "__main__":

    def get_time_minus_5_minutes():
        current_time = datetime.now()
        time_minus_5 = current_time - timedelta(minutes=5)
        return time_minus_5.strftime("%H%M")

    # 현재시간보다 5분전 시간 출력
    print(get_time_minus_5_minutes())

    data = get_eurex_time_tick(
        focode="105VC000", cvolume=1, stime=get_time_minus_5_minutes()
    )
    print(pd.DataFrame(data))
