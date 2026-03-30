# Heuristic Trading Strategy (EMERALDS)

## 0. Acknowledgements
To familiarize myself with the environment, I heavily referenced [Frankfurt Hedgehogs'](https://github.com/TimoDiehm/imc-prosperity-3/tree/main?tab=readme-ov-file#round-1-market-making)
writeup and this initial strategy is identical to the strategy the team used for trading ***Rainforest resin***. It will serve as a 
base to iterate upon. Some initial ideas I have been circling are using a fill probability calculation to make better informed
markets and also considering order sizes intertwined with recycling inventory at a higher rate.

## 1. State Variables

At time $t$, define the order book:

- **Bids:**
  $$
  \mathcal{B}_t = \{(p_i^b, v_i^b)\}_{i=1}^n
  $$
  (sorted in decreasing price)

- **Asks:**
  $$
  \mathcal{A}_t = \{(p_j^a, v_j^a)\}_{j=1}^m
  $$
  (sorted in increasing price)

**Best quotes:**
$$
p_t^{b,*} = \max_i p_i^b, \quad
p_t^{a,*} = \min_j p_j^a
$$

**Wall prices:**
$$
p_t^{b,\min} = \min_i p_i^b, \quad
p_t^{a,\max} = \max_j p_j^a
$$

**Anchor price:**
$$
\tilde{p}_t = \frac{p_t^{b,\min} + p_t^{a,\max}}{2}
$$

**Inventory:**
$$
q_t \in [-Q, Q]
$$

---

## 2. Trading Policy

The strategy is a mapping:
$$
\pi: (\mathcal{B}_t, \mathcal{A}_t, q_t) \mapsto \text{orders}
$$

It consists of three components:
- Taking
- Inventory Control
- Market Making

---

## 3. Taking (Aggressive Trades)

For each ask $(p_j^a, v_j^a) \in \mathcal{A}_t$:

If:
$$
p_j^a \leq \tilde{p}_t - \delta
$$
then submit:
$$
\text{Buy } \min(v_j^a, Q - q_t)
$$

---

For each bid $(p_i^b, v_i^b) \in \mathcal{B}_t$:

If:
$$
p_i^b \geq \tilde{p}_t + \delta
$$
then submit:
$$
\text{Sell } \min(v_i^b, Q + q_t)
$$

---

## 4. Inventory Control

If $q_t < 0$ (short):
$$
p_j^a \leq \tilde{p}_t
\quad \Rightarrow \quad \text{Buy to reduce } |q_t|
$$

If $q_t > 0$ (long):
$$
p_i^b \geq \tilde{p}_t
\quad \Rightarrow \quad \text{Sell to reduce } q_t
$$

---

## 5. Market Making (Passive Quotes)

### Bid Construction

Initialize:
$$
p_t^{bid} = p_t^{b,\min} + 1
$$

Find first $(p_i^b, v_i^b)$ such that:
$$
p_i^b < \tilde{p}_t
$$

Then:
$$
p_t^{bid} =
\begin{cases}
\max(p_t^{bid}, p_i^b + 1), & \text{if } v_i^b > \theta \text{ and } p_i^b + 1 < \tilde{p}_t \\
\max(p_t^{bid}, p_i^b), & \text{otherwise}
\end{cases}
$$

---

### Ask Construction

Initialize:
$$
p_t^{ask} = p_t^{a,\max} - 1
$$

Find first $(p_j^a, v_j^a)$ such that:
$$
p_j^a > \tilde{p}_t
$$

Then:
$$
p_t^{ask} =
\begin{cases}
\min(p_t^{ask}, p_j^a - 1), & \text{if } v_j^a > \theta \text{ and } p_j^a - 1 > \tilde{p}_t \\
\min(p_t^{ask}, p_j^a), & \text{otherwise}
\end{cases}
$$

---

### Final Orders

$$
\text{Post:}
\quad
\begin{cases}
\text{Buy } (Q - q_t) \text{ at } p_t^{bid} \\
\text{Sell } (Q + q_t) \text{ at } p_t^{ask}
\end{cases}
$$

---

## 6. Compact Formulation

The strategy decomposes as:
$$
\pi = \pi_{\text{take}} + \pi_{\text{inventory}} + \pi_{\text{make}}
$$

Where:

- **Taking:**
$$
\mathbb{1}_{p \leq \tilde{p}_t - \delta}, \quad
\mathbb{1}_{p \geq \tilde{p}_t + \delta}
$$

- **Inventory Control:**
$$
\text{Trade toward } q_t = 0 \text{ near } \tilde{p}_t
$$

- **Market Making:**
$$
(p_t^{bid}, p_t^{ask}) = \arg\max \text{(queue priority under constraints)}
$$

---

## 7. Tunable Parameters

- **Anchor function:**
$$
\tilde{p}_t = f(\mathcal{B}_t, \mathcal{A}_t)
$$

- **Threshold:**
$$
\delta
$$

- **Volume threshold:**
$$
\theta
$$

- **Inventory limit:**
$$
Q
$$

---

## 8. Interpretation

The strategy approximates the optimization:
$$
\max_{p^{bid}, p^{ask}}
\mathbb{E}[\text{spread capture}]
- \gamma \cdot \text{inventory risk}
$$

subject to:
- price constraints relative to $\tilde{p}_t$
- order book structure
- position limits

## 9. Empirical Analysis

### 9.1 Order Book Statistics

From historical order book data:

- **Midprice:**
  - Mean ≈ 10000  
  - Variance ≈ 0.51  

- **Microprice:**
  - Mean ≈ 10000  
  - Variance ≈ 0.30  

- **Log Returns (midprice):**
  - Mean ≈ 0  
  - Variance ≈ 1e-8  

These results indicate that the price process is **extremely stable**, with negligible drift and very low volatility.

---

### 9.2 Signal Analysis

Two microstructure-derived signals were evaluated:

- **Order Book Imbalance:**
  $$
  \text{imbalance} = \frac{V^{bid} - V^{ask}}{V^{bid} + V^{ask}}
  $$
  Correlation with future returns:
  $$
  \text{corr}(\text{imbalance}, r_{t+1}) \approx -0.68
  $$

- **Microprice Deviation:**
  $$
  \Delta_{\mu} = \text{microprice} - \text{midprice}
  $$
  Correlation with future returns:
  $$
  \text{corr}(\Delta_{\mu}, r_{t+1}) \approx 0.62
  $$

---

### 9.3 Interpretation

- The near-zero return mean and variance confirm that **no persistent directional trend exists**.
- Despite strong correlations:
  - Microprice deviation suggests short-term directional movement.
  - Imbalance suggests contrarian pressure from liquidity takers.
- However, these effects are **too small in magnitude** to produce meaningful PnL when executed.

---

## 10. Strategy Iterations

A series of targeted improvements were tested to extract additional edge.

---

### 10.1 Microprice-Adjusted Fair Value

The anchor price was modified:

$$
\tilde{p}_t = \text{midprice} + \alpha \cdot (\text{microprice} - \text{midprice})
$$

**Result:**
- No change in PnL (≈ 1050)

**Conclusion:**
- Although statistically predictive, the signal does not translate into executable edge.

---

### 10.2 Inventory-Skewed Market Making

Quotes were adjusted based on inventory and imbalance:
- Inventory-dependent spread widening
- Directional skew of quotes

**Result:**
- Significant degradation in PnL (≈ 204)

**Conclusion:**
- The artificial spread structure dominates any inventory risk
- Skewing quotes sacrifices guaranteed spread capture without sufficient benefit

---

### 10.3 Midprice as Anchor

Replaced wall-based anchor with:

$$
\tilde{p}_t = \frac{p_t^{b,*} + p_t^{a,*}}{2}
$$

**Result:**
- No change in PnL (≈ 1050)

**Conclusion:**
- Anchor definition is largely irrelevant due to price stability

---

### 10.4 Stricter Taking Conditions

Taking logic was refined using:
- Microprice confirmation
- Increased thresholds

**Result:**
- No improvement in PnL

**Conclusion:**
- Aggressive trading does not contribute meaningful alpha

---

## 11. Observations

Across all experiments:

- Baseline strategy PnL: **1050**
- Modified strategies:
  - Microprice adjustment: **1050**
  - Midprice anchor: **1050**
  - Inventory skew: **204**

Additionally:
- Reference strategies and default implementations also converge to **≈1050 PnL**

---

## 12. Conclusion

The EMERALDS market exhibits the following properties:

1. **Price Stability**
   - Midprice is effectively constant
   - No exploitable drift or volatility

2. **Artificial Spread Structure**
   - Profits arise primarily from spread capture
   - The spread is fixed and reliably harvestable

3. **Lack of Executable Alpha**
   - Microstructure signals exist statistically
   - But do not translate into meaningful trading profits

---

### Final Insight

The problem reduces to:

$$
\max (\text{spread capture subject to minimal inventory risk})
$$

The base heuristic strategy already achieves this optimally.

---

### Practical Implication

Further improvements (e.g., Avellaneda–Stoikov, fill probability models, or advanced signals) do not yield meaningful gains in this environment.

Thus:

> **The EMERALDS product is effectively solved using a simple market-making strategy, and additional complexity leads to diminishing or negative returns.**
