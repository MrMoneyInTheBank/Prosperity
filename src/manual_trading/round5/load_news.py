import json
from pathlib import Path

from src.manual_trading.round5.datatypes import Product, Article, Newspaper


def load_news_json(news_json_path: Path) -> Newspaper:
    with open(news_json_path, "r") as data_file:
        raw_data = json.load(data_file)

        newspaper: Newspaper = {}
        for product, article in raw_data.items():
            try:
                product = Product(product)
            except ValueError:
                raise ValueError(f"Invalid product key: {product}")

            if not isinstance(article, dict):
                raise TypeError(f"{product}: expected object")
            elif sorted(article.keys()) != sorted(["body", "headline"]):
                raise KeyError(
                    f"{product}: expected object with keys body and headline, got{article.keys()}"
                )

            headline = article["headline"]
            body = article["body"]

            if not isinstance(headline, str) or not isinstance(body, str):
                raise TypeError(f"{product}: headline/body must be str")

            newspaper[product] = Article(headline=headline, body=body)

    return newspaper
