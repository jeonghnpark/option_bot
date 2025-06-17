import json
from api_auth import auth
import websockets
import asyncio


# stop_signal = False
import logging

logger = logging.getLogger(__name__)


async def connect(shcode="105V3000", callback=None):
    """
    FCO 코스피200 선물 체결
    실시간 시장 체결 관찰
    주문거래의 체결 여부는 C01
    """
    tr = "FC0"
    ACCESS_TOKEN = auth.get_token_futures()

    # 웹 소켓에 접속을 합니다.
    print(f"FC0: shcode {shcode}")
    header = {"token": ACCESS_TOKEN, "tr_type": "3"}
    body = {"tr_cd": tr, "tr_key": shcode}
    js = json.dumps({"header": header, "body": body})

    try:
        async with websockets.connect(
            "wss://openapi.ls-sec.co.kr:29443/websocket"
        ) as websocket:
            # 웹 소켓 서버로 데이터를 전송합니다.
            await websocket.send(js)

            # 웹 소켓 서버로부터 메시지를 비동기적으로 받습니다.
            async for message in websocket:
                dict_data = json.loads(message)
                # body = dict_data["body"]
                # if body is not None:
                #     print(body)
                if callback is not None:
                    await asyncio.create_task(callback(dict_data))
                else:
                    print(dict_data)
    except asyncio.CancelledError:
        logger.info(f"{tr}  웹소켓 연결이 취소되었습니다.")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"{tr} 웹소켓 연결이 종료되었습니다.")


async def callback(dict_data):
    print(dict_data)


if __name__ == "__main__":
    shcode = "101VC000"
    asyncio.run(connect(shcode, callback))
