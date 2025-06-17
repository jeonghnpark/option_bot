# from dotenv import load_dotenv

# load_dotenv()
import json
from api_auth import auth
import websockets
import asyncio


async def connect(shcode="105V3000", callback=None):
    """
    야간 선물 옵션 호가
    """
    tr = "EH0"
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
            # print(f"EH0 웹소켓 연결 완료 {shcode}")

            # 웹 소켓 서버로부터 메시지를 비동기적으로 받습니다.
            async for message in websocket:
                dict_data = json.loads(message)
                if callback is not None:
                    await asyncio.create_task(callback(dict_data))
                else:
                    print(dict_data)

    except asyncio.CancelledError:
        print("웹소켓 연결이 취소되었습니다.")
    except websockets.exceptions.ConnectionClosed:
        print("웹소켓 연결이 종료되었습니다.")


async def message_handler(websocket):
    try:
        async for msg in websocket:
            dict_data = json.loads(msg)
            body = dict_data.get("body")
            header = dict_data.get("header")
            if body is not None:
                # print(
                #     body["bidho1"], body["bidrem1"], body["offerho1"], body["offerrem1"]
                # )
                print(body)
            # print("본문:")
            # print(json.dumps(body, indent=2, ensure_ascii=False))
            # print("헤더:")
            # print(json.dumps(header, indent=2, ensure_ascii=False))
    except websockets.exceptions.ConnectionClosed:
        print("websocket connection closed")


async def current_fut(shcode):
    """
    주어진 상품에 대한 야간 선물 옵션 호가 실시간
    """
    tr = "EH0"
    ACCESS_TOKEN = auth.get_token_futures()
    header = {"token": ACCESS_TOKEN, "tr_type": "3"}
    body = {"tr_cd": tr, "tr_key": shcode}

    combined_dict = {"header": header, "body": body}
    json_string = json.dumps(combined_dict)
    async with websockets.connect(
        "wss://openapi.ls-sec.co.kr:29443/websocket"
    ) as websocket:
        await websocket.send(json_string)
        await message_handler(websocket)
        # 10초 동안 웹소켓 연결 대기
        # try:
        #     await asyncio.wait_for(message_handler(websocket), timeout=10)
        # except asyncio.TimeoutError:
        #     print("WebSocket connection timed out after 10 seconds")
        # await websocket.close()


if __name__ == "__main__":

    asyncio.run(current_fut("101VC000"))
