# 1000초 기다렸다가 모니터링 종료
from datetime import datetime
import json
from api_auth import auth
import websockets
import asyncio


async def message_handler(websocket):
    """
    서버로부터 메시지를 수신시 호출되어 처리
    """
    async for message in websocket:
        print("message 수신됨====== ")
        dict_data = json.loads(message)
        body = dict_data["body"]
        if body is not None:
            # print(body)  # 타입을 보기위함
            for key, value in body.items():
                print(f"{key}: {value}")
            print(
                f"------------------------{datetime.now()}"
            )  # 항목을 구분하기 위한 구분선
        else:
            print(f"NONBODY message \n{dict_data}")


async def get_done():
    """
    주문에 대한 주간 시장 "선물옵션" 체결시 수신
    주문해도 메시지 수신
    취소해도 메시지 수신
    (OC0 ?  => 특정 옵션의 시장체결여부)
    """
    tr = "C01"
    ACCESS_TOKEN = auth.get_token_futures()
    header = {"token": ACCESS_TOKEN, "tr_type": "1"}
    body = {"tr_cd": tr, "tr_key": ""}
    # 두 딕셔너리를 하나로 결합
    combined_dict = {"header": header, "body": body}

    json_string = json.dumps(combined_dict)

    async with websockets.connect(
        "wss://openapi.ls-sec.co.kr:29443/websocket"
    ) as websocket:
        print("주간 선물옵션 체결 모니터링.. ")
        await websocket.send(json_string)
        try:
            # await message_handler(websocket)
            await asyncio.wait_for(message_handler(websocket), timeout=1000)
        except asyncio.TimeoutError:
            print("메시지 수신시간 초과, 연결을 종료합니다")


asyncio.run(get_done())
