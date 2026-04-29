import math as m
from abc import ABC, abstractmethod

from scipy.stats import norm

from src.manual_trading.round4.constants import (
    AC_VOL_ANNUAL,
)


class BlackScholes(ABC):
    def __init__(self, sigma: float = AC_VOL_ANNUAL, r: float = 0):
        self.sigma = sigma
        self.r = r

    def _d1_d2(self, K: float, S: float, T: float) -> tuple[float, float]:
        sqrtT = m.sqrt(T)

        d1 = (m.log(S / K) + (self.r + 0.5 * self.sigma**2) * T) / (self.sigma * sqrtT)

        d2 = d1 - self.sigma * sqrtT

        return d1, d2

    def gamma(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return norm.pdf(d1) / (S * self.sigma * m.sqrt(T))

    def vega(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return S * norm.pdf(d1) * m.sqrt(T)

    @abstractmethod
    def price(self, K: float, S: float, T: float) -> float:
        raise NotImplementedError()


class BlackScholesCall(BlackScholes):
    def __init__(self, sigma: float = AC_VOL_ANNUAL, r: float = 0):
        super().__init__(sigma, r)

    def price(self, K: float, S: float, T: float) -> float:

        d1, d2 = self._d1_d2(K, S, T)

        return S * norm.cdf(d1) - K * m.exp(-self.r * T) * norm.cdf(d2)

    def delta(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return norm.cdf(d1)


class BlackScholesPut(BlackScholes):
    def __init__(self, sigma: float = AC_VOL_ANNUAL, r: float = 0):
        super().__init__(sigma, r)

    def price(self, K: float, S: float, T: float) -> float:

        d1, d2 = self._d1_d2(K, S, T)
        return K * m.exp(-self.r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    def delta(self, K: float, S: float, T: float) -> float:
        d1, _ = self._d1_d2(K, S, T)
        return -norm.cdf(d1)
