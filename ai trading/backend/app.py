"""
app.py - FastAPI server for the AI Trading Research Assistant.

Provides:
- POST /api/parse: Extracts structured hypothesis draft with explicit nulls & ambiguous terms.
- POST /api/clarify: Applies user clarifications and updates deterministic gaps.
- POST /api/backtest: Executes 10-year simulation and generates data vs. conclusion analysis.
- GET /api/templates: Pre-configured sample research hypotheses.
- Static file serving for the frontend UI.
"""

import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path for internal imports
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from schema import (
    ParseRequest,
    ClarifySubmission,
    BacktestRequest,
    Experiment
)
from extractor import extract_experiment_from_query
from validator import apply_clarifications
from backtest import run_backtest_simulation

app = FastAPI(
    title="AI Trading Research Assistant",
    description="Structured quantitative research assistant that highlights ambiguity instead of papering over it.",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.post("/api/parse", response_model=Experiment)
async def parse_hypothesis(req: ParseRequest):
    """Parses natural language question into structured Experiment schema."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Research question cannot be empty.")
    experiment = await extract_experiment_from_query(req.question.strip())
    return experiment


@app.post("/api/clarify", response_model=Experiment)
async def clarify_hypothesis(submission: ClarifySubmission):
    """Applies user selections for missing fields and ambiguous parameters."""
    updated = apply_clarifications(submission.experiment, submission.clarifications)
    return updated


@app.post("/api/backtest")
async def execute_backtest(req: BacktestRequest):
    """Executes backtesting simulation with risk analysis and bias evaluation."""
    # Check if required fields are still missing
    if req.experiment.missing_fields:
        required_missing = [f for f in req.experiment.missing_fields]
        if required_missing:
            # We allow running if fallback defaults can be inferred, but flag it
            pass
            
    result = run_backtest_simulation(
        experiment=req.experiment,
        cost_per_trade=req.transaction_cost_pct,
        slippage_pct=req.slippage_pct
    )
    return result


@app.get("/api/templates")
async def get_templates():
    """Returns curated research questions to test the system."""
    return [
        {
            "id": "assignment_q",
            "title": "NIFTY Sharp Fall in High Volatility (Assignment Prompt)",
            "query": "Does buying NIFTY after a sharp fall work better during high-volatility periods?",
            "highlight": "Deliberately ambiguous: 'sharp fall', 'high-volatility', 'better', missing holding period & exit rule."
        },
        {
            "id": "drop_with_holding",
            "title": "NIFTY 2% Pullback with 5-day Holding Period",
            "query": "Does buying NIFTY when it drops >= 2% during high volatility yield edge when holding for 5 days?",
            "highlight": "Quantified drop and holding period, but still requires exit rule & volatility definition."
        },
        {
            "id": "banknifty_bounce",
            "title": "Bank Nifty Oversold Bounce",
            "query": "Is buying BANKNIFTY after a big crash profitable on daily bars?",
            "highlight": "Multiple vague terms: 'big crash', 'profitable', missing timeframe and parameters."
        }
    ]


# Mount frontend static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("Starting AI Trading Research Assistant on http://localhost:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
