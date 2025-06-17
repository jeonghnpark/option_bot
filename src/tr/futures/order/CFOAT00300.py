import json
import requests


from api_auth import auth


ACCESS_TOKEN_FUTURES = auth.get_token_futures()


def order_fut(focode, ordno, qty=None):
    """
    선물옵션(주간시장) 주문 취소
    """
    tr = "CFOAT00300"
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/order"
    URL = f"{BASE_URL}/{PATH}"

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
            "OrgOrdNo": ordno,
            "CancQty": qty,  # None인 경우 전량 취소
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    data = res.json()
    # return [data[f"{tr}OutBlock1"]], [data[f"{tr}OutBlock2"]]
    return data


if __name__ == "__main__":

    focode = "105V7000"
    qty = None  # None인 경우 전량 취소
    ordno = 23439

    data = order_fut(focode, ordno, qty)
    print(data)  # type을 보기위함
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"dict:{key}")
            for key_, value_ in value.items():
                print(f"  {key_}: {value_}")
        else:
            print(f"{key}: {value}")
