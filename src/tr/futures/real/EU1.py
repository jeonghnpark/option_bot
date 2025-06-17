from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

import json


from api_auth import auth

import websockets
import asyncio


async def message_handler(websocket):
    """
    서버로부터 메시지를 수신시 호출되어 처리
    """
    async for message in websocket:
        dict_data = json.loads(message)
        body = dict_data["body"]
        if body is not None:
            for key, value in body.items():
                print(f"{key}: {value}")
            print(
                f"------------------------{datetime.now()}"
            )  # 항목을 구분하기 위한 구분선


async def get_done_eurex():
    """
    주문에 대한 "야간" 시장 선옵 체결
    주문을 넣어도 반응한다?
    """
    tr = "EU1"
    ACCESS_TOKEN = auth.get_token_futures()
    header = {"token": ACCESS_TOKEN, "tr_type": "1"}
    body = {"tr_cd": tr, "tr_key": ""}
    # 두 딕셔너리를 하나로 결합
    combined_dict = {"header": header, "body": body}

    json_string = json.dumps(combined_dict)

    async with websockets.connect(
        "wss://openapi.ls-sec.co.kr:29443/websocket"
    ) as websocket:
        print("야간 선물옵션 체결 모니터링.. ")
        await websocket.send(json_string)
        await message_handler(websocket)


asyncio.run(get_done_eurex())
