# Heuristic Trading Strategy (ASH_COATED_OSMIUM)

## 0. Summary

`AshCoatedOsmiumTrader` follows the same take/rebalance/make decomposition as EMERALDS and TOMATOES, but uses an EMA-based fair value instead of a static midpoint.

Fair value:

$$
f_t = \text{EMA}_t
$$

with update form:

$$
\text{EMA}_t = \alpha \cdot \text{mid}_t + (1-\alpha)\cdot \text{EMA}_{t-1}
$$

where $\alpha = 0.26$ in `BaseTrader`.

---

## 1. State Variables

At each timestep:

- Order book levels (bids/asks with sizes)
- EMA fair value $f_t$
- Current inventory $q_t \in [-Q,Q]$
- Quote/fill counters (`bid_quotes`, `ask_quotes`, fills, fill volumes) for diagnostics

If current best quotes are missing, the trader falls back to previous state via inherited logic.

---

## 2. Trading Policy

$$
\pi = \pi_{\text{take}} + \pi_{\text{inventory}} + \pi_{\text{make}}
$$

### 2.1 Taking (Aggressive)

- Buy asks when:
  $$
  p^a < f_t - 1
  $$
- Sell bids when:
  $$
  p^b > f_t + 1
  $$

Compared to TOMATOES, this uses strict inequalities around an adaptive fair value.

### 2.2 Inventory Control

At fair value boundary:

- If short ($q_t < 0$), allow buy at:
  $$
  p^a \le f_t
  $$
- If long ($q_t > 0$), allow sell at:
  $$
  p^b \ge f_t
  $$

This lets the strategy reduce risk without waiting for strong dislocations.

### 2.3 Market Making (Passive)

Start from wall-improved quotes:

$$
p_t^{bid} = \lfloor p_t^{b,\min}+1 \rfloor,\quad
p_t^{ask} = \lceil p_t^{a,\max}-1 \rceil
$$

Then refine similarly to other products:

- Improve bid by one tick if volume and fair-value constraints support it.
- Improve ask by one tick under symmetric conditions.

Post remaining max-allowed size on both sides.

---

## 3. Why EMA Fair Value

Using EMA instead of a static midpoint provides:

- **Adaptivity**: tracks gradual level shifts
- **Noise smoothing**: avoids overreacting to one-tick jitter
- **Consistency**: single fair value for taking + making + inventory recycle

---

## 4. Tunable Parameters

- EMA smoothing factor $\alpha$ (`0.26`)
- Aggressive threshold around fair value (`1` tick)
- Volume threshold for one-tick queue improvement (`>1`)
- Position limit $Q$

