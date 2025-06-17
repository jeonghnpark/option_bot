# from urllib.request import Request, urlopen
# from urllib.parse import urlencode, quote_plus
# import os
from dotenv import load_dotenv
import time

load_dotenv()
# APP_KEY = os.environ.get("EBEST-OPEN-API-APP-KEY-TEST")
# APP_SECRET = os.environ.get("EBEST-OPEN-API-SECRET-KEY-TEST")
import json
import requests
import sys
from api_auth import auth
from api_auth.auth import api_manager
import pandas as pd

pd.set_option("display.max_rows", None)
# pd.set_option("display.max_columns", None)

from requests.exceptions import HTTPError, Timeout, ConnectionError


# last_api_call_time_t8429 = None


def get_eurex_ntick(focode="105V2000", cgubun="B", bgubun=0, cnt=999):
    """
    Eurex 야간 선물옵션 틱분별 체결 조회 데이터/ 최대 999개까지 조회가능/ 연속조회불가
    (주간 t8406와 형식적, 내용적 대응
    주간 t8415과 내용적으로 가장 가까운 tr임)
    당일 16:50 근처에서부터는 전일 야간값 조회가 안된다. 당일 야간시장 모드로 진입함.
    """
    # global last_api_call_time_t8429
    global api_manager

    tr = "t8429"
    time_for_a_call = 1.2  # 건당 인터벌
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/chart"
    URL = f"{BASE_URL}/{PATH}"
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
            "focode": focode,
            "cgubun": cgubun,
            "bgubun": bgubun,
            "cnt": cnt,
        }
    }
    try:
        # current_time = time.time()
        # if last_api_call_time_t8429 is not None:
        #     elapsed_time = current_time - last_api_call_time_t8429
        #     if elapsed_time < 1.0:
        #         time.sleep(1.0 - elapsed_time)

        # last_api_call_time_t8429 = time.time()
        api_manager.wait_for_next_call(tr, time_for_a_call)
        res = requests.post(URL, headers=header, data=json.dumps(body))
        data = res.json()
        res.raise_for_status()
    except HTTPError as http_err:
        # HTTP 오류 응답 처리 (예: 404, 500 등)
        print(f"HTTP error occurred: {http_err}")
        print(data["rsp_msg"])
        sys.exit(1)
    except Timeout as timeout_err:
        # 요청 시간 초과 처리
        print(f"Timeout error occurred: {timeout_err}")
        sys.exit(1)
    except ConnectionError as conn_err:
        # 연결 오류 처리
        print(f"Connection error occurred: {conn_err}")
        sys.exit(1)
    except ValueError as val_err:
        # 데이터 검증 오류 처리
        print(f"Validation error: {val_err}")
        sys.exit(1)
    except Exception as err:
        # 그 밖의 모든 예외 처리
        print(f"An error occurred: {err}")
        sys.exit(1)

    return data[f"{tr}OutBlock1"]


if __name__ == "__main__":
    # data = get_eurex_ntick("101VC000", "B", 1, 999)
    data = get_eurex_ntick("101VC000", "T", 1, 999)

    print(pd.DataFrame(data))
