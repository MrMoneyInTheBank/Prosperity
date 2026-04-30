from typing import Final
from src.manual_trading.round5.datatypes import Newspaper
from src.config.constants import NEWSPAPER_JSON_FILE
from src.manual_trading.round5.load_news import load_news_json


def main() -> None:
    newspaper: Final[Newspaper] = load_news_json(NEWSPAPER_JSON_FILE)
    print(newspaper)


if __name__ == "__main__":
    main()
