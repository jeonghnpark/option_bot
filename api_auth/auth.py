import time

import os
from dotenv import load_dotenv

load_dotenv()

import time

from datetime import datetime, timedelta

import requests
import aiohttp
import asyncio

import logging

logger = logging.getLogger(__name__)


APP_KEY = os.environ.get("EBEST-OPEN-API-APP-KEY")
APP_SECRET = os.environ.get("EBEST-OPEN-API-SECRET-KEY")
APP_FUTURES_KEY = os.getenv("EBEST-OPEN-API-APP-KEY-FUTURES")
APP_FUTURES_SECRET = os.getenv("EBEST-OPEN-API-SECRET-KEY-FUTURES")


APP_KEY_TEST = os.getenv("EBEST-OPEN-API-APP-KEY-TEST")
APP_SECRET_TEST = os.getenv("EBEST-OPEN-API-SECRET-KEY-TEST")

APP_FUTURES_KEY_TEST = os.getenv("EBEST-OPEN-API-APP-KEY-FUTURES-TEST")
APP_FUTURES_SECRET_TEST = os.getenv("EBEST-OPEN-API-SECRET-KEY-FUTURES-TEST")


cached_token = None
token_expiry = None

cached_token_futures = None
token_expiry_futures = None


# def get_token():
#     global cached_token, token_expiry
#     now = datetime.now()
#     if cached_token and token_expiry > now:
#         return cached_token

#     url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
#     values = ""
#     headers = {"content-type": "application/x-www-form-urlencoded"}
#     params = {
#         "appkey": APP_KEY_TEST,
#         "appsecretkey": APP_SECRET_TEST,
#         "grant_type": "client_credentials",
#         "scope": "oob",
#     }

#     requset = requests.post(url, data=params)
#     requset = requset.json()

#     new_token = requset["access_token"]
#     cached_token = new_token

#     expiry_in = requset["expires_in"]
#     token_expiry = now + timedelta(seconds=expiry_in)

#     return new_token


# def get_token_old():
#     url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
#     values = ""
#     headers = {"content-type": "application/x-www-form-urlencoded"}
#     params = {
#         "appkey": APP_KEY_TEST,
#         "appsecretkey": APP_SECRET_TEST,
#         "grant_type": "client_credentials",
#         "scope": "oob",
#     }

#     requset = requests.post(url, data=params)

#     requset = requset.json()
#     return requset["access_token"]


def get_token_futures():
    global cached_token_futures, token_expiry_futures
    now = datetime.now()
    if cached_token_futures and token_expiry_futures > now:
        return cached_token_futures

    url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
    values = ""
    headers = {"content-type": "application/x-www-form-urlencoded"}
    params = {
        "appkey": APP_FUTURES_KEY_TEST,
        "appsecretkey": APP_FUTURES_SECRET_TEST,
        "grant_type": "client_credentials",
        "scope": "oob",
    }

    requset = requests.post(url, data=params)
    requset = requset.json()

    new_token = requset["access_token"]
    cached_token_futures = new_token

    expiry_in = requset["expires_in"]
    token_expiry_futures = now + timedelta(seconds=expiry_in)

    return new_token


# async def get_token_futures_async():
#     global cached_token_futures, token_expiry_futures
#     now = datetime.now()
#     if cached_token_futures and token_expiry_futures > now:
#         return cached_token_futures

#     url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"
#     headers = {"content-type": "application/x-www-form-urlencoded"}
#     params = {
#         "appkey": APP_FUTURES_KEY_TEST,
#         "appsecretkey": APP_FUTURES_SECRET_TEST,
#         "grant_type": "client_credentials",
#         "scope": "oob",
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, data=params, headers=headers) as response:
#             request = await response.json()

#     new_token = request["access_token"]
#     cached_token_futures = new_token

#     expiry_in = request["expires_in"]
#     token_expiry_futures = now + timedelta(seconds=expiry_in)

#     return new_token


class ApiCallManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApiCallManager, cls).__new__(cls)
            cls._instance.last_call_time = {}
        return cls._instance

    def initialize(self):
        # 필요한 초기화 작업을 여기에 추가
        pass

    def wait_for_next_call(self, api_name, time_for_a_call):
        current_time = time.time()
        if api_name in self.last_call_time:
            elapsed_time = current_time - self.last_call_time[api_name]
            if elapsed_time < time_for_a_call:
                logger.debug(f"waiting for next api call {api_name}.... ")
                time.sleep(time_for_a_call - elapsed_time)
        self.last_call_time[api_name] = time.time()


api_manager = ApiCallManager()
