# Prosperity

Quantitative trading research and strategy development workspace for the IMC Prosperity competition.

## What This Repository Is

This repo has two main jobs:

- **Research pipeline** for analyzing historical order book + trades data with Polars
- **Submission trader codebase** with product-specific strategy classes and generated final `trader.py`

It is not a single monolithic app entrypoint yet. Instead, work is organized around notebooks, analysis modules, strategy modules, and utility scripts.

## Core Capabilities

- Load and validate round/day market datasets from `data/`
- Build microstructure features from L1 order book data (spread, imbalance, microprice, depth, returns)
- Run product-level analysis and plotting pipelines
- Implement per-product trading logic with shared abstractions
- Auto-generate consolidated submission file `src/traders/trader.py` from templates + product trader modules
- Run backtests via the external Prosperity backtester package

## Project Layout

```text
.
├── data/                          # Local historical CSVs (ignored by git)
├── backtests/                     # Backtest logs/artifacts
├── docs/                          # Research notes
├── src/
│   ├── config/                    # Constants, schemas, product enums, limits
│   ├── processing/                # Dataset loading + feature engineering
│   ├── research/                  # Analysis orchestration, stats, plots
│   ├── traders/
│   │   ├── product_traders/       # Product strategy implementations
│   │   ├── history/               # Generated trader snapshots
│   │   └── trader.py              # Auto-generated submission file
│   ├── templates/                 # Header/footer templates for codegen
│   ├── scripts/                   # Utility scripts (e.g., trader generation)
│   ├── notebooks/                 # Product analysis notebooks
│   └── manual_trading/            # Standalone manual simulation experiments
├── datamodel.py                   # IMC-provided trading model types
├── main.py                        # Minimal placeholder entrypoint
├── pyproject.toml
└── README.md
```

## Setup

### 1) Prerequisites

- Python `>=3.12`
- [`uv`](https://docs.astral.sh/uv/)
- Local clone of `imc-prosperity-4-backtester` at:
  - `../imc-prosperity-4-backtester`

`pyproject.toml` expects `prosperity4btest` from that local path.

### 2) Install dependencies

```bash
uv sync
```

## Data Layout

Analysis code expects CSVs in this exact shape:

```text
data/
└── round{N}/
    ├── prices_round_{N}_day_{D}.csv
    └── trades_round_{N}_day_{D}.csv
```

This convention is enforced by `DatasetSpec` in `src/processing/dataset_spec.py`.

## Common Workflows

### Research and feature analysis

Use notebooks in `src/notebooks/products_analysis/` (for example `emeralds.ipynb`, `tomatoes.ipynb`) which call `run_analysis(...)` from `src/research/analysis.py`.

At a high level, analysis does:

1. Load round/day prices and trades
2. Build engineered order book and trade features
3. Compute summary stats/correlations
4. Generate diagnostic plots

### Generate submission trader file

The final `src/traders/trader.py` is generated from:

- `src/templates/trader_header.txt`
- `src/traders/product_traders/*.py`
- `src/templates/trader_footer.txt`

Run:

```bash
uv run gen-trader
```

This also writes timestamped snapshots to `src/traders/history/`.

### Run backtests

Backtesting is exposed through the script entrypoint:

```bash
uv run bt --help
```

The exact CLI options come from the external `prosperity4btest` package.

## Trading Architecture (Current)

- `BaseTrader` (`src/traders/product_traders/a_base_trader.py`) centralizes:
  - order book parsing
  - best quote + microprice helpers
  - EMA/state tracking
  - position-limit-aware order sizing
- Product-specific traders implement concrete decision rules in `get_orders()`
- `Trader.run(...)` in generated `src/traders/trader.py`:
  - reconstructs previous state from `traderData`
  - dispatches per product
  - collects orders + updated state
  - emits compressed logs

## Tooling

- Linting: `ruff`
- Type checking: `mypy`
- Formatting in trader generation script: attempts `ruff --fix` (imports) and `black` on generated output

## Useful Commands

```bash
# install dependencies
uv sync

# generate submission trader file
uv run gen-trader

# run backtester CLI
uv run bt --help

# run placeholder main entrypoint
uv run python main.py
```

## Notes

- This project is actively evolving.
- There is currently no repository-native automated test suite (`tests/` / `pytest`) yet.
- Most validation currently happens through notebooks, backtests, and simulation outputs.
