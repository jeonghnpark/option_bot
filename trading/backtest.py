# from django.test import TestCase

# Create your tests here.


import os
import sys  # for sys.exit()
import django

# Django 설정 모듈 경로 설정
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "mysite.settings"
)  # mysite는 프로젝트 이름에 맞게 변경하세요

# Django 설정 초기화
django.setup()

from trading.models import FuturesPrice
from django.utils import timezone
from datetime import datetime, timedelta

# Get today's date
today = timezone.now().date()

# Fetch today's FuturesPrice data
todays_futures_prices = FuturesPrice.objects.filter(timestamp__date=today)

# Check if data exists
if todays_futures_prices.exists():
    print(
        f"There are {todays_futures_prices.count()} futures price data entries for {today}."
    )
else:
    print(f"No futures price data found for {today}.")

import pandas as pd
import numpy as np

# 데이터프레임 생성
df = pd.DataFrame(list(todays_futures_prices.values()))

# print(df)

# price, bidho1, offerho1을 float로 변환
df["price"] = df["price"].astype(float)
df["bidho1"] = df["bidho1"].astype(float)
df["offerho1"] = df["offerho1"].astype(float)

# print("데이터 타입 변환 후:")
# print(df.dtypes)
# print("\n변환된 데이터프레임:")
# print(df)
# bidho1 또는 offerho1이 0인 행 제거
df = df[(df["bidho1"] != 0) & (df["offerho1"] != 0)]

# print("\n0 값이 제거된 데이터프레임:")
# print(df)

# 현재 시점부터 과거 5분 동안의 고가와 저가 계산
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)
df.sort_index(inplace=True)  # 시간순으로 정렬

# 롤링 윈도우를 사용하여 과거 5분 동안의 고가와 저가 계산
window = pd.Timedelta(minutes=5)
df["high_5min"] = df["price"].rolling(window=window).max()
df["low_5min"] = df["price"].rolling(window=window).min()

# 처음 5분 동안의 데이터를 NaN으로 설정
start_time = df.index[0]
mask = df.index < start_time + window
df.loc[mask, ["high_5min", "low_5min"]] = np.nan

# NaN 값 확인
# print("\n처음 10개 행:")
# print(df[["price", "high_5min", "low_5min"]].head(10))

# print("롤링 윈도우 적용 후:")
# print(df[["price", "high_5min", "low_5min"]].tail(10))

# print("resampled========================")
# pd.set_option("display.max_rows", None)

# Excel 파일로 저장
# excel_filename = f"futures_data_sample_{datetime.now().strftime('%H%M%S')}.xlsx"
# df[:10000].to_excel(excel_filename, index=True)
# print(
#     f"10000번째부터 30000번째 행까지의 데이터가 '{excel_filename}' 파일로 저장되었습니다."
# )


# sys.exit()

# 시간 측정 시작
import time

start_cal_time = time.time()


# 매수 신호 생성
df["price_range"] = df["high_5min"] - df["low_5min"]  # 1초 절약! for 37000 data size
df["buy_signal"] = (
    (df["price"] <= df["low_5min"] + df["price_range"] * 0.15)
    & (df["price"] >= df["low_5min"])
    & (~df["high_5min"].isna())
    & (~df["low_5min"].isna())
)


# 백테스트 함수 정의


def backtest_enhanced(df):
    trades = []

    # 매수 신호가 있는 인덱스만 추출
    df_with_buy_signal = df.loc[df["buy_signal"]]
    print(df_with_buy_signal)
    last_entry_time = df_with_buy_signal.index[0]
    for i, buy_signal_row in df_with_buy_signal.iterrows():
        if (
            i - last_entry_time
        ).total_seconds() >= 60:  # skip 60 seconds from last entry time
            forward_5min_data = df.loc[df.index >= i + timedelta(minutes=5)]
            if len(forward_5min_data) == 0:
                print(f"***************Not enough forward 5 min  data from {i}")
                break
            else:
                exit_time = forward_5min_data.index[0]
                exit_price = forward_5min_data["price"].iloc[0]
                profit = exit_price - buy_signal_row["price"]
                last_entry_time = i
                trades.append(
                    {
                        "entry_time": i,
                        "exit_time": exit_time,
                        "entry_price": buy_signal_row["price"],
                        "exit_price": exit_price,
                        "profit": profit,
                    }
                )

    #     entry_price = df.loc[entry_time, "price"]
    #     print(f"entry_price : {entry_price}")
    #     # exit_price = df.loc[exit_time, "price"]
    #     # profit = exit_price - entry_price

    #     # trades.append(
    #     #     {
    #     #         "entry_time": entry_time,
    #     #         "exit_time": exit_time,
    #     #         "entry_price": entry_price,
    #     #         "exit_price": exit_price,
    #     #         "profit": profit,
    #     #     }
    #     # )

    return trades


