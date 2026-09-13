# AI Usage Note & Architectural Defense

## 1. AI Tools Used
- **Antigravity AI Assistant** (Powered by Gemini 3.8 Flash / Advanced Agentic Coding)
- **GPT-4o / Claude** for comparative prompt refinement and schema stress testing.

---

## 2. What AI Was Used For
- **Prompt Engineering**: Formulated the structured extraction prompt with explicit anti-hallucination negative constraints: *"If a parameter is not explicitly stated, return null. DO NOT guess."*
- **Schema & Type Boilerplate**: Scaffolding initial Pydantic schema representations matching Zod specifications.
- **Dataset Synthesis**: Writing a realistic, deterministic market simulator generating 10 years of NIFTY 50 and India VIX daily returns with historical volatility clustering (COVID crash 2020, 2022 rate hike cycles).
- **Unit Test Scaffolding**: Drafting initial test assertions in `tests/test_backend.py`.

---

## 3. What Was Designed by Human Ingenuity
- **The Core Product Thesis**: Recognizing that the assignment is an exercise in product thinking and epistemology, not high-frequency execution.
- **Explicit Nullability over Silent Defaults**: Forcing unstated parameters to remain `null` rather than silently assigning standard values.
- **Three-Tier Gap Severity Architecture**:
  - `required`: Blocks experiment until user specifies a value (e.g., entry drop %).
  - `clarification`: Clarifies subjective language (e.g., "sharp fall measurement basis", "volatility threshold").
  - `optional`: Exposes conservative assumptions (e.g., 2015-2024 test window, 0.05% friction).
- **The 4-Step User Experience**: Replacing chat bubbles with a guided scientific workflow:
  $$\text{Ask} \longrightarrow \text{Clarify} \longrightarrow \text{Define} \longrightarrow \text{Test}$$
- **The Epistemic Separation in Analytics**:
  Dividing results into **"What the Data Shows"** (pure descriptive statistics) vs. **"What We Conclude"** (critical warnings on sample size, regimes, and overfitting).

---

## 4. What Was Rejected / Modified
- ❌ **Rejected AI Suggestion 1**: *Building a conversational streaming chatbot.*
  - *Why*: Chat interfaces encourage passive acceptance and hand-waving explanations. A structured form with cards and interactive chips enforces intellectual discipline.
- ❌ **Rejected AI Suggestion 2**: *Auto-filling missing values with market norms (e.g., automatically setting sharp fall = 2%).*
  - *Why*: Auto-filling masks ambiguity. The system's value is making incompleteness visible.
- ❌ **Modified AI Suggestion 3**: *Single unified LLM call for extraction + validation + testing.*
  - *Why*: LLMs are good at extracting messy natural language, but notoriously poor at deterministic validation and numerical calculation. We separated LLM extraction from pure deterministic Python validation and backtesting.

---

## 5. Key Decisions to Defend in an Interview

1. **Why Schema-First with Explicit Nulls?**
   - In financial research, an unstated variable is a risk. Optional fields in typical APIs default silently; explicit `null` fields force runtime gap detection.

2. **Why Separate Extraction and Validation?**
   - Natural language extraction is stochastic. Validation must be deterministic and rule-bound. Keeping them decoupled ensures testability and prevents hallucinations.

3. **Why Include Parameter Sensitivity Analysis?**
   - Any single threshold (e.g., 1.0%) can look artificially profitable due to luck. Showing performance across a gradient of thresholds (0.5% to 2.5%) instantly reveals if an edge is real or curve-fitted.

4. **Why Mock Historical Data with Seeded Regimes?**
   - The purpose of this prototype is validating research workflow and user interaction, not paying API fees for live exchange feeds. A seeded realistic dataset provides 100% reproducible, multi-regime backtests.
