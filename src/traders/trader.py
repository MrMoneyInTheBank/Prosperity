# =========================================
# Auto-generated code for trader.py
# Generated on 2026-04-20 02:15:36
# =========================================

import json
import math
import typing as t
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import StrEnum
from operator import itemgetter

from datamodel import (
    Listing,
    Observation,
    Order,
    OrderDepth,
    ProsperityEncoder,
    Symbol,
    Trade,
    TradingState,
)


class Product(StrEnum):
    EMERALDS = "EMERALDS"
    TOMATOES = "TOMATOES"
    ASH_COATED_OSMIUM = "ASH_COATED_OSMIUM"
    INTARIAN_PEPPER_ROOT = "INTARIAN_PEPPER_ROOT"


POS_LIMITS: t.Final[dict[Product, int]] = {
    Product.EMERALDS: 80,
    Product.TOMATOES: 80,
    Product.ASH_COATED_OSMIUM: 80,
    Product.INTARIAN_PEPPER_ROOT: 80,
}


@dataclass(frozen=True)
class PreviousTradingState:
    midprice: t.Optional[float]
    ema: t.Optional[float]
    bid_quotes: int
    ask_quotes: int
    bid_fills: int
    ask_fills: int
    bid_fill_vol: int
    ask_fill_vol: int


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: t.Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(
        self,
        state: TradingState,
        orders: dict[Symbol, list[Order]],
        conversions: int,
        trader_data: str,
    ) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(
                        state, self.truncate(state.traderData, max_item_length)
                    ),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[t.Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[t.Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(
        self, order_depths: dict[Symbol, OrderDepth]
    ) -> dict[Symbol, list[t.Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[t.Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[t.Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[t.Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: t.Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        lo, hi = 0, min(len(value), max_length)
        out = ""

        while lo <= hi:
            mid = (lo + hi) // 2

            candidate = value[:mid]
            if len(candidate) < len(value):
                candidate += "..."

            encoded_candidate = json.dumps(candidate)

            if len(encoded_candidate) <= max_length:
                out = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        return out


class BaseTrader(ABC):
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

    @abstractmethod
    def get_orders(self) -> dict[str, list[Order]]:
        raise NotImplementedError()


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


class TomatoTrader(BaseTrader):
    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        super().__init__(product, trading_state, prev_state)

    def get_orders(self) -> dict[str, list[Order]]:
        if not (self.buy_anchor and self.ask_anchor and self.mid_anchor):
            return {self.product: []}
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
                make_ask = min(make_ask, sell_price)
                break

        self.bid(make_bid, self.max_allowed_buy_volume)
        self.ask(make_ask, self.max_allowed_sell_volume)

        return {self.product: self.orders}


class AshCoatedOsmiumTrader(BaseTrader):
    def __init__(
        self,
        product: Product,
        trading_state: TradingState,
        prev_state: t.Optional[PreviousTradingState],
    ) -> None:
        super().__init__(product, trading_state, prev_state)

    def get_orders(self) -> dict[str, list[Order]]:
        fair_price = self.ema

        if not fair_price:
            return {self.product: []}

        # arbitrage
        for ask_price, ask_vol in self.sell_orders.items():
            if ask_price < fair_price - 1:
                self.bid(ask_price, ask_vol)
                self.bid_quotes += 1
            elif ask_price <= fair_price and self.initial_position < 0:
                self.bid(ask_price, ask_vol)
                self.bid_quotes += 1

        for bid_price, bid_vol in self.buy_orders.items():
            if bid_price > fair_price + 1:
                self.ask(bid_price, bid_vol)
                self.ask_quotes += 1
            elif bid_price >= fair_price and self.initial_position > 0:
                self.ask(bid_price, bid_vol)
                self.ask_quotes += 1

        # market making
        if not self.buy_anchor or not self.ask_anchor:
            return {self.product: self.orders}

        make_bid = math.floor(self.buy_anchor + 1)
        make_ask = math.ceil(self.ask_anchor - 1)

        for bid_price, bid_vol in self.buy_orders.items():
            overbidding_price = bid_price + 1
            if bid_vol > 1 and overbidding_price < fair_price:
                make_bid = max(make_bid, overbidding_price)
                break
            elif bid_price < fair_price:
                make_bid = max(make_bid, bid_price)
                break
        for sell_price, sell_vol in self.sell_orders.items():
            underbidding_price = sell_price - 1
            if sell_vol > 1 and underbidding_price > fair_price:
                make_ask = min(make_ask, underbidding_price)
                break
            elif sell_price > fair_price:
                make_ask = min(make_ask, sell_price)
                break

        self.bid(make_bid, self.max_allowed_buy_volume)
        self.ask(make_ask, self.max_allowed_sell_volume)
        self.bid_quotes += 1
        self.ask_quotes += 1

        return {self.product: self.orders}


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


TRADERS: t.Final[dict[Product, t.Type[BaseTrader]]] = {
    Product.EMERALDS: EmeraldTrader,
    Product.TOMATOES: TomatoTrader,
    Product.ASH_COATED_OSMIUM: AshCoatedOsmiumTrader,
    Product.INTARIAN_PEPPER_ROOT: IntarianPepperRootTrader,
}

logger = Logger()


class Trader:
    def load_prev_trading_state(self, trader_data: str) -> t.Optional[dict[str, dict]]:
        try:
            return json.loads(trader_data)
        except json.JSONDecodeError:
            return None

    def get_product_prev_state(
        self, prev_state: t.Optional[dict[str, dict]], product: str
    ) -> t.Optional[PreviousTradingState]:
        if not prev_state or product not in prev_state:
            return None

        data = prev_state[product]
        try:
            return PreviousTradingState(**data)
        except (TypeError, ValueError):
            return None

    def serialize_trading_state(self, trader_data: dict[str, dict]) -> str:
        return json.dumps(trader_data)

    def bid(self) -> int:
        return 15

    def run(
        self, trading_state: TradingState
    ) -> t.Tuple[dict[str, list[Order]], int, str]:
        result: dict[str, list[Order]] = {}
        prev_trading_state = self.load_prev_trading_state(trading_state.traderData)

        trader_data: dict[str, dict] = {}

        for product, trader in TRADERS.items():
            if product in trading_state.order_depths:
                product_prev_state = self.get_product_prev_state(
                    prev_trading_state, product
                )
                trader_instance = trader(product, trading_state, product_prev_state)
                result.update(trader_instance.get_orders())
                trader_data[product] = asdict(trader_instance.save_current_state())

                logger.print(
                    f"{product} pos={trading_state.position.get(product, 0)} "
                    f"bids={len(trading_state.order_depths[product].buy_orders)} asks={len(trading_state.order_depths[product].sell_orders)} "
                    f"orders={len(result[product])}"
                )

        serialized_trader_data = self.serialize_trading_state(trader_data)
        conversions = 0

        logger.print(serialized_trader_data)

        logger.flush(trading_state, result, conversions, serialized_trader_data)
        return result, conversions, serialized_trader_data


# End of auto-generated trader.py
