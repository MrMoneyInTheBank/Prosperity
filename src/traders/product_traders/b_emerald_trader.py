import typing as t

from datamodel import Order, TradingState
from src.config.constants import PreviousTradingState
from src.traders.product_traders.a_base_trader import BaseTrader, Product


class EmeraldTrader(BaseTrader):
    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        super().__init__(product, trading_state, prev_state)

    def get_orders(self) -> dict[str, list[Order]]:
        midprice = self.get_midprice()

        if not midprice:
            return {self.product: []}

        # pure arbitrage
        for ask_price, ask_vol in self.sell_orders.items():
            if ask_price <= midprice - 1:
                self.bid(ask_price, ask_vol)
            elif ask_price <= midprice and self.initial_position < 0:
                self.bid(ask_price, ask_vol)

        for bid_price, bid_vol in self.buy_orders.items():
            if bid_price >= midprice + 1:
                self.ask(bid_price, bid_vol)
            elif bid_price >= midprice and self.initial_position > 0:
                self.ask(bid_price, bid_vol)

        # market making
        if not self.buy_anchor or not self.ask_anchor:
            return {self.product: self.orders}

        make_bid = int(self.buy_anchor + 1)
        make_ask = int(self.ask_anchor - 1)

        for bid_price, bid_vol in self.buy_orders.items():
            overbidding_price = bid_price + 1
            if bid_vol > 1 and overbidding_price < midprice:
                make_bid = max(make_bid, overbidding_price)
                break
            elif bid_price < midprice:
                make_bid = max(make_bid, bid_price)
                break
        for sell_price, sell_vol in self.sell_orders.items():
            underbidding_price = sell_price - 1
            if sell_vol > 1 and underbidding_price > midprice:
                make_ask = min(make_ask, underbidding_price)
                break
            elif sell_price > midprice:
                make_ask = min(make_ask, sell_price)
                break

        self.bid(make_bid, self.max_allowed_buy_volume)
        self.ask(make_ask, self.max_allowed_sell_volume)

        return {self.product: self.orders}
