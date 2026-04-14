from datamodel import Order, TradingState
from src.traders.product_traders.a_base_trader import BaseTrader, Product


class IntarianPepperRootTrader(BaseTrader):
    def __init__(self, product: Product, trading_state: TradingState) -> None:
        super().__init__(product, trading_state)

    def get_orders(self) -> dict[str, list[Order]]:
        return {self.product: []}
