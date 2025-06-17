from django.shortcuts import render
from django.core.cache import cache
import json
from django.utils import timezone
from django.shortcuts import get_object_or_404
import numpy as np
import pandas as pd

pd.set_option("display.max_rows", None)
from tr.stock.invest_info.t3521 import get_cd_rate
from tr.futures.market_data.t8435 import get_listed_future

from tr.futures.market_data.t2831 import (
    get_current_orderbook as get_current_orderbook_eurex,
    get_current_orderbook_async as get_current_orderbook_eurex_async,
)
from tr.futures.market_data.t2105 import (
    get_current_orderbook as get_current_orderbook,
    get_current_orderbook_async as get_current_orderbook_async,
)
from src.tr.futures.chart.t2832 import get_eurex_time_tick
from src.tr.futures.chart.t2201 import get_hist_chetime

from src.tr.futures.real.FC0 import connect as fc0_connect
from src.tr.futures.real.EC0 import connect as ec0_connect


from src.tr.futures.real.EH0 import connect as connect_eurex
from src.tr.futures.real.FH0 import connect as connect_futures

from tr.futures.chart.t8415 import get_hist_fut
from tr.futures.chart.t8429 import get_eurex_ntick
from trading.jobs import calcVol
from datetime import datetime, timedelta, time
from django.http import JsonResponse
from django.http import StreamingHttpResponse

import asyncio
from api_auth import auth
import httpx
import websockets
import uuid

from .models import Portfolio, Trade
from .order_manager import Order, OrderManager
from trading.models import VolatilityData
from order.background_tasks import BackgroundTaskManager

import logging

logger = logging.getLogger(__name__)


def index(request):
    logger.info("Order index page accessed")
    return render(request, "order/index.html")  # order/templates/생략


def portfolio_list(request):
    logger.info("portfolio_list: load template")

    return render(request, "order/portfolio_list.html")


def portfolio_detail(request, portfolio_id):
    logger.info(f"Accessing portfolio detail for id: {portfolio_id}")
    portfolio = get_object_or_404(Portfolio, portfolio_id=portfolio_id)
    trades = portfolio.trades.all().order_by("-timestamp")
    logger.debug(f"Portfolio {portfolio.portfolio_id} has {trades.count()} trades")
    return render(
        request,
        "order/portfolio_detail.html",
        context={"portfolio": portfolio, "trades": trades},
    )


async def place_order(order: Order):
    logger.info(f"Placing order: {order.focode} {order.direction} {order.quantity} ")
    headers, body = make_order(order)
    api_url_order = "https://openapi.ls-sec.co.kr:8080/futureoption/order"
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url_order, json=body, headers=headers)
        order_id = None
        if response.status_code == 200:
            data = response.json()
            for key in data:
                if isinstance(data[key], dict) and "OrdNo" in data[key]:
                    order_id = data[key]["OrdNo"]
                    break
            logger.info(f"Order response~: {data['rsp_msg']} order id: {order_id} ")
        else:
            logger.error(f"Order placement failed: {response.text}")
        if not order.order_id_future.done():
            order.order_id_future.set_result(order_id)
        return order_id


def generate_portfolio_id():
    date_str = datetime.now().strftime("%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # UUID의 첫 8자리만 사용

    return f"p{date_str}_{unique_id}"


async def save_portfolio(execution_info, portfolio_id, target_profit, strategy):
    logger.info(f"Saving portfolio with ID: {portfolio_id}")
    try:
        try:
            portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
            created = False
        except Portfolio.DoesNotExist:
            portfolio = await Portfolio.objects.acreate(
                portfolio_id=portfolio_id,
                timestamp=timezone.now(),
                status="Active",
                target_profit=target_profit,
                strategy=strategy,  # 새로운 필드 추가
            )
            created = True

        if created:
            logger.info(f"New Portfolio {portfolio} was created")

        else:
            logger.info(f"Existing Portfolio {portfolio} was retrieved")

        logger.info(f"target_profit: {target_profit}")

        # 포트폴리오의 전체 내용을 로깅
        logger.info(f"포트폴리오 전체 내용:")
        logger.info(f"  ID: {portfolio.portfolio_id}")
        logger.info(f"  타임스탬프: {portfolio.timestamp}")
        logger.info(f"  상태: {portfolio.status}")
        logger.info(f"  목표 수익: {portfolio.target_profit}")
        logger.info(f"  전략: {portfolio.strategy}")  # 새로운 필드 추가

        for trade_data in execution_info:
            logger.debug(f"Saving trade data: {trade_data}")

            trade = await Trade.objects.acreate(
                portfolio=portfolio,
                order_id=trade_data["order_id"],
                focode=trade_data["focode"],
                price=trade_data["price"],
                volume=trade_data["volume"],
                multiplier=trade_data["multiplier"],
                direction=trade_data["direction"],
                description=trade_data["description"],
            )

            logger.debug(f"Trade {trade} was saved")

        # 포트폴리오에 연결된 모든 거래 정보 로깅
        async for trade in portfolio.trades.all():
            logger.info(f"  거래 정보:")
            logger.info(f"    주문 ID: {trade.order_id}")
            logger.info(f"    상품 코드: {trade.focode}")
            logger.info(f"    가격: {trade.price}")
            logger.info(f"    수량: {trade.volume}")
            logger.info(f"    승수: {trade.multiplier}")
            logger.info(f"    방향: {trade.direction}")

        return True
    except Exception as e:
        logger.error(f"Error saving portfolio {portfolio_id}: {str(e)}")
        return False


def make_cancel_request(order: Order):

    api_url = "https://openapi.ls-sec.co.kr:8080/futureoption/order"
    api_token = auth.get_token_futures()

    if datetime.now().hour >= 16 or datetime.now().hour < 5:
        tr = "CEXAT11300"
    else:
        tr = "CFOAT00300"

    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {api_token}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    body = {
        f"{tr}InBlock1": {
            "FnoIsuNo": order.focode,
            "OrgOrdNo": order.order_id,
            # "CancQty": None, #주간에도 먹히는지 확인
        }
    }

    return api_url, headers, body


def make_order(order: Order):

    api_token = auth.get_token_futures()
    if datetime.now().hour >= 16 or datetime.now().hour < 5:
        tr = "CEXAT11100"
        ordertype_map = {"limit": "2", "market": "1"}
    else:
        tr = "CFOAT00100"
        ordertype_map = {"limit": "00", "market": "03"}

    direction_map = {"buy": "2", "sell": "1"}
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {api_token}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    focode = order.focode
    quantity = order.quantity
    direction = order.direction
    ordertype = order.order_type
    price = order.price

    if datetime.now().hour >= 16 or datetime.now().hour < 5:
        body = {
            f"{tr}InBlock1": {
                "FnoIsuNo": focode,
                "BnsTpCode": direction_map.get(direction),  # 1@매도2@매수
                "ErxPrcCndiTpCode": ordertype_map.get(
                    ordertype
                ),  # "2"@지정가 "1"@시장가
                "OrdPrc": price,
                "OrdQty": quantity,
            }
        }

    else:
        body = {
            f"{tr}InBlock1": {
                "FnoIsuNo": focode,
                "BnsTpCode": direction_map.get(direction),  # 1@매도2@매수
                "FnoOrdprcPtnCode": ordertype_map.get(
                    ordertype
                ),  # 00@지정가03@시장가05@조건부지정가06@최유리지정가
                "FnoOrdPrc": price,
                "OrdQty": quantity,
            }
        }

    return headers, body


def make_order_request(request):

    api_token = auth.get_token_futures()
    if datetime.now().hour >= 16 or datetime.now().hour < 5:
        tr = "CEXAT11100"
        ordertype_map = {"limit": "2", "market": "1"}
    else:
        tr = "CFOAT00100"
        ordertype_map = {"limit": "00", "market": "03"}

    direction_map = {"buy": "2", "sell": "1"}
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {api_token}",
        "tr_cd": tr,
        "tr_cont": "N",
        "tr_cont_key": "",
    }

    data = json.loads(request.body)
    # print(data)

    focode = data["focode"]
    direction = data["direction"]
    ordertype = data["orderType"]
    price = float(data["price"]) if data["price"] else 0
    quantity = int(data["quantity"])

    if datetime.now().hour >= 16 or datetime.now().hour < 5:
        body = {
            f"{tr}InBlock1": {
                "FnoIsuNo": focode,
                "BnsTpCode": direction_map.get(direction),  # 1@매도2@매수
                "ErxPrcCndiTpCode": ordertype_map.get(
                    ordertype
                ),  # "2"@지정가 "1"@시장가
                "OrdPrc": price,
                "OrdQty": quantity,
            }
        }

    else:
        body = {
            f"{tr}InBlock1": {
                "FnoIsuNo": focode,
                "BnsTpCode": direction_map.get(direction),  # 1@매도2@매수
                "FnoOrdprcPtnCode": ordertype_map.get(
                    ordertype
                ),  # 00@지정가03@시장가05@조건부지정가06@최유리지정가
                "FnoOrdPrc": price,
                "OrdQty": quantity,
            }
        }

    return headers, body


