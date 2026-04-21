# Heuristic Trading Strategy (INTARIAN_PEPPER_ROOT)

## 0. Summary

`IntarianPepperRootTrader` is intentionally minimal and one-sided.

At each timestep, if a best ask exists, it buys the full displayed best-ask volume at that price.

In compact form:

$$
\pi_t =
\begin{cases}
\text{Buy } v_t^{a,*} \text{ at } p_t^{a,*}, & \text{if ask exists}\\
\varnothing, & \text{otherwise}
\end{cases}
$$

---

## 1. State and Inputs

The strategy uses only:

- Best ask price:
  $$
  p_t^{a,*}
  $$
- Best ask volume:
  $$
  v_t^{a,*}
  $$

No explicit fair-value estimation, no inventory-aware quote logic, and no passive asks are used.

---

## 2. Execution Rule

Algorithm:

1. If there is no best ask, do nothing.
2. Else submit:
   $$
   \text{Order} = (p_t^{a,*}, +v_t^{a,*})
   $$

Order sizing still passes through inherited position-limit guards in `BaseTrader.bid(...)`, so effective filled volume is clipped by available buy capacity.

---

## 3. Interpretation

This implementation behaves like an always-on liquidity taker on the ask side:

- **Pros**: simple, deterministic, aggressively accumulates inventory when asks are present.
- **Cons**: no valuation filter, no rebalancing logic, no spread capture through passive quoting.

It is best viewed as a baseline or placeholder strategy for rapid iteration.

---

## 4. Likely Next Iterations

Natural extensions include:

- add fair-value gate before buying
- add symmetric sell/reduce rules
- add inventory targets and dynamic sizing
- add passive quoting when spread conditions are favorable

