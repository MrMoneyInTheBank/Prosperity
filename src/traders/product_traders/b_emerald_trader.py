from datamodel import Order, TradingState
from src.traders.product_traders.a_base_trader import BaseTrader, Product


class EmeraldTrader(BaseTrader):
    def __init__(self, product: Product, trading_state: TradingState) -> None:
        super().__init__(product, trading_state)

    def get_orders(self) -> dict[str, list[Order]]:
        # pure arbitrage
        if not self.best_bid or not self.best_ask:
            return {self.product: []}

        alpha = 0.3
        beta = 0.4
        microprice = self.get_microprice()
        midprice = self.get_midprice()
        imbalance = self.get_market_imbalance()
        imbalance_adj = beta * imbalance

        assert microprice is not None
        assert midprice is not None

        fair_price = (midprice + alpha * (microprice - midprice)) + imbalance_adj
        delta = 1

        for ask_price, ask_vol in self.sell_orders.items():
            if ask_price <= fair_price - delta and microprice > midprice:
                self.bid(ask_price, ask_vol)
            elif ask_price <= fair_price and self.initial_position < 0:
                self.bid(ask_price, ask_vol)

        for bid_price, bid_vol in self.buy_orders.items():
            if bid_price >= fair_price + delta and microprice < midprice:
                self.ask(bid_price, bid_vol)
            elif bid_price >= fair_price and self.initial_position > 0:
                self.ask(bid_price, bid_vol)

        # market making
        position = self.initial_position
        base_spread = 2
        k = 0.1
        spread = base_spread + k * abs(position)

        inventory_skew = 0.2 * position

        make_bid = int(fair_price - spread / 2 - inventory_skew)
        make_ask = int(fair_price + spread / 2 - inventory_skew)

        for bid_price, bid_vol in self.buy_orders.items():
            overbidding_price = bid_price + 1
            if bid_vol > 1 and overbidding_price < self.mid_anchor:
                make_bid = max(make_bid, overbidding_price)
                break
            elif bid_price < self.mid_anchor:
                make_bid = max(make_bid, bid_price)
                break
        for sell_price, sell_vol in self.sell_orders.items():
            underbidding_price = sell_price - 1
            if sell_vol > 1 and underbidding_price > self.mid_anchor:
                make_ask = min(make_ask, underbidding_price)
                break
            elif sell_price > self.mid_anchor:
                make_ask = min(make_ask, sell_price)
                break

        self.bid(make_bid, self.max_allowed_buy_volume)
        self.ask(make_ask, self.max_allowed_sell_volume)

        return {self.product: self.orders}
