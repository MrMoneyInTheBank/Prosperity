import math
import typing as t

from datamodel import Order, TradingState
from src.config.constants import PreviousTradingState
from src.traders.product_traders.a_base_trader import BaseTrader, Product


class HydrogelPackTrader(BaseTrader):
    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        super().__init__(product, trading_state, prev_state)

    def get_orders(self) -> dict[str, list[Order]]:
        if self.midprice is None or self.ema is None:
            return {self.product: self.orders}

        if self.midprice > self.ema:
            if self.prev_state and self.prev_state.midprice is not None:
                self.ask(math.ceil(self.midprice), 30)
        elif self.midprice < self.ema:
            if self.prev_state and self.prev_state.midprice is not None:
                self.bid(math.floor(self.midprice), 30)
        elif self.midprice == self.ema:
            if self.initial_position > 0:
                self.ask(math.ceil(self.midprice), self.max_allowed_sell_volume)
            elif self.initial_position > 0:
                self.bid(math.floor(self.midprice), self.max_allowed_buy_volume)

        return {self.product: self.orders}
