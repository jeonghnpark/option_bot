from django.conf import settings
import os


from django.db import transaction

from tr.futures.market_data.t2101 import get_current
from tr.stock.invest_info.t3521 import get_cd_rate

from tr.futures.market_data.t2830 import get_current as get_current_eurex
from tr.futures.market_data.t2301 import get_current_screen
from tr.futures.market_data.t2835 import get_current_screen as get_current_screen_eurex
from mathematics.BSformula.bs76 import bs_greeks
from tr.futures.market_data.t2105 import get_current_orderbook
from tr.futures.market_data.t2831 import (
    get_current_orderbook as get_current_orderbook_eurex,
)

from tr.futures.market_data.t8435 import get_listed_future
from tr.futures.chart.t8415 import get_hist_fut
from tr.futures.chart.t8429 import get_eurex_ntick
from tr.futures.market_data.t8433 import get_options_codes

import pandas as pd

# import time
from datetime import datetime, timedelta

from mathematics.BSformula.bs76 import bs_greeks_mid
from .models import VolatilityData

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib import gridspec
import matplotlib.dates as mdates

matplotlib.use("Agg")

from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def fetch_latest_data():
    now = timezone.now()
    query_set = VolatilityData.objects.filter(
        date_time__gte=now.date() - timedelta(days=2)
    ).order_by("date_time")
    return pd.DataFrame(list(query_set.values()))


