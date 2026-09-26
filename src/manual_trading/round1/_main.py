from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from rich.console import Console
from rich.table import Table

#################################################################
## CONSTANTS / DATA TYPES #######################################
#################################################################


class Product(StrEnum):
    DRYLAND_FLAX = "DRYLAND_FLAX"
    EMBER_MUSHROOM = "EMBER_MUSHROOM"


class Side(StrEnum):
    BID = "BID"
    ASK = "ASK"


@dataclass
class Order:
    side: Side
    price: int
    quantity: int


DRYLAND_FLAX_BIDS: Final[list[Order]] = [
    Order(Side.BID, 30, 30_000),
    Order(Side.BID, 29, 5_000),
    Order(Side.BID, 28, 12_000),
    Order(Side.BID, 27, 28_000),
]

DRYLAND_FLAX_ASKS: Final[list[Order]] = [
    Order(Side.ASK, 28, 40_000),
    Order(Side.ASK, 31, 20_000),
    Order(Side.ASK, 32, 20_000),
    Order(Side.ASK, 33, 30_000),
]

EMBER_MUSHROOM_BIDS: Final[list[Order]] = [
    Order(Side.BID, 20, 43_000),
    Order(Side.BID, 19, 17_000),
    Order(Side.BID, 18, 6_000),
    Order(Side.BID, 17, 5_000),
    Order(Side.BID, 16, 10_000),
    Order(Side.BID, 15, 5_000),
    Order(Side.BID, 14, 10_000),
    Order(Side.BID, 13, 7_000),
]

EMBER_MUSHROOM_ASKS: Final[list[Order]] = [
    Order(Side.ASK, 12, 20_000),
    Order(Side.ASK, 13, 25_000),
    Order(Side.ASK, 14, 50_000),
    Order(Side.ASK, 15, 6_000),
    Order(Side.ASK, 16, 5_000),
    Order(Side.ASK, 17, 0),
    Order(Side.ASK, 18, 18_000),
    Order(Side.ASK, 19, 12_000),
]

DRYLAND_FLAX_MAX_QTY = 50_000
EMBER_MUSHROOM_MAX_QTY = 75_000

DRYLAND_FLAX_BUYBACK_PER_UNIT = 30
EMBER_MUSHROOM_BUYBACK_PER_UNIT = 20

EMBER_MUSHROOM_FEES_PER_UNIT = 0.1


#################################################################
## ORDERBOOK + REGISTRY #########################################
#################################################################


class OrderBook:
    def __init__(self, product: Product) -> None:
        self.product = product
        self.orders: dict[int, dict[Side, list[Order]]] = {}
        self.bids: list[Order] = []
        self.asks: list[Order] = []
        self.order_submitted: bool = False

    def add_bids(self, bids: list[Order]) -> None:
        for bid in bids:
            if bid.side != Side.BID:
                raise ValueError(f"Order {bid} is not a bid order.")

            if bid.price not in self.orders:
                self.orders[bid.price] = {Side.BID: [], Side.ASK: []}

            self.orders[bid.price][Side.BID].append(bid)

    def add_asks(self, asks: list[Order]) -> None:
        for ask in asks:
            if ask.side != Side.ASK:
                raise ValueError(f"Order {ask} is not an ask order.")

            if ask.price not in self.orders:
                self.orders[ask.price] = {Side.BID: [], Side.ASK: []}

            self.orders[ask.price][Side.ASK].append(ask)

    @classmethod
    def construct_orderbook(
        cls, product: Product, bids: list[Order], asks: list[Order]
    ) -> "OrderBook":
        orderbook: OrderBook = OrderBook(product)
        try:
            orderbook.add_bids(bids)
            orderbook.add_asks(asks)
            return orderbook
        except ValueError as e:
            raise ValueError(e)

    def submit_order(self, order: Order) -> None:
        if order.price not in self.orders:
            self.orders[order.price] = {Side.BID: [], Side.ASK: []}

        if order.side == Side.BID:
            self.orders[order.price][Side.BID].append(order)
            self.order_submitted = True
        elif order.side == Side.ASK:
            self.orders[order.price][Side.ASK].append(order)
            self.order_submitted = True
        else:
            raise ValueError(f"Invalid order: {order}")

    def calculate_clearing_price(self) -> int:
        if not self.order_submitted:
            raise PermissionError(
                "Cannot calculate clearing price before submitting order."
            )

        prices = sorted(self.orders.keys())
        clearing_price, max_traded_volume = None, 1

        for p in prices:
            bid_vol = 0
            ask_vol = 0

            for price in self.orders.keys():
                if price >= p:
                    bid_vol += sum(b.quantity for b in self.orders[price][Side.BID])
                if price <= p:
                    ask_vol += sum(a.quantity for a in self.orders[price][Side.ASK])

            traded_volume = min(bid_vol, ask_vol)

            if traded_volume >= max_traded_volume:
                clearing_price = (
                    max(clearing_price, p) if clearing_price is not None else p
                )
                max_traded_volume = traded_volume

        assert clearing_price is not None
        return clearing_price


