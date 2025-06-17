import json
from api_auth import auth
import websockets
import asyncio
import sys
import os


async def connect():
    tr = "NWS"
    ACCESS_TOKEN = auth.get_token_futures()
    header = {"token": ACCESS_TOKEN, "tr_type": "3"}
    body = {"tr_cd": tr, "tr_key": "NWS001"}
    js = json.dumps({"header": header, "body": body})

    try:
        async with websockets.connect(
            "wss://openapi.ls-sec.co.kr:29443/websocket"
        ) as websocket:
            await websocket.send(js)

            async for message in websocket:
                dict_data = json.loads(message)
                body = dict_data["body"]
                if body is not None:
                    print(body)
    except asyncio.CancelledError:
        print("웹소켓 연결이 취소되었습니다.")
    except websockets.exceptions.ConnectionClosed:
        print("웹소켓 연결이 종료되었습니다.")
    finally:
        print("연결 종료 및 정리 작업 수행")


if __name__ == "__main__":
    try:
        asyncio.run(connect())
    except KeyboardInterrupt:
        print("프로그램이 강제 종료되었습니다.")
    finally:
        print("프로그램을 종료합니다.")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
