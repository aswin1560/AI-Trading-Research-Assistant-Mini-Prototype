"""
defaults.py - Conservative defaults, baseline assumptions, and educational biases.
"""

from typing import List
from schema import AssumptionItem

CONSERVATIVE_ASSUMPTIONS: List[AssumptionItem] = [
    AssumptionItem(
        field="test_period",
        assumed_value="2015-01-01 to 2024-12-31 (10 Years)",
        reason="Provides multi-cycle coverage including low-vol bull markets, COVID crash (2020), and post-COVID regimes."
    ),
    AssumptionItem(
        field="transaction_costs",
        assumed_value="0.05% per trade (0.10% round-trip)",
        reason="Accounts for exchange fees, STT, and broker commissions typical for index cash/ETF trading."
    ),
    AssumptionItem(
        field="slippage",
        assumed_value="0.02% per fill",
        reason="Reflects realistic bid-ask bounce and market impact upon entry/exit execution."
    ),
    AssumptionItem(
        field="execution_timing",
        assumed_value="Next bar Open (or Close on signal bar)",
        reason="Prevents look-ahead bias by assuming trades execute after the signal candle confirms."
    ),
    AssumptionItem(
        field="benchmark",
        assumed_value="NIFTY 50 Buy-and-Hold",
        reason="Standard comparative baseline for Indian equity market research."
    )
]

BIAS_WARNINGS = [
    {
        "type": "Look-Ahead Bias",
        "description": "Using information that was not available at signal generation time.",
        "mitigation": "Ensure volatility regime (e.g., India VIX) and daily drops are measured using prior close or confirmed bar close, not intraday future data."
    },
    {
        "type": "Survivorship Bias",
        "description": "Testing only indices or stocks that survived and prospered, ignoring delisted constituents.",
        "mitigation": "For individual stocks, survivorship bias is severe. For NIFTY 50 index, constituent turnover introduces a milder positive momentum bias."
    },
    {
        "type": "Overfitting (p-Hacking)",
        "description": "Testing multiple drop thresholds (0.5%, 1%, 1.5%, 2%, 2.5%) and only reporting the best performing one.",
        "mitigation": "Perform parameter sensitivity tests across neighboring thresholds to verify if an edge is robust or a random local peak."
    },
    {
        "type": "Regime Shifts",
        "description": "High volatility in 2015-2019 behaved differently from the 2020 pandemic crash and 2022-2023 rate hiking cycle.",
        "mitigation": "Evaluate sub-period stability rather than relying solely on aggregate 10-year metrics."
    },
    {
        "type": "Sample Size Fragility",
        "description": "Strategies with fewer than 30-50 trades lack statistical power to reject the null hypothesis.",
        "mitigation": "A 58% win rate over 47 trades could easily be explained by random noise (p > 0.05)."
    }
]
