import math as m
import typing as t
from statistics import NormalDist

import numpy as np

from datamodel import TradingState
from src.config.constants import OPTIONS_CONTRACTS, PreviousTradingState, Product
from src.traders.product_traders.a_base_trader import BaseTrader


class OptionTrader:
    def __init__(
        self, trading_state: TradingState, prev_state: t.Optional[PreviousTradingState]
    ) -> None:
        self.options = [
            BaseTrader(opt_cont, trading_state=trading_state, prev_state=prev_state)
            for opt_cont in OPTIONS_CONTRACTS
        ]
        self.underlying = BaseTrader(
            Product.VELVETFRUIT_EXTRACT,
            trading_state=trading_state,
            prev_state=prev_state,
        )
        self.N = NormalDist()

    def get_option_values(self, spot_price, strike_price: int, TTE):

        def bs_call(spot_price, strike_price: int, TTE, sigma, r=0):
            d1 = (m.log(spot_price / strike_price) + (r + 0.5 * sigma**2) * TTE) / (
                sigma * TTE**0.5
            )
            d2 = d1 - sigma * TTE**0.5
            return spot_price * self.N.cdf(d1) - strike_price * m.exp(
                -r * TTE
            ) * self.N.cdf(d2), self.N.cdf(d1)

        def bs_vega(spot_price, strike_price, TTE, sigma, r=0):
            d1 = d1 = (
                m.log(spot_price / strike_price) + (r + 0.5 * sigma**2) * TTE
            ) / (sigma * TTE**0.5)
            return spot_price * self.N.pdf(d1) * TTE**0.5

        def get_iv(spot_price, strike_price, TTE):
            m_t_k = np.log(strike_price / spot_price) / TTE**0.5
            coeffs = [5.072685908964969, -0.6074819778933004, 0.2917365991488423]
            iv = np.poly1d(coeffs)(m_t_k)
            return iv

        iv = get_iv(spot_price, strike_price, TTE)
        bs_call_value, delta = bs_call(spot_price, strike_price, TTE, iv)
        vega = bs_vega(spot_price, strike_price, TTE, iv)
        return bs_call_value, delta, vega
