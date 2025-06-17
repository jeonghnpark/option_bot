import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from tr.futures.chart.t8415 import get_hist_fut


def collect_historical_data(shcode, start_date, end_date):
    data = get_hist_fut(shcode, 1, start_date, end_date)
    df = pd.DataFrame(data)
    df["date_time"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str), format="%Y%m%d %H%M%S"
    )
    df.drop(["date", "time"], axis=1, inplace=True)
    df.sort_values(by="date_time", inplace=True)
    df[["close", "high", "low"]] = df[["close", "high", "low"]].astype(float)
    print(df)
    return df


def prepare_features(df, period, buydip_threshold):
    df["price_range"] = (
        df["high"].rolling(window=period).max() - df["low"].rolling(window=period).min()
    )
    df["lower_threshold"] = (
        df["low"].rolling(window=period).min()
        + df["price_range"] * buydip_threshold / 100
    )
    df["buydip_condition"] = df["close"] <= df["lower_threshold"]
    df["future_return"] = df["close"].pct_change(periods=5).shift(-5)  # 5분 후의 수익률
    return df.dropna()


def optimize_parameters(shcode, start_date, end_date):
    df = collect_historical_data(shcode, start_date, end_date)

    # 파라미터 그리드 정의
    param_grid = {
        "period": [5, 10, 15, 20],
        "buydip_threshold": [5, 10, 15, 20],
        "liquidation_delay": [1, 3, 5, 10],
    }

    # 특성 및 타겟 준비
    X = []
    y = []

    for period in param_grid["period"]:
        for buydip_threshold in param_grid["buydip_threshold"]:
            prepared_df = prepare_features(df.copy(), period, buydip_threshold)
            X.append(
                prepared_df[prepared_df["buydip_condition"]][
                    ["close", "lower_threshold", "price_range"]
                ]
            )
            y.append(prepared_df[prepared_df["buydip_condition"]]["future_return"])

    X = pd.concat(X)
    y = pd.concat(y)

    print(X, y)

    # # 랜덤 포레스트 모델 및 그리드 서치 설정
    # model = RandomForestRegressor(n_estimators=100, random_state=42)
    # grid_search = GridSearchCV(
    #     estimator=model, param_grid=param_grid, cv=5, scoring="neg_mean_squared_error"
    # )

    # # 그리드 서치 수행
    # grid_search.fit(X, y)

    # # 최적 파라미터 반환
    # return grid_search.best_params_
    return None


# 최적 파라미터 찾기
shcode = "105VA000"  # 코스피200 선물 코드
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
end_date = datetime.now().strftime("%Y%m%d")

optimal_params = optimize_parameters(shcode, end_date, end_date)
print("최적 파라미터:", optimal_params)
