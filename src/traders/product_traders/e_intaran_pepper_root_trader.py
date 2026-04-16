import typing as t
from datamodel import Order, TradingState
from src.config.constants import PreviousTradingState
from src.traders.product_traders.a_base_trader import BaseTrader, Product


class IntarianPepperRootTrader(BaseTrader):
    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        super().__init__(product, trading_state, prev_state)

    def get_orders(self) -> dict[str, list[Order]]:
        if not self.best_ask:
            return {self.product: []}

        ask_vol = self.sell_orders[self.best_ask]
        self.bid(self.best_ask, ask_vol)

        return {self.product: self.orders}
