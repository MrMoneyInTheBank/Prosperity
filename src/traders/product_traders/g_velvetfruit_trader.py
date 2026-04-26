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

    def calculate_indicators(self):

        indicators = {
            "ema_u_dev": None,
            "ema_o_dev": None,
            "mean_theo_diffs": {},
            "current_theo_diffs": {},
            "switch_means": {},
            "deltas": {},
            "vegas": {},
        }

        if self.underlying.wall_mid is not None:
            new_mean_price = self.calculate_ema(
                "ema_u", underlying_mean_reversion_window, self.underlying.wall_mid
            )
            indicators["ema_u_dev"] = self.underlying.wall_mid - new_mean_price

            new_mean_price = self.calculate_ema(
                "ema_o", options_mean_reversion_window, self.underlying.wall_mid
            )
            indicators["ema_o_dev"] = self.underlying.wall_mid - new_mean_price

            for option in self.options:
                k = int(option.name.split("_")[-1])

                if option.wall_mid is None:
                    if option.ask_wall is not None:
                        option.wall_mid = option.ask_wall - 0.5
                        option.bid_wall = option.ask_wall - 1
                        option.best_bid = option.ask_wall - 1
                    elif option.bid_wall is not None:
                        option.wall_mid = option.bid_wall + 0.5
                        option.ask_wall = option.bid_wall + 1
                        option.best_ask = option.bid_wall + 1

                if option.wall_mid is not None:
                    tte = (
                        1
                        - (
                            DAYS_PER_YEAR
                            - 8
                            + DAY
                            + self.state.timestamp // 100 / 10_000
                        )
                        / DAYS_PER_YEAR
                    )
                    underlying = (
                        self.underlying.best_bid * 0.5 + self.underlying.best_ask * 0.5
                    )
                    option_theo, option_delta, option_vega = self.get_option_values(
                        underlying, k, tte
                    )
                    option_theo_diff = option.wall_mid - option_theo

                    indicators["current_theo_diffs"][option.name] = option_theo_diff
                    indicators["deltas"][option.name] = option_delta
                    indicators["vegas"][option.name] = option_vega

                    new_mean_diff = self.calculate_ema(
                        f"{option.name}_theo_diff", THEO_NORM_WINDOW, option_theo_diff
                    )
                    indicators["mean_theo_diffs"][option.name] = new_mean_diff

                    new_mean_avg_dev = self.calculate_ema(
                        f"{option.name}_avg_devs",
                        IV_SCALPING_WINDOW,
                        abs(option_theo_diff - new_mean_diff),
                    )
                    indicators["switch_means"][option.name] = new_mean_avg_dev

        return indicators
