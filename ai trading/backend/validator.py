"""
validator.py - Pure deterministic gap detection and validation logic.

Critical Distinction:
- Required gaps -> block the experiment, must ask user
- Clarification gaps -> show as suggestions with clickable chips
- Optional gaps -> show with sensible conservative defaults
"""

from typing import List, Tuple, Dict, Any
from schema import Experiment, Gap
from defaults import CONSERVATIVE_ASSUMPTIONS


REQUIRED_FIELD_DEFINITIONS = [
    {
        "path": "instrument",
        "question": "Which instrument or ticker would you like to research?",
        "options": ["NIFTY", "BANKNIFTY", "SPY", "QQQ"],
        "severity": "required"
    },
    {
        "path": "timeframe",
        "question": "What timeframe should be evaluated for signals?",
        "options": ["daily", "hourly", "15min", "weekly"],
        "severity": "required"
    },
    {
        "path": "entry.condition",
        "question": "What quantifiable price decline constitutes a 'sharp fall'?",
        "options": [
            "Close drop >= 0.5%",
            "Close drop >= 1.0%",
            "Close drop >= 2.0%",
            "Intraday drop >= 1.5%",
            "2-day cumulative drop >= 2.5%"
        ],
        "severity": "required"
    },
    {
        "path": "exit.condition",
        "question": "What is the rule for exiting the position?",
        "options": [
            "Time-based (Hold for fixed N days)",
            "Target (+1.5%) or Stop-Loss (-1.0%)",
            "Trailing Stop (1.0% from peak)",
            "Until opposing reversal signal"
        ],
        "severity": "required"
    },
    {
        "path": "holding_period.value",
        "question": "How long should the position be held before exit?",
        "options": ["1 day", "3 days", "5 days", "10 days", "20 days"],
        "severity": "required"
    }
]


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Safely traverse dot-separated paths in dictionary."""
    parts = path.split(".")
    curr = data
    for part in parts:
        if isinstance(curr, dict):
            curr = curr.get(part)
        else:
            return None
    return curr


def find_gaps_and_validate(exp: Experiment) -> Tuple[List[Gap], List[str]]:
    """
    Evaluates an Experiment instance, computes missing required fields,
    and returns a list of actionable Gaps plus missing field paths.
    """
    gaps: List[Gap] = []
    missing_fields: List[str] = []
    exp_dict = exp.model_dump()

    # 1. Evaluate Core Required Fields
    for field_def in REQUIRED_FIELD_DEFINITIONS:
        path = field_def["path"]
        val = get_nested_value(exp_dict, path)
        
        if val is None or val == "":
            missing_fields.append(path)
            gaps.append(Gap(
                field=path,
                question=field_def["question"],
                severity="required",
                suggested_options=field_def["options"],
                current_value=None
            ))

    # 2. Evaluate Ambiguous Term Clarifications
    for term in exp.ambiguous_terms:
        term_lower = term.lower().strip()
        if "sharp fall" in term_lower or "crash" in term_lower or "drop" in term_lower:
            # If entry condition already specified, this is a clarification, else overlaps with required
            if "entry.condition" not in missing_fields:
                gaps.append(Gap(
                    field="clarification.sharp_fall_measurement",
                    question=f'You specified "{term}". How should this drop be measured?',
                    severity="clarification",
                    suggested_options=[
                        "Close-to-Close return",
                        "Open-to-Close intraday bar drop",
                        "High-to-Low intraday swing",
                        "Z-score of returns (> 2 std dev)"
                    ],
                    current_value=None
                ))
        elif "high-volatility" in term_lower or "volatility" in term_lower:
            gaps.append(Gap(
                field="clarification.volatility_threshold",
                question=f'You mentioned "{term}". What threshold or metric defines high volatility?',
                severity="clarification",
                suggested_options=[
                    "India VIX > 18",
                    "India VIX > 20 (90th percentile)",
                    "20-day Historical Volatility > 25%",
                    "ATR(14) > 1.5 * 50-day average ATR"
                ],
                current_value=None
            ))
        elif "better" in term_lower or "works better" in term_lower:
            gaps.append(Gap(
                field="clarification.edge_definition",
                question='You asked if it "works better". What quantitative objective defines success?',
                severity="clarification",
                suggested_options=[
                    "Higher Win Rate (> 55%)",
                    "Higher Average Trade Return (+X%)",
                    "Superior Risk-Adjusted Sharpe Ratio (> 1.0)",
                    "Lower Maximum Drawdown compared to baseline"
                ],
                current_value=None
            ))

    # 3. Optional Gaps / Research Calibration
    if not any(f.name.lower() == "filter_regime" for f in exp.filters):
        gaps.append(Gap(
            field="optional.market_regime",
            question="Would you like to restrict testing to bull markets or test all market regimes?",
            severity="optional",
            suggested_options=[
                "All Regimes (Unrestricted)",
                "Bull Regime Only (Close > 200 SMA)",
                "Bear Regime Only (Close < 200 SMA)"
            ],
            current_value="All Regimes"
        ))

    return gaps, missing_fields


def apply_clarifications(exp: Experiment, clarifications: Dict[str, Any]) -> Experiment:
    """
    Applies user-selected clarifications to the experiment model.
    """
    exp_dict = exp.model_dump()

    for path, value in clarifications.items():
        if value is None:
            continue

        if path == "instrument":
            exp_dict["instrument"] = str(value).upper()

        elif path == "timeframe":
            val_str = str(value).lower()
            if "daily" in val_str:
                exp_dict["timeframe"] = "daily"
            elif "hourly" in val_str:
                exp_dict["timeframe"] = "hourly"
            elif "15min" in val_str:
                exp_dict["timeframe"] = "15min"
            elif "weekly" in val_str:
                exp_dict["timeframe"] = "weekly"
            else:
                exp_dict["timeframe"] = "daily"

        elif path == "entry.condition":
            exp_dict["entry"]["condition"] = str(value)
            exp_dict["entry"]["type"] = "price_drop"

        elif path == "exit.condition":
            exp_dict["exit"]["condition"] = str(value)
            val_str = str(value).lower()
            if "time" in val_str or "day" in val_str:
                exp_dict["exit"]["type"] = "time"
            elif "target" in val_str or "stop" in val_str:
                exp_dict["exit"]["type"] = "target"
            elif "trailing" in val_str:
                exp_dict["exit"]["type"] = "stop"
            else:
                exp_dict["exit"]["type"] = "signal"

        elif path == "holding_period.value":
            val_str = str(value).lower()
            # extract numeric part
            import re
            match = re.search(r"(\d+(\.\d+)?)", val_str)
            if match:
                exp_dict["holding_period"]["value"] = float(match.group(1))
            else:
                exp_dict["holding_period"]["value"] = 5.0

            if "day" in val_str:
                exp_dict["holding_period"]["unit"] = "days"
            elif "week" in val_str:
                exp_dict["holding_period"]["unit"] = "weeks"
            elif "hour" in val_str:
                exp_dict["holding_period"]["unit"] = "hours"
            elif "bar" in val_str:
                exp_dict["holding_period"]["unit"] = "bars"
            else:
                exp_dict["holding_period"]["unit"] = "days"

        elif path == "clarification.volatility_threshold":
            # Add or update filter
            existing = False
            for f in exp_dict.get("filters", []):
                if "volatility" in f.get("name", "").lower():
                    f["condition"] = str(value)
                    existing = True
                    break
            if not existing:
                exp_dict["filters"].append({
                    "name": "volatility",
                    "condition": str(value),
                    "confidence": 0.95
                })

    # Update assumptions if not present
    if not exp_dict.get("assumptions"):
        exp_dict["assumptions"] = [a.model_dump() for a in CONSERVATIVE_ASSUMPTIONS]

    updated = Experiment(**exp_dict)
    # Re-evaluate gaps
    new_gaps, new_missing = find_gaps_and_validate(updated)
    updated.gaps = new_gaps
    updated.missing_fields = new_missing
    
    # Synthesize clean hypothesis
    inst = updated.instrument or "[Instrument]"
    tf = updated.timeframe or "daily"
    entry_cond = updated.entry.condition or "[Entry Condition]"
    exit_cond = updated.exit.condition or "[Exit Condition]"
    filter_cond = ", ".join([f"{f.name}: {f.condition}" for f in updated.filters]) or "None"
    
    updated.hypothesis = (
        f"Buying {inst} on a {tf} timeframe when {entry_cond} "
        f"under condition ({filter_cond}), exiting on {exit_cond}, "
        f"generates positive risk-adjusted excess returns over buy-and-hold."
    )

    return updated