def generate_volatility_graph(threshold=0.0025):
    data = fetch_latest_data()
    data["date_time"] = pd.to_datetime(data["date_time"])
    data.set_index("date_time", inplace=True)

    fig = plt.figure(figsize=(10, 7))
    gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 2])
    ax0 = fig.add_subplot(gs[0])  # future graph
    ax1 = fig.add_subplot(gs[2])  # vol graph
    ax2 = fig.add_subplot(gs[1])  # avg vol graph

    # 이동 평균 계산
    data["5min_avg"] = data["iv_20"].rolling(window="5min", min_periods=5).mean()
    data["90min_avg"] = data["iv_20"].rolling(window="90min", min_periods=90).mean()

    ax1.plot(data.index, data["5min_avg"] * 100, label="5min Avg IV", color="blue")
    ax1.plot(data.index, data["90min_avg"] * 100, label="90min Avg IV", color="brown")
    ax1.scatter(
        data.index,
        data["iv_20"] * 100,
        color="grey",
        s=10,
        alpha=0.3,
        label="Instantaneous IV",
    )

    ax1.scatter(
        data.index[-1],
        data["iv_20"].iloc[-1] * 100,
        color="black",
        s=20,
        label=f"Last IV: {data['iv_20'].iloc[-1]*100:.2f}%",
    )
    ax1.annotate(
        f"{data['iv_20'].iloc[-1]*100:.2f}%\n{data.index[-1].hour}:{data.index[-1].minute}:{data.index[-1].second}\ndiff={(data['5min_avg'].iloc[-1]-data['90min_avg'].iloc[-1])*100 :.2f}%",  # 변동성 값을 백분율로 표시
        (data.index[-1], data["iv_20"].iloc[-1] * 100),
        textcoords="offset points",
        xytext=(10, 0),
        ha="left",
        color="blue",
    )
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Implied Volatility (%)")
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax1.yaxis.set_major_locator(MultipleLocator(0.25))
    ax1.tick_params(axis="x", rotation=60, labelsize=7)
    ax1.legend(loc="upper left")
    ax1.grid(True)

    ax0.set_ylabel("Future Price")
    ax0.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
    ax0.xaxis.set_major_locator(mdates.HourLocator(interval=2))  # 여기를 변경합니다.

    ax0.plot(data.index, data["future_price"], color="black", label="Future Price")
    ax0.scatter(
        data.index[-1],
        data["future_price"].iloc[-1],
        color="grey",
        s=20,
    )
    ax0.annotate(
        f"{data['future_price'].iloc[-1]}",  # 변동성 값을 백분율로 표시
        (data.index[-1], data["future_price"].iloc[-1]),
        textcoords="offset points",
        xytext=(10, 0),
        ha="left",
        color="blue",
    )

    ax0.legend(loc="upper left")
    ax0.grid(True)

    # ax0.tick_params(axis="x", rotation=45)
    ax0.set_xticklabels([])
    ax0.set_xticks([])

    ax2.set_ylabel("5min-90min")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))  # 여기를 변경합니다.

    ax2.plot(
        data.index,
        (data["5min_avg"] - data["90min_avg"]) * 100,
        color="gray",  # 검은색 대신 회색으로 변경
        linewidth=1.0,  # 선의 두께를 줄임 (기본값은 보통 1.5)
        alpha=0.6,  # 투명도를 설정 (0에서 1 사이의 값, 1이 완전 불투명)
        label="5min-90min",
    )
    # logger.info(
    #     f"avg5m-avg90m={(data['5min_avg'].iloc[-1] - data['90min_avg'].iloc[-1]) * 100:.3f}%"
    # )

    ax2.scatter(
        data.index[-1],
        (data["5min_avg"].iloc[-1] - data["90min_avg"].iloc[-1]) * 100,
        color="black",
        s=10,
    )
    ax2.annotate(
        f"{data.index[-1].hour}:{data.index[-1].minute}:{data.index[-1].second}\n5min avg={data['5min_avg'].iloc[-1]*100:.2f}%\n90min avg={data['90min_avg'].iloc[-1]*100:.2f}%\n{(data['5min_avg'].iloc[-1]-data['90min_avg'].iloc[-1])*100:.2f}%",  # 변동성 값을 백분율로 표시
        (
            data.index[-1],
            (data["5min_avg"].iloc[-1] - data["90min_avg"].iloc[-1]) * 100,
        ),
        textcoords="offset points",
        xytext=(10, 0),
        ha="left",
        color="blue",
    )
    mask_up = (data["5min_avg"] - data["90min_avg"]) > threshold
    ax2.fill_between(
        data.index,
        0,
        (data["5min_avg"] - data["90min_avg"]) * 100,
        # ax2.get_ylim()[1],
        where=mask_up,
        color="red",
        alpha=0.3,
    )

    mask_down = (data["90min_avg"] - data["5min_avg"]) > threshold
    ax2.fill_between(
        data.index,
        0,
        (data["5min_avg"] - data["90min_avg"]) * 100,
        where=mask_down,
        color="blue",
        alpha=0.3,
    )

    ax2.axhline(
        y=threshold * 100,
        color="r",
        linestyle="--",
        label=f"Threshold {threshold*100}%",
        linewidth=0.8,  # 선의 두께를 줄임 (기본값은 보통 1.5)
        alpha=0.4,  # 투명도를 설정 (0에서 1 사이의 값, 1이 완전 불투명)
    )

    ax2.annotate(
        f"{threshold*100:.2f}%",
        xy=(0, threshold * 100),  # 데이터 좌표계에서의 위치 (x축의 끝, threshold 값)
        xytext=(-3, 0),
        xycoords=("axes fraction", "data"),  # x는 축의 비율, y는 데이터 값
        textcoords="offset points",
        color="red",  # 붉은색으로 설정
        va="center",  # 수직 정렬을 중앙으로
        ha="right",  # 수평 정렬을 왼쪽으로
        fontsize=8,
    )

    ax2.axhline(
        y=-threshold * 100,
        color="b",
        linestyle="--",
        label=f"Threshold {-threshold*100}%",
        linewidth=0.8,  # 선의 두께를 줄임 (기본값은 보통 1.5)
        alpha=0.4,  # 투명도를 설정 (0에서 1 사이의 값, 1이 완전 불투명)
    )

    ax2.annotate(
        f"{-threshold*100:.2f}%",
        xy=(0, -threshold * 100),  # 데이터 좌표계에서의 위치 (x축의 끝, threshold 값)
        xytext=(-3, 0),  # 텍스트 오프셋 (약간 오른쪽으로)
        xycoords=("axes fraction", "data"),  # x는 축의 비율, y는 데이터 값
        textcoords="offset points",
        color="blue",  # 붉은색으로 설정
        va="center",  # 수직 정렬을 중앙으로
        ha="right",  # 수평 정렬을 왼쪽으로
        fontsize=8,
    )
    ax2.legend(loc="upper left")
    ax2.grid(True)

    # ax2.tick_params(axis="x", rotation=45)
    ax2.set_xticklabels([])
    ax2.set_xticks([])

    plt.tight_layout()

    # 이미지 파일 저장 경로 수정
    image_dir = os.path.join(settings.MEDIA_ROOT, "volatility_graphs")
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(
        image_dir, f"volatility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )

    plt.savefig(image_path)
    plt.close()

    return image_path


def save_volatility_data(data_list):
    """
    VolatilityData모델을 사용하여 변동성 데이터 저장
    :param data_list : 저장할 데이터의 리스트, 각 항목은 dict
    """
    update_count = 0
    create_count = 0
    error_count = 0

    with transaction.atomic():
        for data in data_list:
            try:
                obj, created = VolatilityData.objects.update_or_create(
                    date_time=data["date_time"],
                    defaults={
                        "iv_20": data["iv_20"],
                        "option_code": data["option_code"],
                        "option_price": data["option_price"],
                        "option_delta": data["option_delta"],
                        "option_gamma": data["option_gamma"],
                        "option_vega": data["option_vega"],
                        "option_theta": data["option_theta"],
                        "future_code": data["future_code"],
                        "future_price": data["future_price"],
                    },
                )
                if created:
                    create_count += 1
                else:
                    update_count += 1
            except Exception as e:
                error_count += 1
    result = {"created": create_count, "updated": update_count, "error": error_count}
    logger.debug(
        f"변동성 데이터 저장 결과 -현재: {data_list[0].get('iv_20')*100:.2f}%  생성: {create_count}, 업데이트: {update_count}, 오류: {error_count}"
    )

    return result


def calcVol(fut_code, maturity, cd_rate):

    current_datetime = datetime.now()

    if current_datetime.hour >= 18 or current_datetime.hour < 5:
        fut_data = get_current_eurex(fut_code)
        fut_order_book = get_current_orderbook_eurex(fut_code)
        option_data = get_current_screen_eurex(maturity, "G")
    elif (
        current_datetime.hour >= 9
        or (current_datetime.hour == 8 and current_datetime.minute > 45)
    ) and (
        current_datetime.hour <= 14
        or (current_datetime.hour == 15 and current_datetime.minute <= 35)
    ):
        # elif current_datetime.hour >= 9:
        fut_data = get_current(fut_code)
        fut_order_book = get_current_orderbook(fut_code)
        option_data = get_current_screen(maturity, "G")

    else:
        logging.info("Market is closed. Job will not proceed.")
        return None, None

    if fut_data is None:
        logging.info("선물데이터(t2101) API 호출 실패. 작업을 중단합니다. ")
        return None, None
    if option_data is None:
        logging.info("옵션데이터 (t2301) API 호출 실패. 작업을 중단")
        return None, None

    fut_price = float(fut_data.get("price"))
    list_put = [
        e["optcode"]
        for e in option_data[2]
        if float(e["actprice"]) <= fut_price
        and float(e["actprice"]) > fut_price - 2.5 * 15
    ]
    df_option_filtered = pd.DataFrame(option_data[2])
    df_option_filtered = df_option_filtered.loc[
        df_option_filtered["optcode"].isin(list_put)
    ]

    # df_option_filtered["close_fut"] = float(fut_data.get("price"))
    df_option_filtered["close_fut"] = (
        float(fut_order_book.get("bidho1")) / 2
        + float(fut_order_book.get("offerho1")) / 2
    )

    df_option_filtered["cd_rate"] = cd_rate

    df_option_filtered["date_time"] = current_datetime

    df_option_filtered.rename(
        columns={"price": "close", "optcode": "shcode", "actprice": "strike"},
        inplace=True,
    )
    col_to_be_float = ["close", "close_fut", "strike", "bidho1", "offerho1"]
    df_option_filtered[col_to_be_float] = df_option_filtered[col_to_be_float].astype(
        "float"
    )

    greeks = df_option_filtered.apply(lambda row: bs_greeks_mid(row), axis=1)
    df_greeks = pd.DataFrame(
        greeks.tolist(), columns=["iv2", "delta2", "gamma2", "vega2", "theta2"]
    )
    df_option_filtered.reset_index(
        drop=True, inplace=True
    )  # 인덱스가 다르면 pd.concat으로 붙일수 없음
    df_option_filtered = pd.concat([df_option_filtered, df_greeks], axis=1)
    df_option_filtered["date_time"] = current_datetime.strftime(
        "%Y-%m-%d %H:%M:%S"
    )  # db에 넣기 전에 8문자열로
    df_option_filtered = df_option_filtered[
        [
            "date_time",
            "shcode",
            "strike",
            "close",
            "close_fut",
            "cd_rate",
            "iv2",
            "delta2",
            "gamma2",
            "vega2",
            "theta2",
        ]
    ]

    # TODO VolatilityDataDetial table을 만들고 저장
    closest_option = df_option_filtered.iloc[
        (df_option_filtered["delta2"] + 0.2).abs().argsort()[:1]
    ]

    larger_option = df_option_filtered[df_option_filtered["delta2"] >= -0.2].nsmallest(
        1, "delta2"
    )
    smaller_option = df_option_filtered[df_option_filtered["delta2"] < -0.2].nlargest(
        1, "delta2"
    )
    larger_delta = larger_option["delta2"].values[0]
    smaller_delta = smaller_option["delta2"].values[0]
    larger_delta_vol = larger_option["iv2"].values[0]
    smaller_delta_vol = smaller_option["iv2"].values[0]

    iv_at_20delta = (
        (larger_delta - (-0.2)) * smaller_delta_vol
        + (-0.2 - smaller_delta) * larger_delta_vol
    ) / (larger_delta - smaller_delta)

    result = (
        f"{current_datetime.hour}:{current_datetime.minute}:{current_datetime.second}\n "
        f"20delta_vol:{iv_at_20delta * 100:.2f}% "
        f"fut code:{fut_code} "
        f"fut price:{fut_price} \n"
        f"option:{larger_option['shcode'].iloc[-1]} "
        f"vol:{larger_option['iv2'].iloc[-1] * 100:.2f} "
        f"option delta :{larger_option['delta2'].iloc[-1]:.3f} "
        f"option theta :{larger_option['theta2'].iloc[-1] * 250000:.0f} "
        f"option vega :{larger_option['vega2'].iloc[-1] * 250000:.0f} \n"
        f"option2:{smaller_option['shcode'].iloc[-1]} "
        f"vol2:{smaller_option['iv2'].iloc[-1] * 100:.2f} "
        f"option delta2:{smaller_option['delta2'].iloc[-1]:.3f} "
        f"option theta2:{smaller_option['theta2'].iloc[-1] * 250000:.0f} "
        f"option vega2:{smaller_option['vega2'].iloc[-1] * 250000:.0f} "
    )

    try:
        vol_threshold = (
            closest_option["theta2"].iloc[-1] / closest_option["vega2"].iloc[-1]
        )
    except ZeroDivisionError:
        vol_threshold = 0
    except Exception as e:
        logger.error(f"vol_threshold 계산 중 오류 발생: {e}")
        vol_threshold = 0

    volatility_data = []
    # logger.info("closest_option의 모든 내용:")
    # for column in closest_option.columns:
    #     logger.info(f"{column}: {closest_option[column].iloc[-1]}")

    volatility_data.append(
        {
            "date_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "iv_20": iv_at_20delta,
            "option_code": closest_option["shcode"].iloc[-1],
            "option_price": closest_option["close"].iloc[-1],
            "option_delta": closest_option["delta2"].iloc[-1],
            "option_gamma": closest_option["gamma2"].iloc[-1],
            "option_vega": closest_option["vega2"].iloc[-1],
            "option_theta": closest_option["theta2"].iloc[-1],
            "future_code": fut_code,
            "future_price": fut_price,
        }
    )
    # logger.info(f"vol data \n{volatility_data}")

    # print(result, vol_threshold)

    rst = save_volatility_data(volatility_data)
    return result, vol_threshold


def calc_iv_hist(yymm, ncnt, sdate, edate):
    """
    전일 정규장, 야간장, 금일 정규장의 20deltal vol을 계산한다.
    sdate: "yyyymmdd" 전일자 정규장, 야간장일
    edate: "yyyymmdd" 오늘자
    return :DataFrame
    """
    hname = "MF " + yymm
    data = get_listed_future("MF")
    shcode = [e["shcode"] for e in data if e["hname"] == hname]
    focode = shcode[0]
    next_sdate_dt = datetime.strptime(sdate, "%Y%m%d") + timedelta(days=1)
    next_sdate = next_sdate_dt.strftime("%Y%m%d")

    current_datetime = datetime.now()

    fut_data = []
    fut_data_eurex = []

    if (
        current_datetime.hour >= 9
        or (current_datetime.hour == 8 and current_datetime.minute > 45)
    ) and (current_datetime.hour < 17):
        # 정규시간의 경우
        fut_data = get_hist_fut(focode, ncnt, sdate, edate)
        fut_data_eurex = get_eurex_ntick(focode, "B", ncnt, 999)
        fut_data_eurex = [
            {
                "date": sdate,  # 일단 전일자로 설정
                "time": d["chetime"],
                "close": d["price"],
                **{k: v for k, v in d.items() if (k != "chetime" and k != "price")},
            }
            for d in fut_data_eurex
        ]
        for entry in fut_data_eurex:  #
            if int(entry["time"]) >= 240000:  # 24시 이후는 오늘로 설정
                entry["date"] = edate
                entry["time"] = f'{int(entry["time"])-240000:06}'
            else:  # 24시 전에는 전일로 설정
                entry["date"] = sdate

    elif current_datetime.hour >= 17 and current_datetime.hour < 18:
        # 17시 이후로는 야간데이터 사라짐
        fut_data = get_hist_fut(focode, ncnt, edate, edate)  # 주간 데이터는 당일만

    elif 18 <= current_datetime.hour < 24:
        fut_data = get_hist_fut(focode, ncnt, edate, edate)
        fut_data_eurex = get_eurex_ntick(focode, "B", ncnt, 999)
        fut_data_eurex = [
            {
                "date": edate,
                "time": d["chetime"],
                "close": d["price"],
                **{k: v for k, v in d.items() if (k != "chetime" and k != "price")},
            }
            for d in fut_data_eurex
        ]

    else:
        return

    if fut_data_eurex:
        df_fut_data = pd.DataFrame(fut_data)
        df_fut_data_eurex = pd.DataFrame(fut_data_eurex)

        df_fut_merged = pd.concat(
            [
                df_fut_data[["date", "time", "close", "high", "low"]],
                df_fut_data_eurex[["date", "time", "close", "high", "low"]],
            ],
            axis=0,
        )
    else:  # df_fut_data_eurex==[]인 경우
        df_fut_data = pd.DataFrame(fut_data)
        df_fut_merged = df_fut_data

    df_fut_merged["date_time"] = pd.to_datetime(
        df_fut_merged["date"].astype(str) + " " + df_fut_merged["time"].astype(str),
        format="%Y%m%d %H%M%S",
    )

    df_fut_merged.drop(["date", "time"], axis=1, inplace=True)
    df_fut_merged.sort_values(by="date_time", inplace=True)

    df_fut_merged[["close", "high", "low"]] = df_fut_merged[
        ["close", "high", "low"]
    ].astype(float)

    ref = float(df_fut_merged.iloc[-1]["close"])

    opt_list = get_options_codes()

    opt_list_filtered = [
        e
        for e in opt_list
        if float(e["hname"][-5:]) <= ref
        and float(e["hname"][-5:]) > ref - 2.5 * 15
        and e["hname"][0] == "P"
        and e["hname"][2:6] == yymm
    ]

    opt_data = []
    opt_data_eurex = []

    for row in opt_list_filtered[:]:

        opcode = row["shcode"]
        if (
            current_datetime.hour >= 9
            or (current_datetime.hour == 8 and current_datetime.minute > 45)
        ) and (current_datetime.hour < 17):
            # 한국 정규시장
            opt_data_tmp = get_hist_fut(opcode, ncnt, sdate, edate)
            opt_data_tmp = [
                {**d, "shcode": opcode, "strike": float(row["hname"][-5:])}
                for d in opt_data_tmp
            ]

            opt_data[:0] = opt_data_tmp

            opt_data_eurex_tmp = get_eurex_ntick(opcode, "B", ncnt, 999)
            opt_data_eurex_tmp = [
                {
                    "date": edate,
                    "time": d["chetime"],
                    "close": d["price"],
                    "shcode": opcode,
                    "strike": float(row["hname"][-5:]),
                    **{k: v for k, v in d.items() if (k != "chetime" and k != "price")},
                }
                for d in opt_data_eurex_tmp
            ]

            for entry in opt_data_eurex_tmp:
                if int(entry["time"]) >= 240000:
                    entry["date"] = edate
                    entry["time"] = f'{int(entry["time"])-240000:06}'
                else:
                    entry["date"] = sdate

            opt_data_eurex[:0] = opt_data_eurex_tmp
        elif current_datetime.hour >= 17 and current_datetime.hour < 18:
            # 17시 이후로는 야간데이터 사라짐
            opt_data_tmp = get_hist_fut(opcode, ncnt, sdate, edate)
            opt_data_tmp = [
                {**d, "shcode": opcode, "strike": float(row["hname"][-5:])}
                for d in opt_data_tmp
            ]

            opt_data[:0] = opt_data_tmp
        elif 18 <= current_datetime.hour < 24:
            opt_data_tmp = get_hist_fut(opcode, ncnt, edate, edate)
            opt_data_tmp = [
                {**d, "shcode": opcode, "strike": float(row["hname"][-5:])}
                for d in opt_data_tmp
            ]

            opt_data[:0] = opt_data_tmp

            opt_data_eurex_tmp = get_eurex_ntick(opcode, "B", ncnt, 999)
            opt_data_eurex_tmp = [
                {
                    "date": edate,
                    "time": d["chetime"],
                    "close": d["price"],
                    "shcode": opcode,
                    "strike": float(row["hname"][-5:]),
                    **{k: v for k, v in d.items() if (k != "chetime" and k != "price")},
                }
                for d in opt_data_eurex_tmp
            ]
            opt_data_eurex[:0] = opt_data_eurex_tmp
        else:
            print("정의되지 않은 시간대")

        logger.info(f'{row["shcode"]} retrieved..')

    if opt_data_eurex:
        df_opt_data = pd.DataFrame(opt_data)
        df_opt_data_eurex = pd.DataFrame(opt_data_eurex)

        df_opt_data_combined = [df_opt_data, df_opt_data_eurex]
    else:
        df_opt_data = pd.DataFrame(opt_data)
        df_opt_data_combined = df_opt_data

    cd_rate = float(get_cd_rate().get("close")) / 100.0
    logger.info(f"cd rate from hist was {cd_rate} for past impvol calculation!! ")
    for i, df in enumerate(df_opt_data_combined):
        df["date_time"] = pd.to_datetime(
            df["date"].astype(str) + " " + df["time"].astype(str),
            format="%Y%m%d %H%M%S",
        )
        df["cd_rate"] = cd_rate

        df = pd.merge(  # TODO combined loop내에서 join for calc time
            left=df,
            right=df_fut_merged[["date_time", "close"]],
            on="date_time",
            suffixes=("", "_fut"),
        )

        df_opt_data_combined[i] = df[
            [
                "date_time",
                "shcode",
                "strike",
                "close",
                "close_fut",
                "high",
                "low",
                "cd_rate",
            ]
        ]

    df_opt_data_merged = pd.concat(
        [df_opt_data_combined[0], df_opt_data_combined[1]], axis=0
    )

    # implied vol 계산
    greeks = df_opt_data_merged.apply(lambda r: bs_greeks(r), axis=1)
    df_greeks = pd.DataFrame(
        greeks.tolist(), columns=["iv2", "delta2", "gamma2", "vega2", "theta2"]
    )

    df_opt_data_merged.reset_index(drop=True, inplace=True)
    df_opt_data_merged = pd.concat([df_opt_data_merged, df_greeks], axis=1)

    grouped = df_opt_data_merged.groupby(by="date_time")

    iv_20delta_list = []

    # 시간별로 계산하기
    for date_time, group in grouped:
        upper_option = group[group["delta2"] >= -0.2].nsmallest(1, "delta2")
        lower_option = group[group["delta2"] < -0.2].nlargest(1, "delta2")
        closest_option = group.iloc[(group["delta2"] + 0.2).abs().argsort()[:1]]

        try:
            upper_delta = upper_option["delta2"].values[0]
            lower_delta = lower_option["delta2"].values[0]
            upper_delta_vol = upper_option["iv2"].values[0]
            lower_delta_vol = lower_option["iv2"].values[0]

            iv_at_20delta = (
                (upper_delta - (-0.2)) * lower_delta_vol
                + (-0.2 - lower_delta) * upper_delta_vol
            ) / (upper_delta - lower_delta)

            iv_20delta_list.append(
                {
                    "date_time": date_time,
                    "iv_20": iv_at_20delta,
                    "option_code": closest_option["shcode"].iloc[0],
                    "option_price": closest_option["close"].iloc[0],
                    "option_delta": closest_option["delta2"].iloc[0],
                    "option_gamma": closest_option["gamma2"].iloc[0],
                    "option_vega": closest_option["vega2"].iloc[0],
                    "option_theta": closest_option["theta2"].iloc[0],
                    "future_code": focode,
                    "future_price": closest_option["close_fut"].iloc[0],
                }
            )
        except IndexError:
            logger.warning(f"데이터 문제 등으로 변동성 계산 실패 - {date_time}")
            continue

    rst = save_volatility_data(iv_20delta_list)
    logger.info(f"과거 변동성 데이터 저장 결과 - {rst}")
    return rst


if __name__ != "__main__":
    pass
