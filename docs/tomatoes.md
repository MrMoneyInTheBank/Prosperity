# Heuristic Trading Strategy (TOMATOES)

## 0. Summary

The `TomatoTrader` uses the same three-part structure as the EMERALDS baseline:

1. Aggressive taking when quotes are clearly mispriced vs an anchor
2. Inventory-aware rebalancing near fair value
3. Passive market making inside the book to capture spread

The primary difference is the fair-value anchor:

$$
\tilde{p}_t = \frac{p_t^{b,\min} + p_t^{a,\max}}{2}
$$

where $p_t^{b,\min}$ and $p_t^{a,\max}$ are the outer "wall" prices of visible bids/asks.

---

## 1. State Variables

At time $t$:

- Best bid/ask:
  $$
  p_t^{b,*},\; p_t^{a,*}
  $$
- Wall bid/ask:
  $$
  p_t^{b,\min},\; p_t^{a,\max}
  $$
- Mid anchor:
  $$
  \tilde{p}_t = \frac{p_t^{b,\min} + p_t^{a,\max}}{2}
  $$
- Inventory:
  $$
  q_t \in [-Q, Q]
  $$

---

## 2. Trading Policy

The policy is:

$$
\pi = \pi_{\text{take}} + \pi_{\text{inventory}} + \pi_{\text{make}}
$$

### 2.1 Taking (Aggressive)

- Buy asks when:
  $$
  p^a \le \tilde{p}_t - 1
  $$
- Sell bids when:
  $$
  p^b \ge \tilde{p}_t + 1
  $$

This captures obvious edge when available liquidity is outside anchor bounds.

### 2.2 Inventory Control

Near fair value:

- If short ($q_t < 0$), allow buys at:
  $$
  p^a \le \tilde{p}_t
  $$
- If long ($q_t > 0$), allow sells at:
  $$
  p^b \ge \tilde{p}_t
  $$

This helps recycle inventory while staying close to neutral.

### 2.3 Market Making (Passive)

Initial quote candidates:

$$
p_t^{bid} = p_t^{b,\min} + 1,\quad
p_t^{ask} = p_t^{a,\max} - 1
$$

Then refine by scanning visible levels:

- On bid side, overbid by one tick where queue quality is favorable and still below anchor.
- On ask side, undercut by one tick where queue quality is favorable and still above anchor.

Finally post residual capacity:

$$
\text{Buy up to } (Q-q_t) \text{ at } p_t^{bid},\quad
\text{Sell up to } (Q+q_t) \text{ at } p_t^{ask}
$$

---

## 3. Practical Interpretation

- TOMATOES strategy is a spread-capture + inventory-control heuristic.
- It assumes short-horizon reversion to a stable anchor defined by current book walls.
- It prioritizes always quoting both sides (when possible) while using taking rules for obvious mispricings.

---

## 4. Tunable Parameters

- Tick threshold around anchor (currently `1`)
- Volume threshold for one-tick improvement (currently `> 1`)
- Position limit $Q$ from global config
- Anchor definition (currently wall-based midpoint)

