import math
import typing as t
from datamodel import Order, TradingState
from src.config.constants import PreviousTradingState
from src.traders.product_traders.a_base_trader import BaseTrader, Product


class AshCoatedOsmiumTrader(BaseTrader):
    inventory_risk: float = 0.1
    half_spread: float = 1.0

    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        super().__init__(product, trading_state, prev_state)

    def get_reservation_price(self) -> float:
        assert self.midprice is not None
        return self.midprice - (self.inventory_risk * self.initial_position)

    def get_orders(self) -> dict[str, list[Order]]:
        if not self.midprice:
            return {self.product: self.orders}

        reservation_price = self.get_reservation_price()

        for ask_price, ask_vol in self.sell_orders.items():
            if ask_price < reservation_price:
                self.bid(ask_price, ask_vol)

        for bid_price, bid_vol in self.buy_orders.items():
            if bid_price > reservation_price:
                self.ask(bid_price, bid_vol)

        bid_price = math.floor(reservation_price - self.half_spread)
        ask_price = math.ceil(reservation_price + self.half_spread)

        bid_vol = self.max_allowed_buy_volume * (
            1 - (self.initial_position / self.position_limit)
        )
        ask_vol = self.max_allowed_sell_volume * (
            1 + (self.initial_position / self.position_limit)
        )

        self.bid(bid_price, int(bid_vol))
        self.ask(ask_price, int(ask_vol))

        return {self.product: self.orders}
