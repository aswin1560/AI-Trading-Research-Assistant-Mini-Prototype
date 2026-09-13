# Thinking Note: Designing an AI Trading Research Assistant

> **Assignment Focus**: Product thinking, ambiguity resolution, and quantitative epistemics in financial machine learning.

---

## 1. Deconstructing "Sharp Fall": Parameter vs. Concept

When a user asks:
> *"Does buying NIFTY after a sharp fall work better during high-volatility periods?"*

The phrase **"sharp fall"** is superficially clear to a human trader, but mathematically meaningless to an execution engine. It cannot be hardcoded because it embodies three distinct dimensions:

1. **Measurement Basis**:
   - **Close-to-Close return**: (e.g., $Close_t / Close_{t-1} - 1 \le -1.0\%$) — captures overnight sentiment and session trend.
   - **Intraday Open-to-Close return**: (e.g., $Close_t / Open_t - 1 \le -1.5\%$) — isolates intra-session panic selling.
   - **High-to-Low candle range**: measures intra-day volatility expansion rather than directional drift.
   - **Normalized z-score**: return normalized by rolling 20-day standard deviation (e.g., $z \le -2.0\sigma$), making the definition adaptive across regimes.

2. **The Product Decision**:
   - **Treat "sharp fall" as an explicit user-calibrated parameter, never a hardcoded constant.**
   - By presenting clickable options (`>= 0.5%`, `>= 1.0%`, `>= 2.0%`, or custom z-score), the system forces the user to confront their implicit threshold before generating results.

---

## 2. Assumptions vs. Questions Matrix

A key failure mode of quantitative AI assistants is either **interrogating the user with 20 questions** (decision paralysis) or **silently making assumptions** (epistemic dishonesty).

| Category | Parameter | System Treatment | Rationale |
| :--- | :--- | :--- | :--- |
| **Must Ask** | Drop Threshold (e.g., $\ge 1\%$) | **Required Gap** | Core variable of the hypothesis; cannot be guessed. |
| **Must Ask** | Holding Period (e.g., 5 days) | **Required Gap** | Determines the horizon of the edge; day trading vs swing trading. |
| **Must Ask** | Exit Rule (Time vs Target vs Stop) | **Required Gap** | Entry is only 50% of trade expectancy; exits dictate downside. |
| **Must Clarify**| High Volatility Definition (VIX > 20) | **Clarification Gap** | Ambiguous term; suggest standard cutoffs (e.g., VIX 90th percentile). |
| **Can Assume** | Historical Test Window (2015–2024) | **Conservative Assumption** | 10 years covers multiple macro regimes (COVID, bull, rate hikes). |
| **Can Assume** | Transaction Costs (0.05% / leg) | **Conservative Assumption** | STT, exchange turnover fees, and broker commissions. |
| **Can Assume** | Execution Slippage (0.02% / fill) | **Conservative Assumption** | Bid-ask spread and market impact on market orders. |
| **Can Assume** | Signal Execution (Next Bar Open) | **Conservative Assumption** | Prevents look-ahead bias of trading at today's close on today's signal. |

---

## 3. The 5 Minimum Questions to Ask Every Trader

Before running any quantitative backtest, an assistant must elicit:

1. **What threshold defines the entry trigger?** (e.g., Close drop $\ge 1\%$, $\ge 2\%$, or intraday dip?)
2. **How long is the position held?** (Time-based holding duration or dynamic stop?)
3. **What is the invalidation/exit rule?** (Trailing stop, profit target, or fixed bar count?)
4. **What timeframe governs the signals?** (Daily close vs 15-minute intraday bars?)
5. **What constitutes "working better"?** (Win rate, absolute CAGR, Sharpe ratio, or maximum drawdown reduction?)

---

## 4. What Could Go Wrong: Pre-Mortem on Flawed Backtests

### A. Look-Ahead Bias
- **The Pitfall**: Using today's closing VIX value to filter today's trade when the trade is supposedly entered intraday, or referencing future bar extrema.
- **System Safeguard**: Signals are strictly calculated on confirmed bar closes, and executions are simulated at the subsequent open or marked at the exact close of the signal day.

### B. Survivorship Bias
- **The Pitfall**: Testing stock-picking strategies only on today's NIFTY 50 constituents, ignoring companies that were removed or went bankrupt.
- **System Safeguard**: For index-level testing (NIFTY 50), constituent turnover has a milder impact, but the system logs an explicit note warning that individual stock tests require point-in-time constituent universes.

### C. Overfitting (p-Hacking)
- **The Pitfall**: Testing 50 variations of thresholds (0.7%, 0.8%, 0.9%, 1.0% ...) and cherry-picking the one that produced the highest returns.
- **System Safeguard**: Built-in **Sensitivity Analysis Grid** automatically displays results for neighboring thresholds (0.5%, 1.0%, 1.5%, 2.0%, 2.5%). A true edge remains positive across neighboring parameters; an overfit strategy collapses.

### D. Transaction Cost Erosion
- **The Pitfall**: A strategy with +0.3% average gross return on a 2-day hold appears profitable, but 0.15% round-trip costs and slippage consume 50% of the alpha.
- **System Safeguard**: Net returns are calculated after deducting standard friction per trade (0.10% round-trip).

### E. Sample Size Fragility & Regime Shifts
- **The Pitfall**: 47 trades over 10 years averages under 5 trades per year. A single macro event (e.g., the March–June 2020 recovery rally) can generate 70% of total lifetime strategy profits.
- **System Safeguard**: Epistemic breakdown highlights trade clustering and warns that $N=47$ lacks statistical power to reject the null hypothesis at $p < 0.05$.

---

## 5. The Critical Distinction: Data vs. Conclusion

$$\text{"Empirical Data"} \neq \text{"Economic Edge"}$$

- **What the Data Shows**:
  - *"Between 2015 and 2024, buying NIFTY after a $\ge 1\%$ drop when VIX was $> 20$ and holding for 5 days produced 47 trades with a 57.4% win rate and +0.42% net return per trade."*
- **What We Can (and Cannot) Conclude**:
  - **Cannot conclude**: *"Buying after sharp falls is a guaranteed tradeable strategy."*
  - **Can conclude**: *"There is empirical evidence of short-term mean-reversion during high volatility regimes, but sample size is small, returns are clustered in crisis-recovery months, and the edge is highly sensitive to execution slippage."*

The hallmark of a great quantitative product is making this distinction impossible to miss.