async def cancel_order(order: Order):
    logger.info(f"Cancelling order: {order.focode} {order.direction} {order.order_id}")
    api_url, headers, body = make_cancel_request(order)

    async with httpx.AsyncClient() as client:

        response = await client.post(api_url, json=body, headers=headers)

        if response.status_code == 200:
            logger.info("Order cancellation request sent")
            cancel_result = response.json()
            return cancel_result
            # print(response.json())
        else:
            logger.error(f"Order cancellation request failed: {response.text}")
            return None


async def on_executed_and_save(websocket, order):
    logger.info(
        f"Monitoring execution for order: {order.focode} {order.direction} {order.quantity} "
    )
    accumulated_volume = 0
    remaining_volume = order.quantity  # 초기값 설정
    order_cancelled = False
    cancel_completed_event = asyncio.Event()
    execution_info = []

    bnstp = (
        "bnstp" if datetime.now().hour >= 16 or datetime.now().hour < 5 else "dosugb"
    )
    che_fld = (
        "execqty" if datetime.now().hour >= 16 or datetime.now().hour < 5 else "chevol"
    )
    che_prc = (
        "execprc"
        if datetime.now().hour >= 16 or datetime.now().hour < 5
        else "cheprice"
    )

    async def cancel_order_after_timeout():
        nonlocal order_cancelled, accumulated_volume, remaining_volume  # remaining_volume을 nonlocal로 선언

        for sec in range(50):
            await asyncio.sleep(1)
            if (sec + 1) % 5 == 0:
                logger.info(f"Order wait: {sec + 1} seconds elapsed")

        if accumulated_volume < order.quantity:
            logger.info("Initiating order cancellation due to timeout")
            if not order.order_id_future.done():
                order.order_id = await order.order_id_future

            order.order_id = order.order_id_future.result()

            await cancel_order(order)

            try:
                await asyncio.wait_for(cancel_completed_event.wait(), timeout=10.0)
                order_cancelled = True
                remaining_volume = order.quantity - accumulated_volume
                total_accumulated_volume = accumulated_volume
                print(
                    f"주문 취소됨. 총누적/이번누적 {total_accumulated_volume}/{accumulated_volume} 미체결 잔량: {remaining_volume}"
                )
                await websocket.close()
            except asyncio.TimeoutError:
                print("asyncio.TimeoutError: cancel주문 처리 안됨 ")
                if not websocket.closed:
                    print(f"웹소캣 열려있어서 닫는중..")
                    await websocket.close()

    cancel_task = asyncio.create_task(cancel_order_after_timeout())

    order.message_ready_event.set()

    try:
        async for message in websocket:
            dict_data = json.loads(message)
            logger.debug(f"Received message: {message}")
            body = dict_data["body"]
            header = dict_data["header"]

            if not order.order_id_future.done():
                order.message_ready_event.set()
                try:
                    order_id = await asyncio.wait_for(
                        order.order_id_future, timeout=5.0
                    )
                    order_id_str = (
                        str(order_id).zfill(10)
                        if datetime.now().hour < 16 and datetime.now().hour >= 5
                        else str(order_id)
                    )
                except asyncio.TimeoutError:
                    print("주문 ID를 받지 못했습니다. 계속 대기합니다.")

                if order_id is None:
                    logger.info(f"in CO1,   order_id is acknowledged as {None}")
                    cancel_task.cancel()
                    if not websocket.closed:
                        logger.info(f"close websocket since order has no id")
                        await websocket.close()

            if body and che_fld in body and int(body[che_fld]) > 0:
                chevol = 0

                if body.get("ordno") == order_id_str:
                    chevol = int(body[che_fld])
                    cheprice = float(body[che_prc])
                    dosugb = body[bnstp]
                    accumulated_volume += chevol
                    execution_info.append(
                        {
                            "order_id": order.order_id,
                            "focode": order.focode,
                            "price": cheprice,
                            "volume": chevol,
                            "multiplier": (
                                250000
                                if order.focode[:3] in ["301", "201", "101"]
                                else 50000 if order.focode[:3] == "105" else 0
                            ),
                            "direction": (
                                "sell"
                                if dosugb == "1"
                                else "buy" if dosugb == "2" else "unknown"
                            ),
                            "description": order.description,
                        }
                    )

                    remaining_volume = order.quantity - accumulated_volume

                    print(
                        f"^^체결: {chevol} 이번누적: {accumulated_volume}  미체결 잔량: {remaining_volume}"
                    )
                else:
                    print("chevol은 들어왔으나 id가 다르다. 다른 수동주문이 있는지??")
                    print(f"{body.get('ordno')} vs {order_id_str}")

                if accumulated_volume >= order.quantity:
                    print(f"목표도달.연결종료!")
                    await websocket.close()
                    break
            elif body:  # body가 있는 비체결 수신(취소 등)
                # print(f"비체결 메시지 수신-------{datetime.now()}")
                if body and "trcode" in body and body["trcode"] == "TTRODP11301":
                    if int(body["qty"]) > 0:
                        cancel_completed_event.set()
                        print(
                            f"주간시장 취소완료 메시지 수신 취소수량{body['qty']} -------{datetime.now()}"
                        )

                if body and "trcode" in body and body["trcode"] == "CONET801":  # 야간
                    if int(body["mrccnfqty"]) > 0:
                        cancel_completed_event.set()
                        print(
                            f"야간시장 취소완료 메시지 수신 취소수량{body['mrccnfqty']} -------{datetime.now()}"
                        )

    except websockets.exceptions.ConnectionClosed:
        logger.warning("WebSocket connection closed")
    finally:
        logger.info("Cleaning up after order execution")
        cancel_task.cancel()
        if not websocket.closed:
            await websocket.close()
    order_status = (
        "completed"
        if accumulated_volume == order.quantity
        else "partially_filled" if accumulated_volume > 0 else "cancelled"
    )
    return order_status, accumulated_volume, remaining_volume, execution_info


