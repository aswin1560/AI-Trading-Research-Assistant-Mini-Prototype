"""
test_backend.py - Unit tests for Schema, Validator, Extractor, and Backtest logic.
"""

import sys
import os
import unittest

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from schema import Experiment, EntryCondition, ExitCondition, HoldingPeriod, FilterItem
from validator import find_gaps_and_validate, apply_clarifications
from extractor import rule_based_extract
from backtest import run_backtest_simulation


class TestTradingResearchBackend(unittest.TestCase):

    def test_schema_nullability_and_tracking(self):
        """Verify that missing fields explicitly default to None rather than guessing."""
        exp = Experiment(raw_question="Test query")
        self.assertIsNone(exp.instrument)
        self.assertIsNone(exp.timeframe)
        self.assertIsNone(exp.entry.condition)
        self.assertIsNone(exp.exit.condition)
        self.assertIsNone(exp.holding_period.value)

    def test_assignment_prompt_extraction(self):
        """Test extraction of the assignment prompt."""
        query = "Does buying NIFTY after a sharp fall work better during high-volatility periods?"
        parsed = rule_based_extract(query)
        
        self.assertEqual(parsed["instrument"], "NIFTY")
        # Entry condition should be null because 'sharp fall' is vague
        self.assertIsNone(parsed["entry"]["condition"])
        # Ambiguous terms should flag 'sharp fall' and 'works better'
        self.assertIn("sharp fall", parsed["ambiguous_terms"])
        self.assertIn("works better", parsed["ambiguous_terms"])
        # High volatility filter should be extracted
        vol_filter = next((f for f in parsed["filters"] if f["name"] == "volatility"), None)
        self.assertIsNotNone(vol_filter)

    def test_gap_detection_severity(self):
        """Verify that missing entry/exit/holding are flagged as required gaps."""
        query = "Does buying NIFTY after a sharp fall work better during high-volatility periods?"
        parsed = rule_based_extract(query)
        
        exp = Experiment(
            instrument=parsed["instrument"],
            timeframe=parsed["timeframe"],
            entry=EntryCondition(**parsed["entry"]),
            exit=ExitCondition(**parsed["exit"]),
            holding_period=HoldingPeriod(**parsed["holding_period"]),
            filters=[FilterItem(**f) for f in parsed["filters"]],
            raw_question=query,
            ambiguous_terms=parsed["ambiguous_terms"]
        )
        
        gaps, missing = find_gaps_and_validate(exp)
        
        # entry.condition, exit.condition, and holding_period.value MUST be missing
        self.assertIn("entry.condition", missing)
        self.assertIn("exit.condition", missing)
        self.assertIn("holding_period.value", missing)
        
        required_gaps = [g for g in gaps if g.severity == "required"]
        self.assertTrue(len(required_gaps) >= 3)

    def test_apply_clarifications(self):
        """Verify that applying user selections populates the fields and updates gaps."""
        exp = Experiment(
            instrument="NIFTY",
            timeframe="daily",
            raw_question="Does buying NIFTY after a sharp fall work better during high-volatility periods?",
            ambiguous_terms=["sharp fall", "works better"]
        )
        
        clarifications = {
            "entry.condition": "Close drop >= 1.0%",
            "exit.condition": "Time-based (Hold for 5 days)",
            "holding_period.value": "5 days",
            "clarification.volatility_threshold": "India VIX > 20"
        }
        
        updated = apply_clarifications(exp, clarifications)
        
        self.assertEqual(updated.entry.condition, "Close drop >= 1.0%")
        self.assertEqual(updated.holding_period.value, 5.0)
        self.assertEqual(updated.holding_period.unit, "days")
        self.assertIn("5 days", updated.exit.condition)
        self.assertTrue(len(updated.missing_fields) == 0)
        self.assertIsNotNone(updated.hypothesis)

    def test_backtest_simulation_and_epistemic_analysis(self):
        """Verify backtest metrics calculation and 'what data shows vs what we conclude'."""
        exp = Experiment(
            instrument="NIFTY",
            timeframe="daily",
            entry=EntryCondition(condition="Close drop >= 1.0%", type="price_drop"),
            exit=ExitCondition(condition="Time-based (Hold for 5 days)", type="time"),
            holding_period=HoldingPeriod(value=5.0, unit="days"),
            filters=[FilterItem(name="volatility", condition="VIX > 20", confidence=0.9)]
        )
        
        results = run_backtest_simulation(exp, cost_per_trade=0.05, slippage_pct=0.02)
        
        summary = results["summary"]
        self.assertGreater(summary["total_trades"], 0)
        self.assertGreater(summary["win_rate"], 0)
        self.assertIn("what_data_shows", results["epistemic_analysis"])
        self.assertIn("what_we_conclude", results["epistemic_analysis"])
        self.assertTrue(len(results["equity_curve"]) > 10)
        self.assertTrue(len(results["sensitivity"]) == 5)


if __name__ == "__main__":
    unittest.main()
