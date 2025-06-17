import json
import requests


from api_auth import auth
import httpx

import asyncio

ACCESS_TOKEN_FUTURES = auth.get_token_futures()


async def modify_order_async(code, ordno, qty, prc, order_id_future_next):
    api_key = auth.get_token_futures()
    print("modified order")
    tr = "CFOAT00200"
    BASE_URL = "https://openapi.ls-sec.co.kr:8080"

    PATH = "futureoption/order"
    URL = f"{BASE_URL}/{PATH}"

    header = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {api_key}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock1": {
            "FnoIsuNo": code,
            "OrgOrdNo": ordno,
            "FnoOrdprcPtnCode": "00",  # 00@지정가03@시장가
            "FnoOrdPrc": prc,
            "MdfyQty": qty,
        }
    }

    # res = requests.post(URL, headers=header, data=json.dumps(body))
    # data = res.json()
    # return data
    async with httpx.AsyncClient() as client:
        response = await client.post(URL, headers=header, data=json.dumps(body))
        if response.status_code == 200:
            print("정정주문 성공")
            print(f"rsp_msg {response.json()['rsp_msg']}")
            order_id = response.json()[f"{tr}OutBlock2"]["OrdNo"]
            print(f"OutBlock2.OrdNo is {order_id}")

            if order_id_future_next is not None:
                order_id_future_next.set_result(order_id)

            return order_id

        else:
            print("주문 실패:", response.text)
            return None


def modify_fut(focode, ordno, qty, prc):
    """
    선물옵션(주간시장) 정정주문
    """
    tr = "CFOAT00200"
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
            "FnoOrdprcPtnCode": "00",  # 00@지정가03@시장가
            "FnoOrdPrc": prc,
            "MdfyQty": qty,
        }
    }
    res = requests.post(URL, headers=header, data=json.dumps(body))
    data = res.json()
    # return [data[f"{tr}OutBlock1"]], [data[f"{tr}OutBlock2"]]
    return data


if __name__ == "__main__":
    buysell = {"sell": "1", "buy": "2"}
    focode = "101V9000"

    qty = None  # 모든 잔량에 대해 정정함

    ordno = 25608
    prc = 380.64

    # data = modify_fut(focode, ordno, qty, prc)
    # print(data)  # type을 보기위함
    # for key, value in data.items():
    #     if isinstance(value, dict):
    #         print(f"dict:{key}")
    #         for key_, value_ in value.items():
    #             print(f"  {key_}: {value_}")
    #     else:
    #         print(f"{key}: {value}")

    asyncio.run(modify_order_async(focode, ordno, qty, prc, None))
