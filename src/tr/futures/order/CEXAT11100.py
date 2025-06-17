from dotenv import load_dotenv

load_dotenv()

import json
import requests
import pandas as pd

from api_auth import auth


def order_fut(focode, bnstpcode, qty, prc):
    """
    야간 선물옵션 정상 주문
    """
    tr = "CEXAT11100"
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/order"
    URL = f"{BASE_URL}/{PATH}"
    ACCESS_TOKEN_FUTURES = auth.get_token_futures()

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN_FUTURES}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock1": {
            "FnoIsuNo": focode,
            "OrdPrc": prc,
            "BnsTpCode": bnstpcode,
            "ErxPrcCndiTpCode": "2",
            "OrdQty": qty,
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    data = res.json()
    return data
    # return [data[f"{tr}OutBlock1"]], [data[f"{tr}OutBlock2"]]


if __name__ == "__main__":
    buysell = {"sell": "1", "buy": "2"}
    focode = "105V7000"
    # focode = "301V2330"
    prc = 377.60
    qty = 1
    data = order_fut(focode, buysell.get("buy"), qty, prc)

    # print(pd.DataFrame(data1))
    # print(pd.DataFrame(data2))
    # print(
    #     f"주문번호:{data2[0].get('OrdNo')} 종목명:{data1[0].get('FnoIsuNo')} 주문수량:{data1[0].get('OrdQty')} 방향 :{'매도' if data1[0].get('BnsTpCode')=='1' else '매수' if data1[0].get('BnsTpCode')=='2' else 'sth wrong'}"
    # )
    print(data)
