from types import MappingProxyType
from src.manual_trading.round4.datatypes import Product, Market, Quote, Bid, Ask


def build_market(raw_quotes: dict[Product, dict[str, list]]) -> Market:
    return Market(
        quotes=MappingProxyType(
            {
                product: Quote(bid=Bid(*quote["bid"]), ask=Ask(*quote["ask"]))
                for product, quote in raw_quotes.items()
            }
        )
    )


def midprice(quote: Quote) -> float:
    return 0.5 * (quote.bid.price + quote.ask.price)


def get_midprice(market: Market, product: Product) -> float:
    return midprice(market.quotes[product])