def backtest(df):
    # position = 0
    # entry_price = 0
    # entry_time = None
    trades = []

    last_entry_time = df.index[0]
    for index, row in df.iterrows():
        if row["buy_signal"] and (index - last_entry_time).total_seconds() >= 60:
            # look forward 5 minutes
            print(f"~~~~~~~~~~~~~~~price : {row['price']} {type(row['price'])}")
            for future_index, future_row in df.loc[index:].iterrows():
                if (future_index - index).total_seconds() >= 300:
                    trades.append(
                        {
                            "entry_time": index,
                            "exit_time": future_index,
                            "entry_price": row["price"],
                            "exit_price": future_row["price"],
                            "profit": future_row["price"] - row["price"],
                        }
                    )
                    last_entry_time = index
                    # row['entry']=1
                    # exit_price=future_row['price']
                    # row['pl']=exit_price-row['price'] #only buy the dip strategy
                    break

    # for index, row in df.iterrows():
    #     if position == 0 and row["buy_signal"]:
    #         position = 1
    #         entry_price = row["price"]
    #         entry_time = index
    #     elif (
    #         position == 1 and (index - entry_time).total_seconds() >= 300
    #     ):  # 5분(300초) 후 청산
    #         exit_price = row["price"]
    #         profit = exit_price - entry_price
    #         trades.append(
    #             {
    #                 "entry_time": entry_time,
    #                 "exit_time": index,
    #                 "entry_price": entry_price,
    #                 "exit_price": exit_price,
    #                 "profit": profit,
    #             }
    #         )
    #         position = 0

    return trades


# 백테스트 실행
# trades = backtest(df)
trades = backtest_enhanced(df)


end_cal_time = time.time()
total_cal_time = end_cal_time - start_cal_time

# 결과 분석
print(f"all  trades ******\n{trades}")
if trades:
    total_profit = sum(trade["profit"] for trade in trades)
    num_trades = len(trades)
    win_rate = sum(1 for trade in trades if trade["profit"] > 0) / num_trades
    print(f"코드 실행 시간: {total_cal_time:.2f}초")
    print(f"총 거래 횟수: {num_trades}")
    print(f"총 수익: {total_profit:.2f}")
    profit_std = np.std([trade["profit"] for trade in trades])
    print(f"수익 표준편차: {profit_std:.2f}")
    print(f"승률: {win_rate:.2%}")
    print(f"평균 수익: {total_profit / num_trades:.2f}")
else:
    print("거래가 없습니다.")

sys.exit()
# 결과 시각화
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.font_manager as fm

# 한글 폰트 설정
font_path = (
    "C:\\Windows\\Fonts\\NanumGothic.ttf"  # 경로는 시스템에 따라 다를 수 있습니다
)
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()

# 거래 데이터를 DataFrame으로 변환
trades_df = pd.DataFrame(trades)

# 누적 수익 계산
trades_df["누적_수익"] = trades_df["profit"].cumsum()

# 시각화
fig, ax1 = plt.subplots(figsize=(12, 6))

# 가격 그래프
ax1.plot(df.index, df["price"], color="blue", alpha=0.6, label="가격")
ax1.set_xlabel("시간")
ax1.set_ylabel("가격", color="blue")
ax1.tick_params(axis="y", labelcolor="blue")

# 진입 시점 표시
for entry_time in trades_df["entry_time"]:
    ax1.axvline(x=entry_time, color="green", linestyle="--", alpha=0.5)

# 누적 수익 그래프
ax2 = ax1.twinx()
ax2.plot(
    trades_df["exit_time"],
    trades_df["누적_수익"],
    color="red",
    marker="o",
    label="누적 수익",
)
ax2.set_ylabel("누적 수익", color="red")
ax2.tick_params(axis="y", labelcolor="red")

plt.title("가격, 진입 시점, 누적 수익 시각화")
fig.tight_layout()
plt.grid(True, alpha=0.3)

# 범례 표시
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

# 그래프 저장
plt.savefig("trading_visualization.png")
print("거래 시각화 그래프가 'trading_visualization.png'로 저장되었습니다.")

# 그래프 표시
plt.show()

# # 거래 내역 출력 (처음 5개만)
# for trade in trades[:]:
#     print(f"진입 시간: {trade['entry_time']}, 진입 가격: {trade['entry_price']:.2f}")
#     print(f"청산 시간: {trade['exit_time']}, 청산 가격: {trade['exit_price']:.2f}")
#     print(f"수익: {trade['profit']:.2f}")
#     print("---")

#     # 시간에 따른 profit 시각화
#     import matplotlib.pyplot as plt
#     import pandas as pd

#     # 거래 데이터를 DataFrame으로 변환
#     trades_df = pd.DataFrame(trades)

#     # 누적 수익 계산
#     trades_df["cumulative_profit"] = trades_df["profit"].cumsum()

#     # 시각화
#     plt.figure(figsize=(12, 6))
#     plt.plot(trades_df["exit_time"], trades_df["cumulative_profit"], marker="o")
#     plt.title("시간에 따른 누적 수익")
#     plt.xlabel("시간")
#     plt.ylabel("누적 수익")
#     plt.grid(True)
#     plt.xticks(rotation=45)
#     plt.tight_layout()

#     # 그래프 저장
#     plt.savefig("cumulative_profit.png")
#     print("누적 수익 그래프가 'cumulative_profit.png'로 저장되었습니다.")

#     # 그래프 표시
#     plt.show()
