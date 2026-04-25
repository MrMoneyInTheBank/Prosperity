import math as m
import typing as t

from scipy.optimize import brentq
from scipy.stats import norm


class BlackScholesCall:
    def __init__(self, r: float, T_days: float):
        self.r = r  # risk-free rate
        self.T = T_days / 365  # time to expiry (in years)

    def _d1_d2(self, K: float, S: float, sigma: float) -> tuple[float, float]:
        if sigma <= 0 or self.T <= 0:
            return 0.0, 0.0

        sqrtT = m.sqrt(self.T)

        d1 = (m.log(S / K) + (self.r + 0.5 * sigma**2) * self.T) / (sigma * sqrtT)

        d2 = d1 - sigma * sqrtT

        return d1, d2

    def call_price(self, K: float, S: float, sigma: float) -> float:
        d1, d2 = self._d1_d2(K, S, sigma)

        return S * norm.cdf(d1) - K * m.exp(-self.r * self.T) * norm.cdf(d2)

    def delta(self, K: float, S: float, sigma: float) -> float:
        d1, _ = self._d1_d2(K, S, sigma)
        return norm.cdf(d1)

    def gamma(self, K: float, S: float, sigma: float) -> float:
        d1, _ = self._d1_d2(K, S, sigma)
        return norm.pdf(d1) / (S * sigma * m.sqrt(self.T))

    def vega(self, K: float, S: float, sigma: float) -> float:
        d1, _ = self._d1_d2(K, S, sigma)
        return S * norm.pdf(d1) * m.sqrt(self.T)

    def theta(self, K: float, S: float, sigma: float) -> float:
        d1, d2 = self._d1_d2(K, S, sigma)

        term1 = -S * norm.pdf(d1) * sigma / (2 * m.sqrt(self.T))
        term2 = -self.r * K * m.exp(-self.r * self.T) * norm.cdf(d2)

        return term1 + term2

    def rho(self, K: float, S: float, sigma: float) -> float:
        _, d2 = self._d1_d2(K, S, sigma)

        return K * self.T * m.exp(-self.r * self.T) * norm.cdf(d2)

    def implied_vol(
        self,
        C_market: float,
        K: float,
        S: float,
        sigma_low: float = 1e-6,
        sigma_high: float = 5.0,
    ) -> t.Optional[float]:

        intrinsic = max(0.0, S - K * m.exp(-self.r * self.T))
        if not (intrinsic <= C_market <= S):
            return None

        def f(sigma: float) -> float:
            return self.call_price(K, S, sigma) - C_market

        try:
            return brentq(f, sigma_low, sigma_high)
        except ValueError:
            return None
