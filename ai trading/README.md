# AI Trading Research Assistant — Mini Prototype

An AI-native trading research assistant demonstrating **product thinking**, **structured extraction**, **deterministic ambiguity detection**, and **quantitative epistemics** ("what the data shows vs. what we conclude").

---

## 🌟 Key Highlights & Philosophy

1. **Not a Chatbot Wrapper**: Replaces chat dialogues with an interactive 4-step scientific workflow:
   $$\text{Step 1: Ask} \longrightarrow \text{Step 2: Clarify} \longrightarrow \text{Step 3: Define} \longrightarrow \text{Step 4: Test}$$
2. **Explicit Nullability**: Fields left unstated by the user return `null` instead of being silently filled by the LLM.
3. **Deterministic Gap Detection**: Python validator categorizes ambiguities into:
   - **Required Gaps**: Blocks testing until quantified (e.g. entry drop %, exit rule, holding duration).
   - **Clarification Gaps**: Clarifies subjective phrases (e.g. *"sharp fall"*, *"high volatility"*, *"works better"*).
   - **Conservative Assumptions**: Explicitly logs defaults (10-year test window, 0.05% cost, 0.02% slippage).
4. **Epistemic Rigor in Testing**: Side-by-side breakdown of **"What the Data Shows"** (58% win rate, +0.42% avg return) vs. **"What We Conclude"** (sample size fragility, regime clustering, parameter sensitivity, look-ahead bias warnings).

---

## 🏗️ Architecture

```
ai-trading/
├── backend/
│   ├── app.py              # FastAPI application & API endpoints
│   ├── schema.py           # Pydantic ExperimentSchema with nullable fields
│   ├── extractor.py        # LLM prompt builder + structured parsing engine
│   ├── validator.py        # Deterministic Gap Detection (Required, Clarification, Assumptions)
│   ├── backtest.py         # 10-year NIFTY & VIX backtesting engine with realistic friction
│   └── defaults.py         # Conservative defaults and bias warnings
├── frontend/
│   ├── index.html          # Semantic modern UI structure
│   ├── style.css           # Obsidian dark mode design system with glassmorphism
│   └── app.js              # State machine for the 4-step workflow + SVG equity curve
├── docs/
│   ├── THINKING_NOTE.md    # Option 2 deep dive: Biases, parameters, questions vs assumptions
│   └── AI_USAGE_NOTE.md    # Transparent AI usage declaration and architectural defense
├── tests/
│   └── test_backend.py     # Unit tests for schema, validator, extractor, and simulation
├── run.py                  # Single-command application launcher
└── README.md
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Installed packages: `fastapi`, `uvicorn`, `pydantic`, `httpx`

### 1. Run Unit Tests
```bash
python -m unittest discover -s tests
```
*Runs 5 test suites covering schema nullability, assignment prompt extraction, gap detection severity, clarification application, and backtest simulations.*

### 2. Launch the Prototype
```bash
python run.py
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 🧪 Guided Test Workflow

1. **Step 1: Ask**
   - Click the pre-loaded sample chip:
     > *"Does buying NIFTY after a sharp fall work better during high-volatility periods?"*
   - Click **Extract & Detect Gaps**.
2. **Step 2: Clarify**
   - Notice how the system flags that `"sharp fall"`, `"high-volatility"`, and `"works better"` are unquantified.
   - Click one of the suggested threshold chips (e.g. `Close drop >= 1.0%`, `5 days`, `Time-based`).
   - Observe the Conservative Assumptions sidebar logging test dates, costs, and execution timing.
3. **Step 3: Define**
   - Review the structured **Experiment Card** displaying the formal hypothesis and verified parameters.
4. **Step 4: Test & Analyze**
   - View the 10-year equity curve, win rate, Sharpe ratio, and drawdown.
   - Study the **"What the Data Shows vs. What We Conclude"** panel.
   - Inspect the **Parameter Sensitivity Check** table to verify if the edge is robust or overfit.
   - Export the complete experiment specification as a JSON artifact.

---

## 📚 Documentation
- [THINKING_NOTE.md](file:///c:/Users/Aswin.R.J/ai%20trading/docs/THINKING_NOTE.md): Option 2 analysis on parameters, biases, minimum questions, and epistemic boundaries.
- [AI_USAGE_NOTE.md](file:///c:/Users/Aswin.R.J/ai%20trading/docs/AI_USAGE_NOTE.md): Full breakdown of AI usage, human design choices, and interview defense points.
