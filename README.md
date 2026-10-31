# ArthDrishti — Financial Intelligence Prototype

A runnable Streamlit prototype based on the ArthDrishti concept deck.

## Features
- Personal and Business workspaces
- Overview dashboard with financial KPIs and a 24-month trajectory
- Editable financial assumptions
- CSV upload and preview
- Conceptual cash-flow model visualization
- Deterministic what-if simulator (income/revenue, expenses, one-time cash cost, extra cash)
- Inflation goal-cost calculator
- Financial resilience stress test
- Rule-based financial copilot (no LLM)
- SQLite simulation history and CSV export

## Run locally

Python 3.10+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (usually http://localhost:8501).

## Important prototype limitations
- All default values are synthetic demo assumptions.
- This is not connected to bank accounts, ERP systems or live market data.
- CSV upload currently previews data only; it does not map transactions into the model.
- The financial model graphic is conceptual, not a transaction-level NetworkX DAG.
- The simulation uses a simplified monthly cash-flow equation, not a trained ML model.
- The copilot uses fixed rules, not Gemini/LLaMA or LangGraph.
- No authentication, multi-user access control, or production security is implemented.
- Outputs are educational prototypes, not financial advice.

## Simplified simulation logic
Each month:
- Baseline income grows at the assumed annual growth rate.
- Baseline expenses grow at the assumed annual inflation rate.
- Scenario income and expenses receive the selected shock for the chosen duration.
- One-time cash expense and additional cash are applied at the start.
- The engine tracks monthly cash balance and the first month it becomes negative.

The same arithmetic engine powers Personal and Business workspaces; labels and context differ.
# ArthDrishti
