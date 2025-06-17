import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_sample_data():
    # 불연속적인 시간 데이터 생성
    times = []
    prices = []

    # 전날 오후 4시부터 데이터 생성
    current_time = datetime(2023, 1, 1, 16, 0)
    end_time = datetime(2023, 1, 2, 16, 0)

    while current_time <= end_time:
        # 새벽 5시부터 오전 9시까지 데이터 제외
        if not (
            datetime(2023, 1, 2, 5, 0) <= current_time < datetime(2023, 1, 2, 9, 0)
        ):
            times.append(current_time)
            prices.append(np.random.randint(1000, 1100))

        current_time += timedelta(minutes=1)

    # DataFrame 생성
    df = pd.DataFrame({"price": prices}, index=times)
    return df


def resample_and_interpolate(df):
    # 1분 간격으로 리샘플링하고 선형 보간
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="1min")
    df_resampled = df.reindex(full_range)
    df_interpolated = df_resampled.interpolate(method="linear")
    return df_interpolated


def calculate_moving_averages(df):
    df["MA_5"] = df["price"].rolling(window=5).mean()
    df["MA_90"] = df["price"].rolling(window=90).mean()
    df["MA_diff"] = df["MA_90"] - df["MA_5"]
    return df


def main():
    # 샘플 데이터 생성
    df = create_sample_data()
    print("원본 데이터 (처음 5행):")
    print(df.head())
    print("\n원본 데이터 (마지막 5행):")
    print(df.tail())

    # 리샘플링 및 보간
    df_interpolated = resample_and_interpolate(df)

    # 이동 평균 계산
    df_final = calculate_moving_averages(df_interpolated)

    # 결과 출력
    print("\n처리된 데이터 (9:00 - 9:10):")
    print(df_final.loc["2023-01-02 09:00:00":"2023-01-02 09:10:00"])


if __name__ == "__main__":
    main()
