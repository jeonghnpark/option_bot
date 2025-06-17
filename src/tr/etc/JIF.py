# import os
# from dotenv import load_dotenv

# load_dotenv()
# APP_KEY = os.environ.get("EBEST-OPEN-API-APP-KEY-FUTURES-TEST")
# APP_SECRET = os.environ.get("EBEST-OPEN-API-SECRET-KEY-FUTURES-TEST")
import json
from api_auth import auth
import websockets
import asyncio

# ACCESS_TOKEN = auth.get_token()

# stop_signal = False


async def msghandler(websocket):
    async for message in websocket:
        dict_data = json.loads(message)
        body = dict_data["body"]
        if body is not None:
            print(body)


async def connect():
    # 웹 소켓에 접속을 합니다.
    tr = "JIF"
    ACCESS_TOKEN = auth.get_token_futures()
    header = {"token": ACCESS_TOKEN, "tr_type": "3"}
    body = {"tr_cd": tr, "tr_key": "1"}
    js = json.dumps({"header": header, "body": body})

    async with websockets.connect(
        "wss://openapi.ls-sec.co.kr:29443/websocket"
    ) as websocket:
        # 웹 소켓 서버로 데이터를 전송합니다.
        await websocket.send(js)
        await msghandler(websocket)

        # while not stop_signal:
        #     await websocket.send(js)

        #     # 웹 소켓 서버로 부터 메시지가 오면 콘솔에 출력합니다.
        #     data = await websocket.recv()
        #     dict_data = json.loads(data)
        #     body = dict_data["body"]
        #     if body is not None:
        #         print(body)


if __name__ == "__main__":
    asyncio.run(connect())
