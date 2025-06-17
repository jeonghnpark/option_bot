from dotenv import load_dotenv

load_dotenv()

import json
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError

from api_auth import auth
import pandas as pd

import sys

ACCESS_TOKEN = auth.get_token_futures()


def get_ntick(focode="105V2000", cgubun="B", bgubun=0, cnt=999):
    """
    선물옵션 틱분별 체결 조회 (야간 t8429에 대응)
    현재시점부터 과거 N분데이터 받기/과거 N tick받기
    cgubun :  "B" 분차트, "T" 틱차트
    최대 999개까지 가능
    """
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/chart"
    URL = f"{BASE_URL}/{PATH}"

    tr = "t2209"
    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "tr_cd": "t2209",
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        "t2209InBlock": {
            "focode": focode,
            "cgubun": cgubun,
            "bgubun": bgubun,
            "cnt": cnt,
        }
    }

    try:
        res = requests.post(URL, headers=header, data=json.dumps(body))
        data = res.json()
        res.raise_for_status()

        # 내용 검증
        # 예: JSON 응답이 기대되는 경우
        # data = res.json()
        # if "필요한 키" not in data:
        #     raise ValueError("응답에서 필요한 데이터가 누락되었습니다.")

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
    data = get_ntick("105V3000", "B", 1, 999)
    print(pd.DataFrame(data))