async def manual_liquidate_portfolio(
    request, portfolio_id, description="Closed from manual liquidation"
):
    logger.info(f"Liquidating portfolio: {portfolio_id}")
    try:
        result = await liquidate_portfolio(portfolio_id, description)

        response_data = {
            "status": "success" if result["all_completed"] else "partial",
            "message": result["message"],
            "result": {
                "portfolio_id": result["portfolio_id"],
                "results_orders": result["results_orders"],
            },
        }
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error during portfolio liquidation: {str(e)}")
        return JsonResponse(
            {
                "status": "error",
                "message": "포트폴리오 청산 중 오류가 발생했습니다.",
                "error": str(e),
            },
            status=500,
        )


async def liquidate_portfolio(
    portfolio_id, description="Closed from manual liquidation"
):
    portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
    order_manager = OrderManager(
        order_category="liquidate_completed_orders", portfolio_id=portfolio_id
    )
    async for trade in portfolio.trades.all():
        order = {
            "focode": trade.focode,
            "quantity": trade.volume,
            "direction": "sell" if trade.direction == "buy" else "buy",
            "order_type": "market",
            "price": None,
            "description": description,
        }

        order_manager.add_order(Order(**order))
        logger.info(
            f"Added order to manager: {order['focode']} {order['direction']} in port {portfolio_id}"
        )

    results_orders, portfolio_id = await place_orders(order_manager)

    # 마감여부 확인
    market_closed = any(
        result.get("order_id") is None
        and result.get("status") == "cancelled"
        and result.get("quantity") == 0
        for result in results_orders
    )

    if market_closed:
        logger.info("시장 마감인 것같다. 청산이 실행되지 못함")
        return {
            "all_completed": False,
            "message": "시장 마감으로 인해 청산이 실행되지 못했습니다. 장 운영 시간에 다시 시도해주세요.",
            "portfolio_id": portfolio_id,
            "results_orders": results_orders,
        }
    # 청산 결과 확인 및 저장
    all_completed = all(result["status"] == "completed" for result in results_orders)

    if all_completed:
        # portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
        # all_unique_codes = await Portfolio.aget_all_unique_codes()
        # current_prices = await Portfolio.aget_current_prices(all_unique_codes)

        # 최종 손익 계산 및 저장
        final_pnl = await portfolio.acalculate_final_pnl()
        portfolio.pnl = final_pnl
        portfolio.status = "Closed"
        portfolio.description = description
    else:
        portfolio.status = "Pending"
        portfolio.description = "Pending by incompleted trades"

    await portfolio.asave()
    logger.info(f"청산결과: {results_orders}")

    return {
        "all_completed": all_completed,
        "message": (
            "포트폴리오가 완전히 청산되었습니다."
            if all_completed
            else "포트폴리오가 부분적으로 청산되었습니다."
        ),
        "portfolio_id": portfolio_id,
        "results_orders": results_orders,
    }


async def place_orders(order_manager: OrderManager):
    """
    비동기적으로 주문을 처리하고 결과를 반환하는 함수입니다.

    이 함수는 OrderManager 객체에 저장된 주문들을 순차적으로 처리합니다.
    각 주문에 대해 웹소켓 연결을 설정하고, 주문을 실행한 후 모니터링합니다.
    주문 처리 결과와 실행 정보를 수집하여 반환합니다.

    Args:
        order_manager (OrderManager): 처리할 주문들이 포함된 OrderManager 객체

    Returns:
        tuple: (results_orders, portfolio_id)
            - results_orders (list): 각 주문의 처리 결과를 포함하는 딕셔너리 리스트
            - portfolio_id (str): 처리된 주문들과 관련된 포트폴리오 ID

    Raises:
        Exception: 주문 처리 중 발생한 예외는 로깅되고 결과에 포함됩니다.

    Note:
        - 연속 거래에서 주문 실패시 후속 거래 주문은 중단됩니다.
        - 모든 실행 정보는 데이터베이스에 저장됩니다.
    """
    results_orders = []
    all_execution_info = []

    for order in order_manager.get_pending_orders():
        try:
            logger.info(f"Processing order: {order.focode} {order.direction}")
            order.order_id_future = asyncio.Future()
            order.websocket_open_event = asyncio.Event()
            order.message_ready_event = asyncio.Event()

            monitor_task = asyncio.create_task(monitor_order(order))

            await order.websocket_open_event.wait()
            await order.message_ready_event.wait()

            order_id = await place_order(order)
            order.order_id = order_id

            order_status, executed_volume, remaining, execution_info = (
                await monitor_task
            )
            order_manager.update_order_status(order.order_id, order_status)

            results_orders.append(
                {
                    "order_id": order.order_id,
                    "quantity": executed_volume,
                    "status": order_status,
                    "remaining": remaining,
                }
            )

            # excecution_info는 여러개의 체결건들로 이루어진 list임
            all_execution_info.extend(execution_info)

            # 연속거래에서 주문 실패시 후속 거래 주문 중단
            if order_status != "completed":
                break

        except Exception as e:
            logger.error(f"Error processing order: {str(e)}")
            results_orders.append(
                {"order_id": None, "status": "failed", "error": str(e)}
            )

    if all_execution_info:
        await save_portfolio(
            all_execution_info,
            order_manager.portfolio_id,
            order_manager.target_profit,
            order_manager.strategy,
        )

    return results_orders, order_manager.portfolio_id


def set_vol_threshold(request):
    if request.method == "POST":
        # logger.info("Initialization request received")

        data = json.loads(request.body)
        fut_code = data.get("fut_code")
        maturity = data.get("maturity")

        cd_rate = get_cd_rate().get("close")

        result, theta_vega_ratio = calcVol(fut_code, maturity, float(cd_rate) / 100.0)

        return JsonResponse({"cd_rate": cd_rate, "theta_vega_ratio": theta_vega_ratio})


async def fetchPortfolios_async(request):
    portfolios_data = []
    all_unique_codes = await Portfolio.aget_all_unique_codes()
    current_prices = await Portfolio.aget_current_prices(all_unique_codes)
    portfolios = Portfolio.objects.all().order_by("-timestamp").aiterator()

    # async for portfolio in Portfolio.objects.filter(
    #     status__in=["Active", "Pending"]
    # ):
    async for portfolio in portfolios:  # TODO closed된 port는 계산할 x

        pnl = await portfolio.acalculate_pnl(current_prices)
        portfolio.pnl = pnl
        await portfolio.asave()
        portfolio_dict = await portfolio.ato_dict()
        portfolios_data.append(portfolio_dict)

    # today total pnl 계산하기(closed, active, pending 모두)
    today = timezone.now().date()
    today_portfolios = []
    async for portfolio in Portfolio.objects.filter(timestamp__date=today):
        today_portfolios.append(portfolio)

    # today_portfolios = [p for p in portfolios if p.timestamp.date() == today]

    strategy_pnl = {}
    for portfolio in today_portfolios:
        if portfolio.strategy not in strategy_pnl:
            strategy_pnl[portfolio.strategy] = 0
        strategy_pnl[portfolio.strategy] += portfolio.pnl

    total_pnl = sum(strategy_pnl.values())

    return JsonResponse(
        {
            "portfolios": portfolios_data,
            "total_pnl_today": total_pnl,
            "strategy_pnl": strategy_pnl,
        }
    )


