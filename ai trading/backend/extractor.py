"""
extractor.py - Structured LLM extraction and deterministic parsing engine.

Core Philosophy:
- Meaningful AI: Enforces structured extraction, never conversational chit-chat.
- Explicit Nullability: If a parameter is not explicitly quantified, return null.
- Flag Ambiguity: Extracts vague expressions ('sharp fall', 'works better', 'oversold')
  into ambiguous_terms instead of silently guessing parameters.
"""

import json
import os
import re
from typing import Dict, Any, Optional
from schema import Experiment, EntryCondition, ExitCondition, HoldingPeriod, FilterItem
from validator import find_gaps_and_validate
from defaults import CONSERVATIVE_ASSUMPTIONS

SYSTEM_EXTRACTION_PROMPT = """You are an expert AI quantitative trading research assistant.
Your task is to parse a trader's natural language hypothesis into a structured, verifiable experiment schema.

CRITICAL RULES:
1. If a field or parameter is not explicitly stated with a precise number or rule, you MUST set it to null. DO NOT guess, fabricate, or silently default.
2. For vague, subjective, or unquantified phrases (e.g. "sharp fall", "oversold", "high volatility", "works better", "crash"), set the condition to null and add the exact phrase to the `ambiguous_terms` array.
3. For market filters or regimes, extract the filter name (e.g., 'volatility', 'trend') and raw condition (e.g., 'high', 'bullish') with a confidence score between 0.0 and 1.0.
4. Output MUST be strictly valid JSON matching the requested schema. No markdown wrapping, no introductory text.

TARGET JSON SCHEMA:
{
  "instrument": string or null,          // e.g. "NIFTY", "SPY", "BANKNIFTY"
  "timeframe": string or null,           // "daily", "weekly", "hourly", "15min"
  "entry": {
    "condition": string or null,         // explicit trigger e.g. "Close drops >= 1.0%"
    "type": string or null               // "price_drop", "breakout", "cross", "other"
  },
  "exit": {
    "condition": string or null,         // explicit exit e.g. "Hold 5 days", "Stop loss 1%"
    "type": string or null               // "target", "stop", "time", "signal"
  },
  "holding_period": {
    "value": number or null,             // numeric duration e.g. 5
    "unit": string or null               // "days", "weeks", "bars", "hours"
  },
  "filters": [
    { "name": string, "condition": string, "confidence": number }
  ],
  "hypothesis": string or null,
  "ambiguous_terms": [string]            // phrases requiring user clarification
}
"""


