# =========================================
# Auto-generated code for trader.py
# Generated on 2026-03-30 20:58:46
# =========================================

import typing as t
from abc import ABC, abstractmethod
from enum import StrEnum
from operator import itemgetter

from datamodel import Order, OrderDepth, TradingState


class Product(StrEnum):
    EMERALDS = "EMERALDS"
    TOMATOES = "TOMATOES"


POS_LIMITS: t.Final[dict[Product, int]] = {Product.EMERALDS: 80, Product.TOMATOES: 80}


class BaseTrader(ABC):
    def __init__(self, product: Product, trading_state: TradingState) -> None:
        self.product = product
        self.trading_state = trading_state

        self.orders: list[Order] = []
        self.position_limit = POS_LIMITS[self.product]
        self.initial_position = self.trading_state.position.get(self.product, 0)
        self.buy_orders, self.sell_orders = self.get_order_depths()
        self.best_bid, self.best_ask = self.get_best_quotes()
        self.buy_anchor, self.ask_anchor, self.mid_anchor = self.get_order_anchors()
        self.max_allowed_buy_volume, self.max_allowed_sell_volume = (
            self.get_max_allowed_volume()
        )

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

    def get_order_anchors(self) -> tuple[int, int, int]:
        buy_anchor = min(self.buy_orders.keys())
        ask_anchor = max(self.sell_orders.keys())
        mid_anchor = (buy_anchor + ask_anchor) // 2

        return buy_anchor, ask_anchor, mid_anchor

    def get_microprice(self) -> t.Optional[float]:
        if not self.best_bid or not self.best_ask:
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

    def bid(self, price, volume) -> None:
        abs_volume = min(abs(int(volume)), self.max_allowed_buy_volume)
        order = Order(self.product, int(price), abs_volume)
        self.max_allowed_buy_volume -= abs_volume
        self.orders.append(order)

    def ask(self, price, volume) -> None:
        abs_volume = min(abs(int(volume)), self.max_allowed_sell_volume)
        order = Order(self.product, int(price), -abs_volume)
        self.max_allowed_sell_volume -= abs_volume
        self.orders.append(order)

    @abstractmethod
    def get_orders(self) -> dict[str, list[Order]]:
        raise NotImplementedError()


class EmeraldTrader(BaseTrader):
    def __init__(self, product: Product, trading_state: TradingState) -> None:
        super().__init__(product, trading_state)

    def get_orders(self) -> dict[str, list[Order]]:
        # pure arbitrage
        for ask_price, ask_vol in self.sell_orders.items():
            if ask_price <= self.mid_anchor - 1:
                self.bid(ask_price, ask_vol)
            elif ask_price <= self.mid_anchor and self.initial_position < 0:
                self.bid(ask_price, ask_vol)

        for bid_price, bid_vol in self.buy_orders.items():
            if bid_price >= self.mid_anchor + 1:
                self.ask(bid_price, bid_vol)
            elif bid_price >= self.mid_anchor and self.initial_position > 0:
                self.ask(bid_price, bid_vol)

        # market making
        make_bid = int(self.buy_anchor + 1)
        make_ask = int(self.ask_anchor - 1)

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
                ask_price = min(make_ask, sell_price)
                break

        self.bid(make_bid, self.max_allowed_buy_volume)
        self.ask(make_ask, self.max_allowed_sell_volume)

        return {self.product: self.orders}


class TomatoTrader(BaseTrader):
    def __init__(self, product: Product, trading_state: TradingState) -> None:
        super().__init__(product, trading_state)

    def get_orders(self) -> dict[str, list[Order]]:

        alpha = 0.3
        fair_price = (
            self.mid_anchor
            if (mp := self.get_microprice()) is None
            else self.mid_anchor + alpha * (mp - self.mid_anchor)
        )

        # pure arbitrage
        for ask_price, ask_vol in self.sell_orders.items():
            if ask_price <= fair_price - 1:
                self.bid(ask_price, ask_vol)
            elif ask_price <= self.mid_anchor and self.initial_position < 0:
                self.bid(ask_price, ask_vol)

        for bid_price, bid_vol in self.buy_orders.items():
            if bid_price >= fair_price + 1:
                self.ask(bid_price, bid_vol)
            elif bid_price >= self.mid_anchor and self.initial_position > 0:
                self.ask(bid_price, bid_vol)

        # market making
        make_bid = int(self.buy_anchor + 1)
        make_ask = int(self.ask_anchor - 1)

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


TRADERS: t.Final[dict[Product, t.Type[BaseTrader]]] = {
    Product.EMERALDS: EmeraldTrader,
    Product.TOMATOES: TomatoTrader,
}


class Trader:
    def run(self, trading_state: TradingState):
        result: dict[str, list[Order]] = {}

        for product, trader in TRADERS.items():
            if product in trading_state.order_depths:
                trader_instance = trader(product, trading_state)
                result.update(trader_instance.get_orders())

        return result, 0, ""


# End of auto-generated trader.py