def portfolio_detail(request, portfolio_id):
    logger.info(f"Accessing portfolio detail for id: {portfolio_id}")
    portfolio = get_object_or_404(Portfolio, portfolio_id=portfolio_id)
    trades = portfolio.trades.all().order_by("-timestamp")
    logger.debug(f"Portfolio {portfolio.portfolio_id} has {trades.count()} trades")
    return render(
        request,
        "order/portfolio_detail.html",
        context={"portfolio": portfolio, "trades": trades},
    )


def generate_portfolio_id():
    date_str = datetime.now().strftime("%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # UUID의 첫 8자리만 사용

    return f"p{date_str}_{unique_id}"


async def request_execution_info(websocket):
    # api_key = await auth.get_token_futures_async()
    api_key = auth.get_token_futures()

    header = {"token": api_key, "tr_type": "1"}
    if datetime.now().hour >= 16 or datetime.now().hour < 5:
        tr = "EU1"
    else:
        tr = "C01"

    body = {"tr_cd": tr, "tr_key": ""}
    await websocket.send(json.dumps({"header": header, "body": body}))


async def monitor_order(order: Order):
    """
    하나의 주문을 모니터링하고 실행 정보를 수집하는 비동기 함수입니다.
    이 함수는 WebSocket 연결을 통해 주문의 실행 상태를 모니터링하고,
    주문이 완료되거나 부분 체결되거나 취소될 때까지 실행 정보를 수집합니다.
    주문 상태는 실시간으로 모니터링되며, 필요한 경우 취소 작업도 수행됩니다.

    매개변수:
    order (Order): 모니터링할 주문 객체

    반환값:
    tuple: (order_status, executed_volume, remaining, execution_info)
        - order_status (str): 주문의 최종 상태 ('completed', 'partially_filled', 'cancelled')
        - executed_volume (int): 실제로 체결된 주문량
        - remaining (int): 남은 미체결 주문량
        - execution_info (list): 주문 실행에 대한 상세 정보 리스트

    예외:
    - WebSocket 연결 실패 시 로그에 오류를 기록하고 False를 반환합니다.

    참고:
    - WebSocket 연결은 함수 실행 중에 열리고 닫힙니다.

    """

    async with websockets.connect(
        "wss://openapi.ls-sec.co.kr:29443/websocket", ping_interval=None
    ) as websocket:
        if not websocket.closed:
            # logger.info(f"websocket is open")
            # logger.info(f"django version {django.get_version()}")
            # logger.info(f"python version {sys.version}")
            await request_execution_info(websocket)
            order.websocket_open_event.set()
            # logger.info("WebSocket opened and execution info requested")
        else:
            logger.error("Failed to open WebSocket connection")
            return False, order.quantity, []

        order_status, executed_volume, remaining, execution_info = (
            await on_executed_and_save(websocket, order)
        )
    logger.info(
        f"Order monitoring completed. Status: {order_status}, Remaining: {remaining}, Execution Info: {execution_info}"
    )
    return order_status, executed_volume, remaining, execution_info


async def manual_order(request):
    """
    수동 주문을 처리하는 비동기 함수입니다.
    이 함수는 클라이언트로부터 받은 주문 데이터를 처리하고, 주문을 실행한 후 결과를 반환합니다.
    새로운 포트폴리오 생성 또는 기존 포트폴리오에 주문 추가를 처리합니다.
    주문 실패 시 미체결 주문에 대한 정리 작업도 수행합니다.

    Args:
        request (HttpRequest): 클라이언트의 요청 객체. 주문 데이터를 포함합니다.
    Returns:
        JsonResponse: 주문 처리 결과를 포함한 JSON 응답.
            성공 시: 주문 결과와 포트폴리오 ID를 포함.
            실패 시: 에러 메시지를 포함.
    Raises:
        JsonResponse: 주문 데이터가 없는 경우 400 상태 코드와 함께 에러 메시지 반환.
    Note:
        - 이 함수는 비동기로 실행되며, 여러 주문을 동시에 처리할 수 있습니다.
        - 주문 카테고리에 따라 새 포트폴리오 생성 여부가 결정됩니다.
        - 미체결 주문에 대해서는 자동으로 정리 작업을 수행합니다.
    """
    logger.info("Processing multi-order request")
    data = json.loads(request.body)
    orders = data.get("orders", [])
    liquidation_condition = data.get("liquidation_condition")
    liquidation_value_str = data.get("liquidation_value")
    liquidation_value = (
        int(liquidation_value_str)
        if liquidation_value_str and liquidation_value_str.strip()
        else 0
    )

    target_profit = None
    liquidation_time_in_second = None

    if liquidation_condition == "pl":
        target_profit = liquidation_value
    elif liquidation_condition == "time":
        liquidation_time_in_second = liquidation_value

    print(
        f"!!!!liquidation_condition {liquidation_condition} {type(liquidation_condition)} liquidation_value {liquidation_value} {type(liquidation_value)}"
    )

    if not orders:
        logger.warning("No orders provided in multi-order request")
        return JsonResponse({"error": "No orders provided"}, status=400)

    order_manager = OrderManager(
        order_category="new",
        portfolio_id=generate_portfolio_id(),
        strategy="manual_order",
        target_profit=target_profit,
    )

    for order_item in orders:
        order = Order(
            focode=order_item["focode"],
            quantity=int(order_item["quantity"]),
            direction=order_item["direction"],
            order_type=order_item["order_type"],
            status="pending",
            price=(
                float(order_item["order_price"]) if order_item["order_price"] else None
            ),
        )
        order_manager.add_order(order)
        logger.info(f"Added order to manager: {order.focode} {order.direction}")

    results, portfolio_id = await place_orders(order_manager)

    print(f"results manual order {results}")
    # 청산 결과 확인 및 저장
    all_completed = all(result["status"] == "completed" for result in results)

    # 정상 처리
    if all_completed:
        portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
        portfolio.status = "Active"
        portfolio.description = "수동 주문 진행 중"
        print(f"portfolio.liquidation_conditionn to save {liquidation_condition}")
        portfolio.liquidation_condition = liquidation_condition
        portfolio.liquidation_value = liquidation_value
        portfolio.target_profit = target_profit
        portfolio.liquidation_time_in_second = liquidation_time_in_second

        await portfolio.asave()

        logger.info("수동 주문 처리 완료")

        return JsonResponse(
            {
                "results": results,
                "portfolio_id": portfolio_id,
            }
        )

    elif any(
        result["status"] in ["completed", "partially_filled"] for result in results
    ):
        logger.info(f"not all completed")
        reverse_orders = make_reverse_order(order_manager)
        if reverse_orders:
            clear_order_manager = OrderManager(
                order_category="clear_incompleted", portfolio_id=portfolio_id
            )

            for order_item in reverse_orders:
                clear_order = Order(
                    focode=order_item["focode"],
                    quantity=int(order_item["quantity"]),
                    direction=order_item["direction"],
                    order_type=order_item["order_type"],
                    price=order_item["order_price"],
                )
                clear_order_manager.add_order(clear_order)

            clear_results, _ = await place_orders(clear_order_manager)

            reverse_orders_completed = all(
                result["status"] == "completed" for result in clear_results
            )
            portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
            portfolio.status = "Closed" if reverse_orders_completed else "Pending"
            portfolio.description = (
                "Closed becaused of incompleted trades"
                if reverse_orders_completed
                else "Pending by incompleted trades. Take manual action!"
            )
            portfolio.liquidation_condition = None
            portfolio.liquidation_value = None
            await portfolio.asave()

            results.extend(clear_results)

            return JsonResponse(
                {
                    "results": results,
                    "portfolio_id": portfolio_id,
                }
            )
    else:
        return JsonResponse(
            {
                "results": results,
                "portfolio_id": portfolio_id,
            }
        )


def make_reverse_order(order_manager):
    liquidation_orders = []
    if (
        order_manager.get_cancelled_orders()
        or order_manager.get_partially_filled_orders()
    ):
        completed_orders = order_manager.get_completed_orders()
        partially_filled_orders = order_manager.get_partially_filled_orders()

        for order in completed_orders + partially_filled_orders:
            liquidation_orders.append(
                {
                    "focode": order.focode,
                    "quantity": order.quantity,
                    "direction": "sell" if order.direction == "buy" else "buy",
                    "order_type": "market",
                    "order_price": None,
                    "portfolio_id": order_manager.portfolio_id,
                }
            )
    return liquidation_orders


async def get_price(request):
    logger.info("Fetching current price")
    data = json.loads(request.body)
    fut_code = data.get("fut_code")
    orderbook_data = await fetch_orderbook_data(fut_code)
    if orderbook_data:
        logger.debug(f"Orderbook data fetched: {orderbook_data}")
        return JsonResponse({"orderbook_data": orderbook_data})
    else:
        logger.error(f"Failed to fetch orderbook data for {fut_code}")
        return JsonResponse({"error": "fail to get prices"}, status=400)


async def fetch_orderbook_data(fut_code):
    current_time = datetime.now()
    if current_time.hour >= 18 or current_time.hour < 6:
        return await get_current_orderbook_eurex_async(fut_code)
    elif current_time.hour >= 8:
        return await get_current_orderbook_async(fut_code)
    return None


async def get_historical_data(shcode, current_datetime, end_date):
    if (
        current_datetime.hour >= 9
        or (current_datetime.hour == 8 and current_datetime.minute > 45)
    ) and (current_datetime.hour < 17):
        return get_hist_fut(shcode, 1, end_date, end_date)
    else:
        return get_eurex_ntick(shcode, "B", 1, 999)


def process_historical_data(fut_data):
    df_fut_data = pd.DataFrame(fut_data)
    df_fut_data["date_time"] = pd.to_datetime(
        df_fut_data["date"].astype(str) + " " + df_fut_data["time"].astype(str),
        format="%Y%m%d %H%M%S",
    )
    df_fut_data.drop(["date", "time"], axis=1, inplace=True)
    df_fut_data.sort_values(by="date_time", inplace=True)
    df_fut_data[["close", "high", "low"]] = df_fut_data[
        ["close", "high", "low"]
    ].astype(float)
    return df_fut_data


async def monitor_real_time_quotes_flex(
    strategy_type, shcode, lb_price, ub_price, min_price, max_price, duration
):
    """
    실시간 호가를 모니터링하고 전략 유형에 따라 조건 충족 여부를 확인하는 비동기 함수

    Args:
        strategy_type (str): 전략 유형 ('buydip', 'buypeak', 'sellpeak')
        shcode (str): 상품 코드
        threshold_price (float): 임계값 가격
        min_price (float): 최소 가격
        max_price (float): 최대 가격
        duration (int): 모니터링 지속 시간(초)

    Returns:
        tuple: (condition_met, bid_price, ask_price)
    """
    condition_met = False
    condition_event = asyncio.Event()
    bid_price = None
    ask_price = None
    log_counter = 0

    async def price_update_callback(dict_data):
        nonlocal condition_met, bid_price, ask_price, log_counter
        if dict_data.get("body") is not None:
            price_data = dict_data.get("body")
            bid_price = float(price_data["bidho1"])
            ask_price = float(price_data["offerho1"])

            # 전략 유형에 따른 조건 확인
            # if strategy_type in ["buydip", "selldip"]:
            #     condition = (ask_price < threshold_price) and (buffer_price < bid_price)
            #     logger.info(
            #         f"{strategy_type}:매도호가 {ask_price} < 임계값 {threshold_price} and buffer {buffer_price} < 매수호가 {bid_price}? {condition}"
            #     )
            # elif strategy_type in ["buypeak", "sellpeak"]:
            #     condition = (ask_price < buffer_price) and (threshold_price < bid_price)
            #     logger.info(
            #         f"{strategy_type} 매도호가 {ask_price} < buffer_price {buffer_price} and 임계값 {threshold_price} < 매수호가 {bid_price}? {condition}"
            #     )
            # else:
            #     condition = False
            #     logger.error(f"알 수 없는 전략 유형: {strategy_type}")

            condition = (ask_price < ub_price) and (lb_price < bid_price)
            logger.info(
                f"{strategy_type}: min {min_price} <LB {lb_price:.3f} <bid {bid_price} <ask {ask_price} <UB {ub_price:.3f} <max {max_price} : {condition}"
            )
            log_counter += 1

            if condition:
                condition_met = True
                condition_event.set()
        else:
            tr = dict_data.get("header").get("tr_cd")
            logger.info(f"가격 모니터링 준비 완료: {tr}")

    # 주간/야간 시장에 따른 웹소켓 연결
    current_time = datetime.now()
    if current_time.hour >= 18 or current_time.hour < 6:
        websocket_task = asyncio.create_task(
            connect_eurex(shcode, price_update_callback)
        )
    else:
        websocket_task = asyncio.create_task(
            connect_futures(shcode, price_update_callback)
        )

    try:
        await asyncio.wait_for(condition_event.wait(), timeout=duration)
    except asyncio.TimeoutError:
        logger.info("모니터링 시간 초과")
    finally:
        websocket_task.cancel()

    return condition_met, bid_price, ask_price


async def start_flexswitch_strategy(request):
    try:
        data = json.loads(request.body)
        action = data.get("action")
        strategy_type = data.get("strategy_type")

        if action == "start":
            params = {
                "shcode": data.get("shcode"),
                "period": data.get("period"),
                "threshold": data.get("threshold"),
                "buffer": data.get("buffer"),
                "liquidation_delay": data.get("liquidation_delay"),
                "monitoring_duration": data.get("monitoring_duration"),
                "interval": data.get("interval"),
                "strategy_type": strategy_type,
                "min_max_interval": data.get("min_max_interval"),
            }

            result = await BackgroundTaskManager.start_flexswitch_task(params)
            return JsonResponse(result)

        elif action == "stop":
            result = BackgroundTaskManager.stop_flexswitch_task(strategy_type)
            return JsonResponse(result)

        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid action. Expected 'start' or 'stop'.",
            },
            status=400,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON format in request body"},
            status=400,
        )
    except Exception as e:
        logger.error(f"Error in start_flexswitch_strategy: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


async def auto_liquidation_internal():
    logger.info(f"자동청산 실행 -{datetime.now()}")

    liquidation_results = []
    all_unique_codes = set()
    # all_unique_codes = await Portfolio.aget_all_unique_codes()
    # current_prices = await Portfolio.aget_current_prices(all_unique_codes)

    # Active나 Pending 상태의 포트폴리오만 필터링
    # active_portfolios = await Portfolio.objects.filter(
    #     status__in=["Active", "Pending"]
    # ).aiterator()
    # 필터링된 포트폴리오에서 직접 unique codes 조회
    async for portfolio in Portfolio.objects.filter(status__in=["Active", "Pending"]):
        portfolio_codes = await portfolio.aget_unique_focode()
        all_unique_codes.update(portfolio_codes)

    if not all_unique_codes:
        return JsonResponse({"result": {"message": "청산할 포트폴리오가 없습니다."}})

    current_prices = await Portfolio.aget_current_prices(list(all_unique_codes))
    logger.info(f"모든 고유 코드: {all_unique_codes}")
    result = {}
    async for portfolio in Portfolio.objects.filter(status__in=["Active", "Pending"]):
        if portfolio.liquidation_condition == "time":
            liquidation_time = portfolio.timestamp + timedelta(
                seconds=portfolio.liquidation_time_in_second
            )
            current_time = timezone.now()
            if current_time >= liquidation_time:
                logger.info(
                    f"포트폴리오 {portfolio.portfolio_id}의 청산 시간이 도래했습니다. 청산을 시작합니다."
                )
                # result["redirect_url"] = reverse("order:portfolio_list")
                result["liquidation"] = str(True)

                try:
                    liquidation_result = await liquidate_portfolio(
                        portfolio.portfolio_id, description="시간 기준 자동 청산"
                    )
                    liquidation_results.append(
                        {
                            "portfolio_id": portfolio.portfolio_id,
                            "result": liquidation_result,
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"포트폴리오 {portfolio.id} 청산 중 오류 발생: {str(e)}"
                    )
                continue
            else:
                logger.info(
                    f"포트폴리오 {portfolio.portfolio_id}의 청산 시간이 아직 도래하지 않았습니다."
                )

        elif portfolio.liquidation_condition == "pl":
            pnl = await portfolio.acalculate_pnl(current_prices)
            logger.info(f" 포트폴리오(청산) {portfolio.portfolio_id} PNL: {int(pnl)}")
            print(
                f"portfolio.target_profit {portfolio.target_profit} {type(portfolio.target_profit)}"
            )
            print(f"pnl {pnl} {type(pnl)}")

            if portfolio.target_profit is None:
                logger.info(
                    f"포트폴리오 {portfolio.portfolio_id}의 목표 수익이 설정되지 않았습니다. 청산을 건너뜁니다."
                )
                continue

            if pnl >= portfolio.target_profit:
                logger.info(
                    f"포트폴리오 {portfolio.portfolio_id}가 목표 수익 {int(portfolio.target_profit)}에 도달했습니다. 청산을 시작합니다."
                )
                # result["redirect_url"] = reverse("order:portfolio_list")
                result["liquidation"] = str(True)

                # request = HttpRequest()
                # request.method = "POST"
                # request.META["CONTENT_TYPE"] = "application/json"
                try:
                    liquidation_result = await liquidate_portfolio(
                        portfolio.portfolio_id, description="PL 기준 자동 청산"
                    )
                    liquidation_results.append(
                        {
                            "portfolio_id": portfolio.portfolio_id,
                            "result": liquidation_result,  # 여기를 변경
                            # "result": json.loads(
                            #     liquidation_result.content.decode("utf-8")
                            # ),
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"포트폴리오 {portfolio.id} 청산 중 오류 발생: {str(e)}"
                    )
            else:
                logger.info(
                    f"포트폴리오 {portfolio.portfolio_id}의 PNL({pnl})이 목표 수익({int(portfolio.target_profit)})에 도달하지 않았습니다."
                )
        elif portfolio.liquidation_condition == "pl_or_time":
            pnl = await portfolio.acalculate_pnl(current_prices)
            logger.info(
                f"포트폴리오({portfolio.liquidation_condition}) {portfolio.portfolio_id} PNL: {int(pnl)}"
            )
            liquidation_time_reached = (
                timezone.now() - portfolio.timestamp
            ).total_seconds() >= portfolio.liquidation_time_in_second
            if pnl >= portfolio.target_profit or liquidation_time_reached:
                if pnl >= portfolio.target_profit:
                    description = "PL 기준 청산"

                if liquidation_time_reached:
                    description = "시간 기준 청산 "

                logger.info(description)
                try:
                    liquidation_result = await liquidate_portfolio(
                        portfolio.portfolio_id, description=description
                    )
                    liquidation_results.append(
                        {
                            "portfolio_id": portfolio.portfolio_id,
                            "result": liquidation_result,  # 여기를 변경
                            # "result": json.loads(
                            #     liquidatin_result.content.decode("utf-8")
                            # ),
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"포트폴리오 {portfolio.portfolio_id} pl_or_time 청산중 오류 발생 {str(e)}"
                    )
            else:
                logger.info(
                    f"포트폴리오 {portfolio.portfolio_id}의 PNL({int(pnl)})이 목표 수익({int(portfolio.target_profit)})에 도달하지 않거나, 경과시간 {(timezone.now() - portfolio.timestamp).total_seconds():.0f}이 청산 시간 {portfolio.liquidation_time_in_second}에 도달하지 않았습니다."
                )

    if liquidation_results:
        result["liquidation_results"] = liquidation_results
    else:
        result["message"] = "청산할 포트폴리오가 없습니다."

    logger.info(f"{result}")
    return JsonResponse({"result": result})


async def run_flexswitch_strategy_internal(params: dict):
    """
    전략을 실행하는 내부 함수
    """
    logger.info(f"run_flexswitch_strategy at {datetime.now()}")

    strategy_type = params.get("strategy_type")
    shcode = params.get("shcode")
    lookback_period = int(params.get("period"))
    threshold = int(params.get("threshold"))
    buffer = int(params.get("buffer"))
    liquidation_delay = int(params.get("liquidation_delay"))
    monitoring_duration = int(params.get("monitoring_duration", 10))
    min_max_interval = float(params.get("min_max_interval", 0.0))
    multiplier = (
        250000
        if shcode[:3] in ["301", "201", "101"]
        else 50000 if shcode[:3] == "105" else 0
    )

    if multiplier == 0:
        logger.info("상품코드가 이상합니다.")
        return {"result": "상품코드가 이상합니다.", "portfolio_id": None}

    result = {}
    # end_date = datetime.now().strftime("%Y%m%d")
    current_datetime = datetime.now()
    current_time = current_datetime.time()
    stime = (current_datetime - timedelta(minutes=lookback_period)).strftime("%H%M")

    # 주간/야간 시장에 따른 데이터 조회
    day_market_start = time(9, lookback_period)
    day_market_end = time(15, 25 - lookback_period)
    night_market_start = time(18, lookback_period)
    night_market_end = time(3, 40 - lookback_period)

    if day_market_start <= current_time <= day_market_end:
        fut_data = get_hist_chetime(shcode, cvolume=1, stime=stime)
    elif night_market_start <= current_time or current_time <= night_market_end:
        fut_data = get_eurex_time_tick(shcode, cvolume=1, stime=stime)
    else:
        logger.info(f"{strategy_type}현재 시간은 유효한 거래시간이 아닙니다.")
        return {
            "result": "현재 시간은 유효한 거래 시간이 아닙니다.",
            "portfolio_id": None,
        }

    if not fut_data:
        logger.info("데이터가 없습니다.")
        return {"result": "데이터가 없습니다.", "portfolio_id": None}

    recent_prices = [float(d.get("price", 0)) for d in fut_data]  # min data경우 'close'

    # print(fut_data)
    max_price = max(recent_prices)
    min_price = min(recent_prices)
    price_range = max_price - min_price

    logger.info(
        f"max_price {max_price} min_price {min_price} price_range {price_range:.3f} threshold {threshold}"
    )

    # 전략 타입에 따른 임계값 및 방향 설정
    if strategy_type in ["buydip", "selldip"]:
        ub_price = min_price + price_range * threshold / 100.0
        lb_price = min_price + price_range * buffer / 100.0
        direction = "buy" if strategy_type == "buydip" else "sell"
    else:  # buypeak, sellpeak
        lb_price = max_price - price_range * threshold / 100.0
        ub_price = max_price - price_range * buffer / 100.0
        direction = "buy" if strategy_type == "buypeak" else "sell"

    # 전략 조건 확인
    condition_met = False
    # 실시간 호가 모니터링
    condition_met, bid_price, ask_price = await monitor_real_time_quotes_flex(
        strategy_type,
        shcode,
        lb_price,
        ub_price,
        min_price,
        max_price,
        monitoring_duration,
    )

    # if direction == "buy":
    #     condition_met = ask_price <= threshold_price
    # else:  # sell
    #     condition_met = bid_price >= threshold_price

    if condition_met:
        # 전체 포트폴리오 손익 계산
        # all_unique_codes = await Portfolio.aget_all_unique_codes()
        # current_prices = await Portfolio.aget_current_prices(all_unique_codes)

        # async for portfolio in Portfolio.objects.filter(status="Active"):
        #     pnl = await portfolio.acalculate_pnl(current_prices)
        #     total_pnl += pnl
        total_pnl = 0
        # logger.info(f"Active 포트폴리오 전체 손익 합계: {total_pnl}")

        # if total_pnl >= 0:
        if max_price - min_price > min_max_interval:
            trade_description = (
                f"전략: {strategy_type}, "
                f"min:{min_price:.2f} LB:{lb_price:.2f} UB:{ub_price:.2f} max{max_price:.2f}"
                f"방향: {direction}"
            )

            logger.info(trade_description)

            # 주문 생성 및 실행
            order_manager = OrderManager(
                order_category="new",
                portfolio_id=params.get("portfolio_id"),  # TODO 여기서 만들것
                strategy=f"{strategy_type}_strategy",
                target_profit=multiplier * price_range,
            )

            order = Order(
                focode=shcode,
                quantity=1,
                direction=direction,
                order_type="market",
                price=None,
                description=trade_description,
            )

            order_manager.add_order(order)

            try:
                order_results, portfolio_id = await place_orders(order_manager)
                result["order_results"] = order_results

                all_completed = all(
                    result["status"] == "completed" for result in order_results
                )
                if all_completed:
                    portfolio = await Portfolio.objects.aget(portfolio_id=portfolio_id)
                    portfolio.status = "Active"
                    portfolio.description = f"Working on {strategy_type}_strategy"
                    portfolio.liquidation_condition = "pl_or_time"
                    portfolio.liquidation_time_in_second = liquidation_delay * 60
                    await portfolio.asave()
                    logger.info(f"{strategy_type} 주문 완료")

            except Exception as e:
                logger.error(f"주문 실행 중 오류 발생: {str(e)}")
                result["error"] = str(e)
        else:
            logger.info(f"min-max <{min_max_interval}이므로 주문 건너뛴다.")
            result["skip_reason"] = "min-max < minimum min_max interval"
    else:
        logger.info(f"{strategy_type} 조건 불발")
        result["skip_reason"] = f"{strategy_type} 전략 조건이 충족되지 않았습니다."

    return result


async def get_current_price(shcode):
    current_datetime = datetime.now()
    if (
        current_datetime.hour >= 9
        or (current_datetime.hour == 8 and current_datetime.minute > 45)
    ) and (current_datetime.hour < 17):
        current_orderbook = await get_current_orderbook_async(shcode)

    else:
        current_orderbook = await get_current_orderbook_eurex_async(shcode)

    return (
        float(current_orderbook["bidho1"]) + float(current_orderbook["offerho1"])
    ) / 2


async def run_volatility_strategy(request):
    LOOKBACK_MINUTES = 20
    FIVE = 5
    VOL_THRESHOLD = 0.003
    logger.info(f"Starting monitoring and trade process {datetime.now()}")
    result = {}

    sometime_ago = timezone.now() - timezone.timedelta(minutes=LOOKBACK_MINUTES * 2)
    recent_data = []
    async for data in VolatilityData.objects.filter(
        date_time__gte=sometime_ago
    ).order_by("-date_time"):
        recent_data.append(data)

    # if len(recent_data) < 2:
    #     result["error"] = f"데이터가 충분하지 않습니다.{datetime.now()}"
    #     return JsonResponse({"result": result})

    five_min_data = recent_data[:FIVE]
    logger.info("Short term volatility data:")
    for data in five_min_data:
        logger.info(
            f"DateTime: {data.date_time}, IV20: {(data.iv_20)*100:.2f}%, Option Code: {data.option_code}, Future Code: {data.future_code}"
        )

    if len(five_min_data) < 5:
        result["error"] = (
            f"5분 평균을 위한 데이터가 부족합니다. 현재 {len(five_min_data)}개의 데이터만 사용 가능합니다."
        )
        logger.info(f"5분 평균을 위한 데이터가 부족합니다. ")
        return JsonResponse({"result": result})

    # TODO recent_data에서 date_time항목의 가장 빠른 시간이  현재 시간보다 1시간 이전이면서 데이터의 개수가 60개 이상일경우
    # 아래 코드를 실행한다.
    if recent_data:
        # LOOKBACK_MINUTES=60
        oldest_data_time = recent_data[-1].date_time
        current_time = timezone.now()
        print(f"recent data length {len(recent_data)}")
        # print(f"oldest_data_time {oldest_data_time}< current_time {current_time - timezone.timedelta(
        #     minutes=LOOKBACK_MINUTES
        # )}")
        print(f"oldest_data_time {oldest_data_time}")
        if len(
            recent_data
        ) >= LOOKBACK_MINUTES and oldest_data_time <= current_time - timezone.timedelta(
            minutes=LOOKBACK_MINUTES
        ):
            # pass
            avg_5min = np.mean([data.iv_20 for data in five_min_data])
            avg_90min = np.mean([data.iv_20 for data in recent_data])

            result["avg_5min"] = float(avg_5min)
            result["avg_90min"] = float(avg_90min)
            logger.info(
                f"short term avg {float(avg_5min)*100:.2f}% long term avg {float(avg_90min)*100:.2f}%"
            )
            condition_met = avg_5min > avg_90min - VOL_THRESHOLD
            # condition_met2 = avg_5min <= avg_90min

            result["condition_met"] = str(condition_met)
            # result["condition_met2"] = str(condition_met2)

            if condition_met:
                logger.info(
                    f"Trading condition1 met, 5min vol {avg_5min:.2f}% vs 90min vol {avg_90min:.2f}% initiating orders"
                )
                latest_data = recent_data[0]
                new_portfolio_id = generate_portfolio_id()
                order_manager = OrderManager(
                    order_category="new",
                    portfolio_id=new_portfolio_id,
                    target_profit=latest_data.option_theta,
                    strategy="volatility_strategy",
                )

                orders = [
                    Order(
                        focode=latest_data.option_code,
                        quantity=1,
                        direction="sell",
                        order_type="market",
                        price=None,
                    ),
                    Order(
                        focode=latest_data.future_code,
                        quantity=1,
                        direction="sell",
                        order_type="market",
                        price=None,
                    ),
                ]

                for order in orders:
                    order_manager.add_order(order)

                # todo hardcoding 개선할것
                order_manager.target_profit = latest_data.option_theta * 250000

                try:
                    order_results, portfolio_id = await place_orders(order_manager)
                    result["order_results"] = order_results
                    result["portfolio_id"] = portfolio_id

                    all_completed = all(
                        result["status"] == "completed" for result in order_results
                    )

                    if all_completed:
                        portfolio = await Portfolio.objects.aget(
                            portfolio_id=portfolio_id
                        )
                        portfolio.status = "Active"
                        portfolio.description = "변동성 전략 진행 중"
                        portfolio.liquidation_condition = "pl"
                        portfolio.target_profit = order_manager.target_profit
                        await portfolio.asave()
                        logger.info(f"포트폴리오 {portfolio_id} 생성 완료")
                    else:
                        incomplete_orders = make_reverse_order(order_manager)
                        if incomplete_orders:
                            clear_order_manager = OrderManager(
                                order_category="clear_incompleted",
                                portfolio_id=portfolio_id,
                            )

                            for order_item in incomplete_orders:
                                clear_order = Order(
                                    focode=order_item["focode"],
                                    quantity=int(order_item["quantity"]),
                                    direction=order_item["direction"],
                                    order_type=order_item["order_type"],
                                    price=order_item["order_price"],
                                )
                                clear_order_manager.add_order(clear_order)

                            clear_results, _ = await place_orders(clear_order_manager)

                            reverse_orders_completed = all(
                                result["status"] == "completed"
                                for result in clear_results
                            )
                            portfolio = await Portfolio.objects.aget(
                                portfolio_id=portfolio_id
                            )
                            portfolio.status = (
                                "Closed" if reverse_orders_completed else "Pending"
                            )
                            portfolio.description = (
                                "Closed because of incompleted trades"
                                if reverse_orders_completed
                                else "Pending by incompleted trades. Take manual action!"
                            )
                            portfolio.liquidation_condition = None
                            portfolio.target_profit = None
                            await portfolio.asave()

                            order_results.extend(clear_results)

                    result["final_status"] = "success" if all_completed else "partial"
                    result["message"] = (
                        "변동성 전략 주문 완료"
                        if all_completed
                        else "일부 주문 실패, 청산 처리 완료"
                    )

                except Exception as e:
                    logger.error(f"주문 처리 중 오류 발생: {str(e)}")
                    result["error"] = str(e)
                    result["final_status"] = "error"
                    result["message"] = "주문 처리 중 오류 발생"

            else:
                logger.info(
                    f"거래 조건 미충족, 5분 변동성 {avg_5min*100:.2f}% vs 90분 변동성 {avg_90min*100:.2f}% {datetime.now()}"
                )
                result["message"] = f"거래 조건이 충족되지 않았습니다. {datetime.now()}"
        else:  #
            logger.info(f"거래데이터 요건 불충분")
            result["message"] = f"거래데이터 요건 불충분. {datetime.now()}"

    return JsonResponse({"result": result})


async def check_auto_liquidation_status(request):
    is_running = BackgroundTaskManager.is_liquidation_task_running()
    return JsonResponse({"is_running": is_running})


async def check_strategy_status(request):
    strategy_type = request.GET.get("strategy")
    if not strategy_type:
        return JsonResponse({"error": "전략 타입이 지정되지 않았습니다"}, status=400)

    is_running = strategy_type in BackgroundTaskManager._tasks

    return JsonResponse({"status": "success", "is_running": is_running})


async def portfolio_stream(request):
    # no task버전
    async def event_stream():
        while True:
            try:
                # fetch_portfolios_internal 호출
                portfolio_data = await fetch_portfolios_internal()
                data = portfolio_data.content.decode("utf-8")

                # SSE 형식으로 데이터 전송
                yield f"data: {data}\n\n"

                await asyncio.sleep(15)  # 15초 대기
            except Exception as e:
                logger.error(f"Portfolio streaming error: {e}")
                break

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


async def fetch_portfolios_internal():
    portfolios_data = []
    all_unique_codes = await Portfolio.aget_all_unique_codes()
    current_prices = await Portfolio.aget_current_prices(all_unique_codes)
    portfolios = Portfolio.objects.all().order_by("-timestamp").aiterator()

    async for portfolio in portfolios:  # TODO closed된 port는 계산할 x

        pnl = await portfolio.acalculate_pnl(current_prices)
        portfolio.pnl = pnl
        await portfolio.asave()
        portfolio_dict = await portfolio.ato_dict()
        portfolios_data.append(portfolio_dict)

    # today total pnl 계산하기(closed, active, pending 모두)
    today = timezone.now().date()
    today_portfolios = []
    async for portfolio in Portfolio.objects.filter(timestamp__date=today):
        today_portfolios.append(portfolio)

    # today_portfolios = [p for p in portfolios if p.timestamp.date() == today]

    strategy_pnl = {}
    for portfolio in today_portfolios:
        if portfolio.strategy not in strategy_pnl:
            strategy_pnl[portfolio.strategy] = 0
        strategy_pnl[portfolio.strategy] += portfolio.pnl

    total_pnl = sum(strategy_pnl.values())

    return JsonResponse(
        {
            "portfolios": portfolios_data,
            "total_pnl_today": total_pnl,
            "strategy_pnl": strategy_pnl,
        }
    )


async def start_portfolio_monitor_task(request):
    try:
        data = json.loads(request.body)
        action = data.get("action")

        if action == "start":
            result = await BackgroundTaskManager.start_portfolio_monitor_task()
            return JsonResponse(result)
        elif action == "stop":
            result = BackgroundTaskManager.stop_portfolio_monitor_task()
            return JsonResponse(result)
        return JsonResponse(
            {"error": "잘못된 액션입니다. 'start' 또는 'stop'이어야 합니다."},
            status=400,
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)


async def check_portfolio_monitor_status(request):
    is_running = BackgroundTaskManager.is_portfolio_monitor_running()
    return JsonResponse({"is_running": is_running})


async def start_auto_liquidation_task(request):
    logger.info(f"서버모드 자동청산 실행")
    try:
        data = json.loads(request.body)
        action = data.get("action")
        print(f"action: start or stop= {action}")
        if action == "start":
            result = await BackgroundTaskManager.start_liquidation_task()
            return JsonResponse(result)
        elif action == "stop":
            result = BackgroundTaskManager.stop_liquidation_task()
            return JsonResponse(result)
        return JsonResponse(
            {"error": "잘못된 액션입니다. 'start'또는 'stop'이어야함 "}, status=400
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "요청본문의 json형식이 잘못된"}, status=400)
