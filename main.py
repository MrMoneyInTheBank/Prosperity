from __future__ import annotations

from shutil import get_terminal_size

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule


def main() -> None:
    width = min(get_terminal_size().columns or 92, 92)
    console = Console(width=width)

    intro = Markdown(
        """\
Work here is centered on **[notebooks](./src/notebooks/products_analysis/)** for \
research (order book features, plots, diagnostics) and **product strategy modules** under \
**`src/traders/product_traders/`**. The runnable entrypoints are **CLI tools**, not `main.py`.

This repo does **not** expose a single long-running trader process—IMC Prosperity is played via \
submission files and offline backtests.
""",
        justify="left",
    )

    steps = Markdown(
        """\
### Typical flow

1. **Place data** (`data/round{N}/prices_*`, `trades_*`) per `DatasetSpec` in `src/processing/dataset_spec.py`.
2. **Iterate in notebooks** (e.g. `src/notebooks/products_analysis/*.ipynb`) calling `run_analysis(...)`.
3. Edit **product traders**, then **regenerate** the submission file.
4. **Backtest** with the bundled backtester CLI.
""",
    )

    cmds = Markdown(
        """\
### Commands (from repo root)

| Action | Command |
|:---|:---|
| Install deps | `uv sync` |
| Build `src/traders/trader.py` + snapshots in `history/` | `uv run gen-trader` |
| Backtest CLI (options from prosperity4btest) | `uv run bt --help` |

Prerequisites: Python **≥3.12**, **`uv`**, and a sibling clone **`../imc-prosperity-4-backtester`** \
(`pyproject.toml` sources `prosperity4btest` from there).
""",
    )

    further = Markdown(
        """\
See **[README.md](./README.md)** for the full layout, data layout diagram, and architecture notes.""",
        justify="left",
    )

    panel = Panel(
        Group(
            intro,
            Rule(style="dim blue"),
            steps,
            Rule(style="dim blue"),
            cmds,
            Rule(style="dim blue"),
            further,
        ),
        title="[bold cyan]Prosperity[/bold cyan]",
        subtitle="IMC Prosperity · quantitative research workspace",
        border_style="bright_blue",
        padding=(1, 2),
    )

    console.print()
    console.print(panel, justify="center")
    console.print()


if __name__ == "__main__":
    main()
