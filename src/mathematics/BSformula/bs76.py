from scipy.interpolate import interp1d

# from scipy import sqrt, log, exp
from numpy import sqrt, log, exp
from scipy.stats import norm
from scipy.optimize import fsolve

from mathematics.BSformula.constants import *
from datetime import datetime as dt_t


class BS76:
    def __init__(
        self, F: float, K: float, T: float, price: float, r: float, option: str
    ):
        self.F, self.K, self.T, self.option = F, K, T, option
        self.r = r
        self.opt_price = price
        self.impvol = self.implied_volatility()

    @staticmethod
    def _BlackScholesCall(F, K, T, sigma, r):
        sigma_sqrtT = sigma * sqrt(T)
        d1 = log(F / K) / sigma_sqrtT + sigma_sqrtT / 2
        d2 = d1 - sigma_sqrtT
        return exp(-r * T) * (norm.cdf(d1) * F - norm.cdf(d2) * K)

    @staticmethod
    def _BlackScholesPut(F, K, T, sigma, r):
        c = BS76._BlackScholesCall(F, K, T, sigma, r)
        return c - (F - K) * exp(-r * T)

    def _fprime(self, sigma):
        logSoverK = log(self.F / self.K)
        n12 = (self.r + sigma**2 / 2) * self.T
        numerd1 = logSoverK + n12
        d1 = numerd1 / (sigma * sqrt(self.T))
        return self.F * sqrt(self.T) * norm.pdf(d1) * exp(-self.r * self.T)

    def BS(self, F, K, T, sigma, r):
        if self.option == "Call":
            return self._BlackScholesCall(F, K, T, sigma, r)
        elif self.option == "Put":
            return self._BlackScholesPut(F, K, T, sigma, r)

    def implied_volatility(self):
        impvol = lambda x: self.BS(self.F, self.K, self.T, x, self.r) - self.opt_price
        iv = fsolve(
            impvol,
            SOLVER_STARTING_VALUE,
            fprime=self._fprime,
            xtol=IMPLIED_VOLATILITY_TOLERANCE,
        )

        return iv[0]

    def delta(self):
        h = DELTA_DIFFERENTIAL
        p1 = self.BS(self.F + h, self.K, self.T, self.impvol, self.r)
        p2 = self.BS(self.F - h, self.K, self.T, self.impvol, self.r)
        return (p1 - p2) / (2 * h)

    def gamma(self):
        h = GAMMA_DIFFERENTIAL
        p1 = self.BS(self.F + h, self.K, self.T, self.impvol, self.r)
        p2 = self.BS(
            self.F,
            self.K,
            self.T,
            self.impvol,
            self.r,
        )
        p3 = self.BS(
            self.F - h,
            self.K,
            self.T,
            self.impvol,
            self.r,
        )
        return (p1 - 2 * p2 + p3) / (h**2)

    def vega(self):
        h = VEGA_DIFFERENTIAL
        p1 = self.BS(
            self.F,
            self.K,
            self.T,
            self.impvol + h,
            self.r,
        )
        p2 = self.BS(
            self.F,
            self.K,
            self.T,
            self.impvol - h,
            self.r,
        )
        return (p1 - p2) / (2 * h * 100)  # percent vega

    def theta(self):
        h = THETA_DIFFERENTIAL
        p1 = self.BS(self.F, self.K, self.T + h, self.impvol, self.r)
        p2 = self.BS(self.F, self.K, self.T - h, self.impvol, self.r)
        return (p1 - p2) / (2 * h * 365)

    def rho(self):
        h = RHO_DIFFERENTIAL
        p1 = self.BS(self.F, self.K, self.T, self.impvol, self.r + h)
        p2 = self.BS(self.F, self.K, self.T, self.impvol, self.r - h)
        return (p1 - p2) / (2 * h * 100)


def bs_greeks(row):
    """
    필드명
    close_fut : 선물가격

    strike : 행사가
    close :옵션가격

    shcode : 상품코드
    cd_rate: 무위험금리
    #TODO: expiry_datetime : 만기정보
    """

    expiry_info = {
        "W7": "2025-7-10 15:45:00",
        "W5": "2025-5-8 15:45:00",
        "W4": "2025-4-10 15:45:00",
        "W3": "2025-3-13 15:45:00",
        "W2": "2025-2-13 15:45:00",
        "W1": "2025-1-9 15:45:00",
        "VC": "2024-12-12 15:45:00",
        "VB": "2024-11-14 15:45:00",
    }
    # print(f"calculating vol of {row['shcode']} when {row['date_time']}")
    expiry_str = expiry_info[row["shcode"][3:5]]
    expiry_datetime = dt_t.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")

    # 잔존 기간 계산
    time_to_maturity = (expiry_datetime - row["date_time"]).total_seconds() / (
        365 * 24 * 3600
    )
    F = float(row["close_fut"])
    K = float(row["strike"])
    prc = float(row["close"])

    cd_rate = float(row["cd_rate"])

    if row["shcode"][:3] == "201":
        bs = BS76(F, K, time_to_maturity, prc, cd_rate, option="Call")
        return (bs.impvol, bs.delta(), bs.gamma(), bs.vega(), bs.theta())

    elif row["shcode"][:3] == "301":
        bs = BS76(F, K, time_to_maturity, prc, cd_rate, option="Put")
        return (bs.impvol, bs.delta(), bs.gamma(), bs.vega(), bs.theta())


def bs_greeks_mid(row):
    """
    필드명
    close_fut : 선물 미드

    strike : 행사가
    close :옵션가격
    bidho1: 옵션 비드
    offerho1: 옵션 오퍼
    shcode : 상품코드
    cd_rate: 무위험금리
    #TODO: expiry_datetime : 만기정보
    """

    expiry_info = {
        "W7": "2025-7-10 15:45:00",
        "W5": "2025-5-8 15:45:00",
        "W4": "2025-4-10 15:45:00",
        "W3": "2025-3-13 15:45:00",
        "W2": "2025-2-13 15:45:00",
        "W1": "2025-1-9 15:45:00",
        "VC": "2024-12-12 15:45:00",
        "VB": "2024-11-14 15:45:00",
    }
    # print(f"calculating vol of {row['shcode']} when {row['date_time']}")
    expiry_str = expiry_info[row["shcode"][3:5]]
    expiry_datetime = dt_t.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")

    # 잔존 기간 계산
    time_to_maturity = (expiry_datetime - row["date_time"]).total_seconds() / (
        365 * 24 * 3600
    )
    F = float(row["close_fut"])  # 실제는 mid임
    K = float(row["strike"])
    # prc = float(row["close"])
    prc = float(row["bidho1"]) / 2 + float(row["offerho1"]) / 2

    cd_rate = float(row["cd_rate"])

    if row["shcode"][:3] == "201":
        bs = BS76(F, K, time_to_maturity, prc, cd_rate, option="Call")
        return (bs.impvol, bs.delta(), bs.gamma(), bs.vega(), bs.theta())

    elif row["shcode"][:3] == "301":
        bs = BS76(F, K, time_to_maturity, prc, cd_rate, option="Put")
        return (bs.impvol, bs.delta(), bs.gamma(), bs.vega(), bs.theta())