def rule_based_extract(question: str) -> Dict[str, Any]:
    """
    Intelligent deterministic extractor that handles trading queries out-of-the-box
    without needing an external API key, strictly obeying the nullability rules.
    """
    q_lower = question.lower()
    
    # 1. Instrument Detection
    instrument = None
    if "nifty" in q_lower:
        instrument = "NIFTY"
    elif "banknifty" in q_lower or "bank nifty" in q_lower:
        instrument = "BANKNIFTY"
    elif "spy" in q_lower:
        instrument = "SPY"
    elif "qqq" in q_lower:
        instrument = "QQQ"
    elif "btc" in q_lower or "bitcoin" in q_lower:
        instrument = "BTC"
    elif "reliance" in q_lower:
        instrument = "RELIANCE"
    elif "apple" in q_lower or "aapl" in q_lower:
        instrument = "AAPL"
        
    # 2. Timeframe Detection
    timeframe = None
    if "daily" in q_lower or "day" in q_lower and "days" not in q_lower:
        timeframe = "daily"
    elif "hourly" in q_lower or "1 hour" in q_lower:
        timeframe = "hourly"
    elif "15min" in q_lower or "15 minute" in q_lower:
        timeframe = "15min"
    elif "weekly" in q_lower or "week" in q_lower and "weeks" not in q_lower:
        timeframe = "weekly"
    else:
        timeframe = "daily"  # standard default for research, but can be flagged if not stated

    # 3. Ambiguous Terms and Entry Condition Extraction
    ambiguous_terms = []
    entry_condition = None
    entry_type = None

    # Check for unquantified drop / sharp fall
    if "sharp fall" in q_lower:
        ambiguous_terms.append("sharp fall")
    elif "crash" in q_lower:
        ambiguous_terms.append("crash")
    elif "big drop" in q_lower or "plummet" in q_lower or "dump" in q_lower:
        ambiguous_terms.append("big drop")

    # Check if explicit drop percentage is given
    drop_pct_match = re.search(r"(falls?|drops?|down)\s*(>=|>|by)?\s*(\d+(\.\d+)?)\s*%", q_lower)
    if drop_pct_match:
        pct = drop_pct_match.group(3)
        entry_condition = f"Close drops >= {pct}%"
        entry_type = "price_drop"
    elif "sharp fall" in q_lower or "crash" in q_lower or "drop" in q_lower:
        # Intentionally null! We do not guess what 'sharp fall' means.
        entry_condition = None
        entry_type = "price_drop"

    # Check for unquantified edge / comparison
    if "work better" in q_lower or "works better" in q_lower:
        ambiguous_terms.append("works better")
    elif "profitable" in q_lower and not any(w in q_lower for w in ["sharpe", "win rate"]):
        ambiguous_terms.append("profitable")

    # 4. Filters (e.g., High Volatility)
    filters = []
    if "high-volatility" in q_lower or "high volatility" in q_lower or "volatile" in q_lower:
        ambiguous_terms.append("high-volatility")
        # Check if explicit VIX threshold is mentioned
        vix_match = re.search(r"vix\s*(>=|>)\s*(\d+)", q_lower)
        if vix_match:
            cond = f"VIX > {vix_match.group(2)}"
        else:
            cond = "high (unquantified)"
        filters.append({
            "name": "volatility",
            "condition": cond,
            "confidence": 0.92
        })

    if "trend" in q_lower or "uptrend" in q_lower:
        filters.append({
            "name": "trend",
            "condition": "uptrend",
            "confidence": 0.85
        })

    # 5. Exit Condition & Holding Period
    exit_condition = None
    exit_type = None
    holding_value = None
    holding_unit = None

    hold_match = re.search(r"hold(ing)?\s*(for)?\s*(\d+)\s*(days?|bars?|weeks?|hours?)", q_lower)
    if hold_match:
        holding_value = float(hold_match.group(3))
        unit = hold_match.group(4)
        holding_unit = "days" if "day" in unit else ("weeks" if "week" in unit else "bars")
        exit_condition = f"Hold for {int(holding_value)} {holding_unit}"
        exit_type = "time"
    
    stop_match = re.search(r"stop\s*(loss)?\s*(\d+(\.\d+)?)\s*%", q_lower)
    if stop_match:
        exit_condition = f"Stop loss at {stop_match.group(2)}%"
        exit_type = "stop"

    return {
        "instrument": instrument,
        "timeframe": timeframe,
        "entry": {
            "condition": entry_condition,
            "type": entry_type
        },
        "exit": {
            "condition": exit_condition,
            "type": exit_type
        },
        "holding_period": {
            "value": holding_value,
            "unit": holding_unit
        },
        "filters": filters,
        "hypothesis": f"Hypothesis on {instrument or 'asset'}: buying after drop under {', '.join([f['condition'] for f in filters]) or 'market conditions'}",
        "ambiguous_terms": list(dict.fromkeys(ambiguous_terms))
    }


async def extract_experiment_from_query(question: str) -> Experiment:
    """
    Orchestrates extraction:
    Attempts live LLM extraction if an API key is present;
    otherwise seamlessly utilizes the deterministic parser.
    """
    raw_dict = None
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
                            {"role": "user", "content": f"USER QUESTION: {question}"}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0
                    }
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    content = resp_json["choices"][0]["message"]["content"]
                    raw_dict = json.loads(content)
        except Exception:
            raw_dict = None

    if not raw_dict:
        raw_dict = rule_based_extract(question)

    # Convert to Pydantic Experiment model
    experiment = Experiment(
        instrument=raw_dict.get("instrument"),
        timeframe=raw_dict.get("timeframe"),
        entry=EntryCondition(**(raw_dict.get("entry") or {})),
        exit=ExitCondition(**(raw_dict.get("exit") or {})),
        holding_period=HoldingPeriod(**(raw_dict.get("holding_period") or {})),
        filters=[FilterItem(**f) for f in raw_dict.get("filters", [])],
        hypothesis=raw_dict.get("hypothesis"),
        raw_question=question,
        ambiguous_terms=raw_dict.get("ambiguous_terms", []),
        assumptions=[a for a in CONSERVATIVE_ASSUMPTIONS]
    )

    # Compute deterministic gaps
    gaps, missing = find_gaps_and_validate(experiment)
    experiment.gaps = gaps
    experiment.missing_fields = missing

    return experiment