class OrderBookRegistry:
    _books: dict[Product, OrderBook] = {}

    @classmethod
    def initialize(
        cls, product: Product, bids: list[Order], asks: list[Order]
    ) -> OrderBook:
        if product in cls._books:
            raise ValueError(f"{product} already initialized")

        ob = OrderBook.construct_orderbook(product, bids, asks)
        cls._books[product] = ob
        return ob

    @classmethod
    def get(cls, product: Product) -> OrderBook:
        if product not in cls._books:
            raise ValueError(f"{product} not initialized")

        return cls._books[product]

    @classmethod
    def clear(cls) -> None:
        cls._books.clear()

    @classmethod
    def print_orderbooks(cls, console: Console | None = None) -> None:
        """Print each orderbook with quantities aggregated by price level."""
        if console is None:
            console = Console()

        for product, orderbook in cls._books.items():
            table = Table(title=f"{product} Orderbook")
            table.add_column("Bid Qty", justify="center")
            table.add_column("Price", justify="center", style="bold")
            table.add_column("Ask Qty", justify="center")

            for price, sides in sorted(orderbook.orders.items(), reverse=True):
                table.add_row(
                    str(sum(order.quantity for order in sides[Side.BID]))
                    if sides[Side.BID]
                    else "",
                    str(price),
                    str(sum(order.quantity for order in sides[Side.ASK]))
                    if sides[Side.ASK]
                    else "",
                )

            console.print(table)


def submit_and_fill(product: Product, my_order: Order) -> tuple[int, int]:
    """
    Returns:
        (clearing_price, filled_quantity)
    """

    ob = OrderBookRegistry.get(product)

    # Step 1: submit order
    ob.submit_order(my_order)

    # Step 2: clearing price
    p_star = ob.calculate_clearing_price()

    # Step 3: gather eligible orders
    bids: list[Order] = []
    asks: list[Order] = []

    for price, sides in ob.orders.items():
        if price >= p_star:
            bids.extend(sides[Side.BID])
        if price <= p_star:
            asks.extend(sides[Side.ASK])

    # Step 4: price-time priority
    bids.sort(key=lambda o: -o.price)  # higher first
    asks.sort(key=lambda o: o.price)  # lower first

    # Step 5: total tradable volume
    total_bid_vol = sum(o.quantity for o in bids)
    total_ask_vol = sum(o.quantity for o in asks)
    remaining = min(total_bid_vol, total_ask_vol)

    # Step 6: matching
    filled = 0
    i = j = 0

    while i < len(bids) and j < len(asks) and remaining > 0:
        bid = bids[i]
        ask = asks[j]

        trade_qty = min(bid.quantity, ask.quantity, remaining)

        if bid is my_order:
            filled += trade_qty
        if ask is my_order:
            filled += trade_qty

        bid.quantity -= trade_qty
        ask.quantity -= trade_qty
        remaining -= trade_qty

        if bid.quantity == 0:
            i += 1
        if ask.quantity == 0:
            j += 1

    return p_star, filled


def compute_pnl(
    product: Product,
    order: Order,
    clearing_price: int,
    filled_qty: int,
) -> float:
    # Get constants
    if product == Product.DRYLAND_FLAX:
        buyback = DRYLAND_FLAX_BUYBACK_PER_UNIT
        fees = 0.0
    elif product == Product.EMBER_MUSHROOM:
        buyback = EMBER_MUSHROOM_BUYBACK_PER_UNIT
        fees = EMBER_MUSHROOM_FEES_PER_UNIT

    # Compute PnL
    if order.side == Side.BID:
        # You bought at clearing_price, sell at buyback
        pnl = float(filled_qty * (buyback - clearing_price))
    else:  # ASK
        # You sold at clearing_price, buy back at buyback
        pnl = float(filled_qty * (clearing_price - buyback))

    # Subtract fees
    pnl -= filled_qty * fees

    return pnl


if __name__ == "__main__":
    # Initialize orderbooks
    OrderBookRegistry.initialize(
        Product.DRYLAND_FLAX,
        DRYLAND_FLAX_BIDS,
        DRYLAND_FLAX_ASKS,
    )

    OrderBookRegistry.initialize(
        Product.EMBER_MUSHROOM,
        EMBER_MUSHROOM_BIDS,
        EMBER_MUSHROOM_ASKS,
    )

    # Create a test order
    dryland_flax_order = Order(
        side=Side.BID,
        price=35,
        quantity=18_000,
    )

    ember_mushroom_order = Order(
        side=Side.BID,
        price=14,
        quantity=43_000,
    )

    # Run simulation
    print("DRYLAND FLAX")
    print(dryland_flax_order)
    dryland_flax_clearing_price, dryland_flax_filled_qty = submit_and_fill(
        Product.DRYLAND_FLAX,
        dryland_flax_order,
    )

    print("Clearing Price:", dryland_flax_clearing_price)
    print("Filled Quantity:", dryland_flax_filled_qty)
    print(
        f"PnL: {compute_pnl(Product.DRYLAND_FLAX, dryland_flax_order, dryland_flax_clearing_price, dryland_flax_filled_qty)}"
    )
    print("\n")

    print("EMBER MUSHROOM")
    print(ember_mushroom_order)
    ember_mushroom_clearing_price, ember_mushroom_filled_qty = submit_and_fill(
        Product.EMBER_MUSHROOM,
        ember_mushroom_order,
    )

    print("Clearing Price:", ember_mushroom_clearing_price)
    print("Filled Quantity:", ember_mushroom_filled_qty)
    print(
        f"PnL: {compute_pnl(Product.EMBER_MUSHROOM, ember_mushroom_order, ember_mushroom_clearing_price, ember_mushroom_filled_qty)}"
    )
    print("\n")
    # Reset registry (important if rerunning in same session)
    OrderBookRegistry.clear()
