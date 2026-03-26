import json
import typing as t

# Type aliases
Time = int
Position = int
Symbol = str
Product = str
UserId = str


class Listing:
    def __init__(self, symbol: Symbol, product: Product, denomination: str) -> None:
        self.symbol = symbol
        self.product = product
        self.denomination = denomination


class Order:
    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

    def __str__(self) -> str:
        return f"({self.symbol}, {self.price}, {self.quantity})"

    def __repr__(self) -> str:
        return f"({self.symbol}, {self.price}, {self.quantity})"


class OrderDepth:
    def __init__(self) -> None:
        self.buy_orders: dict[int, int] = {}
        self.sell_orders: dict[int, int] = {}


class Trade:
    def __init__(
        self,
        symbol: Symbol,
        price: int,
        quantity: int,
        buyer: t.Optional[UserId] = None,
        seller: t.Optional[UserId] = None,
        timestamp: Time = 0,
    ) -> None:
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    def __str__(self) -> str:
        return f"({self.symbol}, {self.buyer} << {self.seller}, {self.price}, {self.quantity}, {self.timestamp})"

    def __repr__(self) -> str:
        return f"({self.symbol}, {self.buyer} << {self.seller}, {self.price}, {self.quantity}, {self.timestamp})"


class Observation:
    pass


class TradingState(object):
    def __init__(
        self,
        traderData: str,
        timestamp: Time,
        listings: dict[Symbol, Listing],
        order_depths: dict[Symbol, OrderDepth],
        own_trades: dict[Symbol, list[Trade]],
        market_trades: dict[Symbol, list[Trade]],
        position: dict[Product, Position],
        observations: Observation,
    ) -> None:
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations

    def toJSON(self):
        return json.dumps(self, default=lambda obj: obj.__dict__, sort_keys=True)
