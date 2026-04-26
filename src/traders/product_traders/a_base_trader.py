import typing as t
from operator import itemgetter

from datamodel import Order, OrderDepth, TradingState
from src.config.constants import POS_LIMITS, PreviousTradingState, Product


class BaseTrader:
    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        self.product = product
        self.trading_state = trading_state
        self.prev_state = prev_state

        self.orders: list[Order] = []
        self.position_limit = POS_LIMITS[self.product]
        self.initial_position = self.trading_state.position.get(self.product, 0)
        self.buy_orders, self.sell_orders = self.get_order_depths()
        self.best_bid, self.best_ask = self.get_best_quotes()
        self.midprice = self.get_midprice()
        self.buy_anchor, self.ask_anchor, self.mid_anchor = self.get_order_anchors()
        self.max_allowed_buy_volume, self.max_allowed_sell_volume = (
            self.get_max_allowed_volume()
        )

        self.bid_quotes = 0
        self.ask_quotes = 0

        self.ema_smoothing_factor = 0.26
        self.ema = self.calculate_ema()

    def get_order_depths(self) -> tuple[dict[int, int], dict[int, int]]:
        order_depth: OrderDepth = self.trading_state.order_depths[self.product]
        buy_orders = {
            bid_price: abs(bid_vol)
            for bid_price, bid_vol in sorted(
                order_depth.buy_orders.items(), key=itemgetter(0), reverse=True
            )
        }
        sell_orders = {
            ask_price: abs(ask_vol)
            for ask_price, ask_vol in sorted(
                order_depth.sell_orders.items(), key=itemgetter(0)
            )
        }

        return buy_orders, sell_orders

    def get_best_quotes(self) -> tuple[t.Optional[int], t.Optional[int]]:
        best_bid = max(self.buy_orders) if self.buy_orders else None
        best_ask = min(self.sell_orders) if self.sell_orders else None

        return best_bid, best_ask

    def get_order_anchors(
        self,
    ) -> tuple[t.Optional[int], t.Optional[int], t.Optional[int]]:
        if not self.buy_orders or not self.sell_orders:
            return None, None, None
        buy_anchor = min(self.buy_orders.keys())
        ask_anchor = max(self.sell_orders.keys())
        mid_anchor = (buy_anchor + ask_anchor) // 2

        return buy_anchor, ask_anchor, mid_anchor

    def get_midprice(self) -> t.Optional[float]:
        if not self.best_bid or not self.best_ask:
            if self.prev_state and self.prev_state.midprice is not None:
                return self.prev_state.midprice
            else:
                return None

        midprice: t.Final[float] = (self.best_bid + self.best_ask) / 2

        return midprice

    def get_microprice(self) -> t.Optional[float]:
        if self.best_bid is None or self.best_ask is None:
            return None

        bid_vol: int = self.buy_orders[self.best_bid]
        ask_vol: int = self.sell_orders[self.best_ask]
        total_vol: int = bid_vol + ask_vol

        cross_weighted_price_sum: int = (self.best_ask * bid_vol) + (
            self.best_bid * ask_vol
        )

        return cross_weighted_price_sum / total_vol

    def get_max_allowed_volume(self):
        max_allowed_buy_volume = self.position_limit - self.initial_position
        max_allowed_sell_volume = self.position_limit + self.initial_position
        return max_allowed_buy_volume, max_allowed_sell_volume

    def get_market_bid_ask_vol(self) -> tuple[int, int]:
        bid_vol = sum(self.buy_orders.values())
        ask_vol = sum(self.sell_orders.values())

        return bid_vol, ask_vol

    def get_market_imbalance(self) -> float:
        bid_vol, ask_vol = self.get_market_bid_ask_vol()
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

    def bid(self, price: int, volume: int) -> None:
        abs_volume = min(abs(int(volume)), self.max_allowed_buy_volume)
        order = Order(self.product, int(price), abs_volume)
        self.max_allowed_buy_volume -= abs_volume
        self.orders.append(order)

    def ask(self, price: int, volume: int) -> None:
        abs_volume = min(abs(int(volume)), self.max_allowed_sell_volume)
        order = Order(self.product, int(price), -abs_volume)
        self.max_allowed_sell_volume -= abs_volume
        self.orders.append(order)

    def get_filled_metrics(self) -> t.Tuple[int, int, int, int]:
        own_trades = self.trading_state.own_trades.get(self.product, [])
        bid_fills, bid_fill_vol = 0, 0
        ask_fills, ask_fill_vol = 0, 0

        for trade in own_trades:
            if trade.buyer == "SUBMISSION":
                bid_fills += 1
                bid_fill_vol += trade.quantity
            else:
                ask_fills += 1
                ask_fill_vol += trade.quantity

        return bid_fills, bid_fill_vol, ask_fills, ask_fill_vol

    def calculate_ema(self) -> t.Optional[float]:
        if self.midprice is None:
            return self.prev_state.ema if self.prev_state else None

        if not self.prev_state or self.prev_state.ema is None:
            return self.midprice

        return (
            self.ema_smoothing_factor * (self.midprice)
            + (1 - self.ema_smoothing_factor) * self.prev_state.ema
        )

    def save_current_state(self) -> PreviousTradingState:
        bid_fills, bid_fill_vol, ask_fills, ask_fill_vol = self.get_filled_metrics()
        if not self.prev_state:
            return PreviousTradingState(
                midprice=self.midprice,
                ema=self.ema,
                bid_quotes=self.bid_quotes,
                ask_quotes=self.ask_quotes,
                bid_fills=bid_fills,
                ask_fills=ask_fills,
                bid_fill_vol=bid_fill_vol,
                ask_fill_vol=ask_fill_vol,
            )
        else:
            return PreviousTradingState(
                midprice=self.midprice,
                ema=self.ema,
                bid_quotes=self.bid_quotes + self.prev_state.bid_quotes,
                ask_quotes=self.ask_quotes + self.prev_state.ask_quotes,
                bid_fills=bid_fills + self.prev_state.bid_fills,
                ask_fills=ask_fills + self.prev_state.ask_fills,
                bid_fill_vol=bid_fill_vol + self.prev_state.bid_fill_vol,
                ask_fill_vol=ask_fill_vol + self.prev_state.ask_fill_vol,
            )

    def get_orders(self) -> dict[str, list[Order]]:
        return {self.product: []}
