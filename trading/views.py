from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from tr.stock.invest_info.t3521 import get_cd_rate
from tr.futures.market_data.t8435 import get_listed_future
from .jobs import calcVol, calc_iv_hist, generate_volatility_graph
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def index(request):
    logger.info("vol Index page requested")
    return render(request, "trading/index.html")


def graph(request):
    threshold = request.GET.get("threshold", "0.3")

    threshold = float(threshold) / 100.0
    # logger.info(f"Graph generation requested with threshold {threshold*100}%")
    image_path = generate_volatility_graph(threshold)
    logger.debug(f"Graph generated at {image_path}")
    with open(image_path, "rb") as f:
        return HttpResponse(f.read(), content_type="image/png")


def historic(request):
    if request.method == "POST":
        data = json.loads(request.body)
        yymm = data.get("yymm")

        edate = date.today()
        sdate = edate - timedelta(days=1)
        edate = edate.strftime("%Y%m%d")
        sdate = sdate.strftime("%Y%m%d")

        if yymm:
            logger.info(
                f"Historical data calculation requested for YYMM: {yymm}, start date: {sdate}, end date: {edate}"
            )
            rst = calc_iv_hist(yymm=yymm, ncnt=1, sdate=sdate, edate=edate)
            logger.info(
                f"Historical IV calculation completed. Created: {rst['created']}, Updated: {rst['updated']}, Errors: {rst['error']}"
            )
            return JsonResponse({"status": "success"})
        else:
            logger.warning("YYMM parameter missing in historical data request")
            return JsonResponse({"error": "YYMM parameter is required"}, status=400)
    else:
        logger.warning("Invalid request method for historical data")
        return JsonResponse({"error": "Invalid request method"}, status=400)


def calc_spot_vol(request):
    if request.method == "POST":
        data = json.loads(request.body)
        fut_code = data.get("fut_code")
        maturity = data.get("maturity")
        cd_rate = float(data.get("cd_rate")) / 100.0

        logger.debug(
            f"Spot volatility calculation requested for future code: {fut_code}, maturity: {maturity}, CD rate: {cd_rate}"
        )
        result, vol_threshold = calcVol(fut_code, maturity, cd_rate)
        logger.debug(f"Spot volatility calculation result: {result}")
        return JsonResponse({"result": result, "vol_threshold": vol_threshold})
    else:
        logger.warning("Invalid request method for spot volatility calculation")
        return JsonResponse({"error": "Invalid request method"}, status=400)


def init(request):
    if request.method == "POST":
        # logger.info("Initialization request received")
        cd_rate_data = get_cd_rate()
        fut_list = get_listed_future("MF")

        if not isinstance(cd_rate_data, dict):
            logger.error("CD rate data is not a dictionary")
            return JsonResponse({"error": "cd_rate_data is not a dict"}, status=500)

        logger.info("market page initialization completed successfully")
        return JsonResponse(
            {"cd_rate": cd_rate_data.get("close"), "listed_fut": fut_list}
        )
    else:
        logger.info("GET request to init, rendering index page")
        return JsonResponse(
            {
                "cd_rate": "",
                "listed_fut": [],
                "message": "data was not retrieved by some reson",
            }
        )


def futures_price_view(request):
    return render(request, "trading/futures_price.html")


@csrf_exempt
def start_collection(request):
    print("start_collection called")
    channel_layer = get_channel_layer()
    print("channel_layer:", channel_layer)

    async_to_sync(channel_layer.group_send)(
        "futures_price", {"type": "start_collection"}
    )
    return JsonResponse({"status": "started"})


@csrf_exempt
def stop_collection(request):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "futures_price", {"type": "stop_collection"}
    )
    return JsonResponse({"status": "stopped"})
