"""
schema.py - Pydantic models for the AI Trading Research Assistant.

Key Design Decision:
Fields are nullable rather than optional. This forces the system to explicitly
track what is missing rather than silently defaulting or hallucinating.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class EntryCondition(BaseModel):
    condition: Optional[str] = Field(
        default=None, 
        description="Explicit entry condition expression (e.g. 'falls >= 1%'). Null if vague or omitted."
    )
    type: Optional[Literal["price_drop", "breakout", "cross", "other"]] = Field(
        default=None,
        description="Category of the entry trigger."
    )


class ExitCondition(BaseModel):
    condition: Optional[str] = Field(
        default=None,
        description="Explicit exit rule expression (e.g. 'holding period expires', 'target hit')."
    )
    type: Optional[Literal["target", "stop", "time", "signal"]] = Field(
        default=None,
        description="Exit mechanism category."
    )


class HoldingPeriod(BaseModel):
    value: Optional[float] = Field(
        default=None,
        description="Holding duration magnitude."
    )
    unit: Optional[Literal["days", "weeks", "bars", "hours", "minutes"]] = Field(
        default=None,
        description="Holding duration unit."
    )


class FilterItem(BaseModel):
    name: str = Field(description="Filter name, e.g., 'volatility', 'trend', 'volume'")
    condition: str = Field(description="Filter condition, e.g., 'high', 'VIX > 20', 'above 200 SMA'")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score of the extraction (0 to 1)")


class AssumptionItem(BaseModel):
    field: str = Field(description="Target field of the assumption")
    assumed_value: str = Field(description="Value conservatively assumed by system")
    reason: str = Field(description="Why this default assumption was made")


class Gap(BaseModel):
    field: str = Field(description="Path to the missing or ambiguous field")
    question: str = Field(description="Direct question prompting the user for clarification")
    severity: Literal["required", "clarification", "optional"] = Field(
        description="Required blocks testing; clarification refines terms; optional provides safe defaults"
    )
    suggested_options: List[str] = Field(
        default_factory=list,
        description="Clickable/selectable suggested options to reduce user friction"
    )
    current_value: Optional[str] = Field(
        default=None,
        description="Current value or null"
    )


class Experiment(BaseModel):
    instrument: Optional[str] = Field(
        default=None,
        description="Traded asset or ticker (e.g. 'NIFTY', 'SPY', 'BANKNIFTY'). Null if unspecified."
    )
    timeframe: Optional[Literal["daily", "weekly", "hourly", "15min", "5min"]] = Field(
        default=None,
        description="Timeframe for the strategy bar data."
    )
    entry: EntryCondition = Field(default_factory=EntryCondition)
    exit: ExitCondition = Field(default_factory=ExitCondition)
    holding_period: HoldingPeriod = Field(default_factory=HoldingPeriod)
    filters: List[FilterItem] = Field(default_factory=list)
    hypothesis: Optional[str] = Field(
        default=None,
        description="Synthesized testable hypothesis statement."
    )
    
    # Metadata & Gap Tracking
    raw_question: str = Field(default="", description="Original natural language query from user")
    ambiguous_terms: List[str] = Field(
        default_factory=list,
        description="Vague or unquantified terms flagged during extraction (e.g., 'sharp fall', 'better')"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="List of dot-notated paths to required fields currently null"
    )
    assumptions: List[AssumptionItem] = Field(
        default_factory=list,
        description="Explicit assumptions made by system"
    )
    gaps: List[Gap] = Field(
        default_factory=list,
        description="Structured gaps identified for user resolution"
    )


class ParseRequest(BaseModel):
    question: str


class ClarifySubmission(BaseModel):
    experiment: Experiment
    clarifications: Dict[str, Any]  # Key: field_path, Value: user-selected or typed value


class BacktestRequest(BaseModel):
    experiment: Experiment
    sample_period_years: int = 10
    transaction_cost_pct: float = 0.05
    slippage_pct: float = 0.02
