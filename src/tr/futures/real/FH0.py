import json
from api_auth import auth
import websockets
import asyncio

import logging

logger = logging.getLogger(__name__)


async def connect(shcode="105V3000", callback=None):
    """
    주간 선물 옵션 호가
    FH0 실시간 호가

    """
    tr = "FH0"
    ACCESS_TOKEN = auth.get_token_futures()

    # 웹 소켓에 접속을 합니다.
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

                if callback is not None:
                    await asyncio.create_task(callback(dict_data))
                else:
                    print(dict_data)

    except asyncio.CancelledError:
        logger.info(f"{tr} 실시간 호가 웹소켓 연결이 취소되었습니다.")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"{tr} 실시간 호가 웹소켓 연결이 종료되었습니다.")


if __name__ == "__main__":
    shcode = "101VC000"
    asyncio.run(connect(shcode))
