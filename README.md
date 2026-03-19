# Prosperity

Quantitative trading research framework for the IMC Prosperity competition.

## Overview

Prosperity is a research-driven trading system designed for the IMC Prosperity competition. The framework follows a structured pipeline from data acquisition through to strategy simulation, with emphasis on rigorous research methodology and realistic trading approximations.

The core approach simulates live trading by feeding historical data sequentially in chunks, ensuring strategies operate under conditions that approximate real-time decision making.

## Research Pipeline

```
download -> analyze -> pattern discovery -> strategy hypothesis -> backtesting -> simulation -> reporting
```

- **download**: Acquire historical market data
- **analyze**: Examine price dynamics, statistical properties, and market microstructure
- **pattern discovery**: Identify recurring behaviors and anomalies
- **strategy hypothesis**: Formulate trading hypotheses based on discovered patterns
- **backtesting**: Evaluate strategies against historical data
- **simulation**: Test strategies under realistic sequential conditions
- **reporting**: Generate performance metrics and outcome analysis

## Features

- Historical data analysis (price dynamics, statistical properties)
- Order book–based feature extraction (L1 data)
- Microstructure signal analysis (spread, mid price, imbalance)
- Strategy development framework
- Backtesting engine
- Sequential simulation engine (chunked data to mimic real-time)
- Performance and outcome reporting

## Simulation Approach

Historical data is split into sequential chunks and fed to strategies step-by-step. At each timestep, both market state and order book state are updated. Strategies only have access to data up to that point in time. This design:

- Prevents future data leakage
- Enforces step-by-step decision making
- Approximates live trading conditions without requiring real-time market access

## Market Microstructure Modeling

The system operates on top-of-book (bid/ask) data, representing the best bid and ask prices with corresponding quantities. An `OrderBook` abstraction maintains this state, updated sequentially at each timestep during simulation.

Derived signals computed from order book state:

- **Mid price**: Fair value estimate from the average of best bid and ask
- **Bid-ask spread**: Transaction cost indicator
- **Order imbalance**: Ratio of bid-to-ask quantity, indicating directional pressure

This is not a full depth order book or matching engine. Only L1 data is modeled.

## Project Structure

```
prosperity/
├── data/              # Data acquisition and storage
├── analysis/          # Statistical and market analysis
├── strategies/        # Trading strategy implementations
├── backtesting/       # Backtesting engine
├── simulation/        # Sequential simulation engine
├── reporting/         # Performance metrics and reports
├── cli/               # Command-line interface
├── pyproject.toml
└── README.md
```

## Getting Started

Install dependencies:

```bash
uv sync
```

Run the research framework:

```bash
uv run python main.py
```

## Development Philosophy

- **Reproducibility**: All experiments are documented and repeatable
- **Modular strategies**: Strategies are isolated and interchangeable
- **Separation of research and execution**: Clear boundaries between analysis and trading logic
- **Performance awareness**: Computational efficiency is considered throughout
- **Data leakage avoidance**: Strict temporal boundaries in all evaluation stages

## Roadmap

- [ ] Implement multiple trading strategies
- [ ] Build strategy comparison framework
- [ ] Improve simulation fidelity
- [ ] Develop comprehensive metrics and evaluation framework
- [ ] Expand CLI tooling

## Notes

This is an evolving research codebase. Structure and conventions will develop as the project matures.
