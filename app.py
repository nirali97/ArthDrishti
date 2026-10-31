import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from arthdrishti.engine import simulate, build_monthly_projection, financial_health
from arthdrishti.storage import init_db, save_simulation, load_history

st.set_page_config(page_title="ArthDrishti | Financial Intelligence", page_icon="📊", layout="wide")
init_db()

NAVY = "#17324D"
TEAL = "#167D75"
AMBER = "#D28A3C"

# Consistent light corporate theme with explicit foreground/background pairs.
st.markdown("""
<style>
:root { color-scheme: light; }
.stApp { background: #F4F7FA; color: #243746; }
[data-testid="stHeader"] { background: rgba(244,247,250,.96); }
.block-container { padding-top: 1.65rem; padding-bottom: 3rem; max-width: 1460px; }
[data-testid="stSidebar"] { background: #17324D; border-right: 1px solid #28465F; }
[data-testid="stSidebar"] * { color: #F5F8FB !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { background: transparent; border-radius: 8px; padding: 7px 10px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: #28465F; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div { background: #FFFFFF; color: #243746 !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] * { color: #243746 !important; }
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #DCE5EC; border-radius: 13px; padding: 17px 18px; box-shadow: 0 2px 8px rgba(23,50,77,.045); }
[data-testid="stMetricLabel"] p { color: #607487 !important; font-size: .84rem; font-weight: 600; }
[data-testid="stMetricValue"] { color: #17324D !important; font-weight: 700; }
[data-testid="stMetricDelta"] { color: #167D75 !important; }
.hero { background: linear-gradient(115deg,#17324D 0%,#24566B 100%); padding: 27px 30px; border-radius: 16px; color: #FFFFFF; margin: 0 0 22px; box-shadow: 0 8px 22px rgba(23,50,77,.12); }
.hero h1 { color: #FFFFFF !important; margin: 0; font-size: 1.85rem; letter-spacing: -.02em; }
.hero p { color: #E2EDF3 !important; margin: 7px 0 0; font-size: .98rem; }
h1,h2,h3,h4,h5,h6,p,li,label,small { color: #243746; }
h2,h3 { color: #17324D !important; font-weight: 700; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #344B5E; }
.stCaption, [data-testid="stCaptionContainer"] p, .small-note { color: #687D8F !important; }
.stButton > button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button { background: #167D75; color: #FFFFFF !important; border: 1px solid #167D75; border-radius: 9px; font-weight: 650; min-height: 2.55rem; }
.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover, [data-testid="stDownloadButton"] button:hover { background: #11665F; border-color: #11665F; color: #FFFFFF !important; }
.stButton > button p, [data-testid="stFormSubmitButton"] button p, [data-testid="stDownloadButton"] button p { color: #FFFFFF !important; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea { background: #FFFFFF !important; color: #243746 !important; border: 1px solid #C9D6E0 !important; border-radius: 8px; }
[data-testid="stSelectbox"] > div > div, [data-testid="stMultiSelect"] > div > div { background: #FFFFFF !important; color: #243746 !important; border-color: #C9D6E0 !important; }
[data-testid="stSelectbox"] *, [data-testid="stMultiSelect"] * { color: #243746; }
[data-testid="stSlider"] [data-testid="stMarkdownContainer"] p { color: #344B5E !important; }
[data-testid="stFileUploader"] section { background: #FFFFFF; border: 1px dashed #AFC0CD; border-radius: 12px; }
[data-testid="stFileUploader"] section * { color: #344B5E !important; }
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stAlert"] p, [data-testid="stAlert"] li { color: #243746 !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { background: #FFFFFF; border: 1px solid #DCE5EC; border-radius: 10px; }
[data-testid="stExpander"] { background: #FFFFFF; border: 1px solid #DCE5EC; border-radius: 10px; }
hr { border-color: #DCE5EC; }
.js-plotly-plot .plotly text { fill: #344B5E !important; }
@media (max-width: 700px) { .hero { padding: 21px; } .hero h1 { font-size: 1.45rem; } }
</style>
""", unsafe_allow_html=True)

if "profile" not in st.session_state:
    st.session_state.profile = "Personal"
if "finance" not in st.session_state:
    st.session_state.finance = {
        "income": 85000.0, "expenses": 48000.0, "savings": 420000.0,
        "debt": 250000.0, "inflation": 6.0, "income_growth": 4.0
    }

with st.sidebar:
    st.markdown("## ◈ ARTHDRISHTI")
    st.caption("Aaj Se Aage Ki Soch.")
    st.divider()
    profile = st.selectbox("WORKSPACE", ["Personal", "Business"], index=0 if st.session_state.profile=="Personal" else 1)
    st.session_state.profile = profile
    pages = ["Overview", "My Finances" if profile=="Personal" else "Financial Statements",
             "Financial Model", "Scenario Simulator", "Inflation Intelligence",
             "Financial Resilience", "AI Financial Copilot", "Reports & History"]
    page = st.radio("NAVIGATION", pages, label_visibility="collapsed")
    st.divider()
    st.caption("Prototype · Synthetic/demo data")

f = st.session_state.finance
unit = "₹"
is_business = profile == "Business"
income_label = "Monthly revenue" if is_business else "Monthly income"
expense_label = "Operating expenses" if is_business else "Monthly expenses"

def money(x):
    return f"₹{x:,.0f}"

def header(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def projection_chart(df, title="Projected cash position"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.month, y=df.baseline, mode="lines", name="Baseline", line=dict(color=TEAL, width=3)))
    if "scenario" in df:
        fig.add_trace(go.Scatter(x=df.month, y=df.scenario, mode="lines", name="Scenario", line=dict(color="#D98B45", width=3)))
    fig.update_layout(title=title, height=360, margin=dict(l=10,r=10,t=50,b=10),
                      paper_bgcolor="white", plot_bgcolor="white", yaxis_title="Cash balance (₹)",
                      legend=dict(orientation="h", y=1.12), hovermode="x unified", font=dict(color="#344B5E"), xaxis=dict(gridcolor="#E8EEF3", zerolinecolor="#DCE5EC"), yaxis=dict(gridcolor="#E8EEF3", zerolinecolor="#DCE5EC"))
    st.plotly_chart(fig, use_container_width=True)

if page == "Overview":
    header("Your financial future, before it happens.", f"{profile} workspace · {datetime.now().strftime('%d %B %Y')}")
    score = financial_health(f["income"], f["expenses"], f["savings"], f["debt"])
    runway = f["savings"] / max(f["expenses"], 1)
    c = st.columns(4)
    c[0].metric(income_label, money(f["income"]))
    c[1].metric(expense_label, money(f["expenses"]))
    c[2].metric("Available reserves", money(f["savings"]))
    c[3].metric("Cash runway", f"{runway:.1f} months")
    left, right = st.columns([1.65,1])
    with left:
        st.subheader("Financial trajectory")
        df = build_monthly_projection(f, months=24)
        projection_chart(df)
    with right:
        st.subheader("Financial health")
        st.metric("Indicative health score", f"{score}/100")
        st.progress(score/100)
        if runway < 3:
            st.error("Liquidity is tight. Consider testing expense or income shocks.")
        elif runway < 6:
            st.warning("Build additional reserves to improve resilience.")
        else:
            st.success("Current reserve coverage is comparatively strong.")
        st.subheader("Quick actions")
        if st.button("Simulate a financial shock", use_container_width=True):
            st.session_state["jump_sim"] = True
            st.rerun()
    st.caption("All figures are illustrative and based on editable demo assumptions. This is not financial advice.")

elif page in ["My Finances", "Financial Statements"]:
    header("Financial inputs", "Add or import the figures that power your simulations.")
    st.info("This prototype uses a simplified monthly cash-flow model. Uploads are previewed; they are not automatically connected to a bank.")
    with st.form("finance_form"):
        a,b = st.columns(2)
        with a:
            income = st.number_input(income_label, min_value=0.0, value=float(f["income"]), step=1000.0)
            expenses = st.number_input(expense_label, min_value=0.0, value=float(f["expenses"]), step=1000.0)
            savings = st.number_input("Current cash / savings", min_value=0.0, value=float(f["savings"]), step=5000.0)
        with b:
            debt = st.number_input("Outstanding debt", min_value=0.0, value=float(f["debt"]), step=5000.0)
            inflation = st.number_input("Expected annual inflation (%)", min_value=0.0, max_value=50.0, value=float(f["inflation"]))
            growth = st.number_input("Expected annual income / revenue growth (%)", min_value=-50.0, max_value=100.0, value=float(f["income_growth"]))
        submitted = st.form_submit_button("Save financial assumptions", type="primary")
    if submitted:
        st.session_state.finance = dict(income=income, expenses=expenses, savings=savings, debt=debt, inflation=inflation, income_growth=growth)
        st.success("Financial assumptions updated.")
    st.subheader("Import a CSV")
    uploaded = st.file_uploader("Upload a transaction or finance CSV", type=["csv"])
    if uploaded:
        try:
            data = pd.read_csv(uploaded)
            st.write(f"Preview · {len(data)} rows")
            st.dataframe(data.head(100), use_container_width=True)
            st.caption("Prototype limitation: CSV contents are not yet mapped into the simulation automatically.")
        except Exception as e:
            st.error(f"Could not read CSV: {e}")

elif page == "Financial Model":
    header("Financial model", "A simplified view of how money moves through your financial system.")
    st.caption("Conceptual cash-flow graph. The simulation engine currently uses aggregate monthly inflows and outflows.")
    nodes = ["Income / Revenue", "Cash reserves", "Living / Operating costs", "Debt servicing", "Savings / Retained cash"]
    cols = st.columns(5)
    values = [f["income"], f["savings"], f["expenses"], min(f["debt"]*0.02, f["income"]*0.3), max(f["income"]-f["expenses"],0)]
    for col, name, val in zip(cols, nodes, values):
        with col:
            st.metric(name, money(val))
    st.subheader("Cash movement")
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=25, thickness=18, color=[NAVY,TEAL,"#D98B45","#9B7BB5","#4D9C8E"]),
        link=dict(source=[0,1,1,1], target=[1,2,3,4],
                  value=[max(f["income"],1), max(f["expenses"]*.75,1), max(min(f["debt"]*.02,f["income"]*.3),1), max(f["income"]-f["expenses"],1)])
    ))
    fig.update_layout(height=420, margin=dict(l=10,r=10,t=20,b=10), paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color="#243746", size=13))
    st.plotly_chart(fig, use_container_width=True)
    st.warning("This is a conceptual flow visual, not a transaction-level NetworkX DAG yet.")

elif page == "Scenario Simulator":
    header("Scenario simulator", "Change an assumption. See how the financial trajectory responds.")
    st.markdown("#### Build a what-if scenario")
    a,b,c = st.columns(3)
    with a:
        shock = st.slider("Income / revenue change (%)", -80, 50, -15, 1)
    with b:
        cost_change = st.slider("Expense change (%)", -30, 100, 0, 1)
    with c:
        shock_months = st.slider("Shock duration (months)", 1, 24, 12, 1)
    d,e = st.columns(2)
    with d:
        one_off = st.number_input("One-time cash expense (₹)", min_value=0, value=0, step=5000)
    with e:
        extra_reserve = st.number_input("Additional cash / credit (₹)", min_value=0, value=0, step=5000)
    result = simulate(f, income_change=shock, expense_change=cost_change, duration=shock_months,
                      one_off_cost=one_off, extra_cash=extra_reserve, months=24)
    projection_chart(result["projection"], "Baseline vs simulated cash balance")
    x,y,z = st.columns(3)
    x.metric("Baseline month-24 cash", money(result["baseline_end"]))
    y.metric("Scenario month-24 cash", money(result["scenario_end"]), delta=money(result["scenario_end"]-result["baseline_end"]))
    z.metric("Scenario runway", f'{result["runway"]:.1f} months')
    if result["first_negative"]:
        st.error(f"Under these assumptions, cash first falls below zero in month {result['first_negative']}.")
    else:
        st.success("Cash remains above zero throughout the 24-month simulation.")
    st.subheader("What changed?")
    st.write(result["explanation"])
    if st.button("Save this simulation", type="primary"):
        save_simulation(profile, {"income_change":shock,"expense_change":cost_change,"duration":shock_months,
                                  "one_off_cost":one_off,"extra_cash":extra_reserve}, result)
        st.success("Simulation saved to local history.")

elif page == "Inflation Intelligence":
    header("Inflation intelligence", "Understand how rising prices change the future cost of your goals.")
    a,b = st.columns(2)
    with a:
        current_cost = st.number_input("Current cost of a goal (₹)", min_value=0, value=1000000, step=50000)
        years = st.slider("Years until goal", 1, 30, 5)
    with b:
        rate = st.slider("Assumed annual inflation (%)", 0.0, 20.0, float(f["inflation"]), 0.5)
        monthly_budget = st.number_input("Current monthly expense basket (₹)", min_value=0, value=int(f["expenses"]), step=1000)
    future = current_cost * (1+rate/100)**years
    future_monthly = monthly_budget * (1+rate/100)**years
    x,y = st.columns(2)
    x.metric("Estimated future goal cost", money(future), delta=money(future-current_cost))
    y.metric("Future monthly expense basket", money(future_monthly), delta=money(future_monthly-monthly_budget))
    data = pd.DataFrame({"Year":list(range(years+1)), "Goal cost":[current_cost*(1+rate/100)**i for i in range(years+1)]})
    fig = go.Figure(go.Scatter(x=data.Year,y=data["Goal cost"],mode="lines+markers",line=dict(color=TEAL,width=3)))
    fig.update_layout(height=330, title="Illustrative future goal cost", yaxis_title="₹", margin=dict(l=10,r=10,t=50,b=10), paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color="#344B5E"), xaxis=dict(gridcolor="#E8EEF3"), yaxis=dict(gridcolor="#E8EEF3"))
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Uses a constant annual inflation assumption; actual inflation varies over time.")

elif page == "Financial Resilience":
    header("Financial resilience", "Explore how much room you have to absorb an unexpected shock.")
    st.subheader("Stress-test your finances")
    shock_type = st.selectbox("Shock type", ["Temporary income loss", "Expense spike", "Combined shock"])
    if shock_type == "Temporary income loss":
        loss = st.slider("Income reduction (%)", 0, 100, 50)
        duration = st.slider("Duration (months)",1,24,3)
        exp = 0
    elif shock_type == "Expense spike":
        loss = 0
        duration = st.slider("Duration (months)",1,24,6)
        exp = st.slider("Expense increase (%)",0,150,25)
    else:
        loss = st.slider("Income reduction (%)",0,100,30)
        duration = st.slider("Duration (months)",1,24,6)
        exp = st.slider("Expense increase (%)",0,150,20)
    result = simulate(f,income_change=-loss,expense_change=exp,duration=duration,months=24)
    st.metric("Estimated runway under stress",f'{result["runway"]:.1f} months')
    st.metric("Cash after 24 months",money(result["scenario_end"]))
    if result["first_negative"]:
        st.error(f"Liquidity shortfall first appears in month {result['first_negative']}.")
    else:
        st.success("No negative cash balance in this simplified 24-month stress test.")
    projection_chart(result["projection"],"Resilience stress test")

elif page == "AI Financial Copilot":
    header("AI financial copilot", "Ask questions about your assumptions and simulated outcomes.")
    st.info("This is a transparent rule-based prototype, not a connected LLM. It only uses the financial inputs and simulation arithmetic shown here.")
    question = st.text_input("Ask a financial question", placeholder="What happens if my income falls by 20%?")
    if st.button("Analyse question", type="primary") and question.strip():
        q = question.lower()
        if any(w in q for w in ["runway","last","how long"]):
            answer = f"At your current monthly expense level of {money(f['expenses'])}, your cash reserves of {money(f['savings'])} cover approximately {f['savings']/max(f['expenses'],1):.1f} months of expenses, before considering income."
        elif any(w in q for w in ["inflation","future cost","prices"]):
            answer = f"At an assumed {f['inflation']:.1f}% annual inflation rate, a cost today grows by approximately {(1+f['inflation']/100)**5:.2f}x over five years."
        elif any(w in q for w in ["expense","spend","cost"]):
            answer = f"Your current monthly surplus before debt servicing is {money(f['income']-f['expenses'])}. A 10% expense increase would reduce it by {money(f['expenses']*.10)} per month."
        elif any(w in q for w in ["debt","loan","emi"]):
            answer = f"Your recorded outstanding debt is {money(f['debt'])}. This prototype approximates monthly debt servicing as 2% of outstanding debt for the financial model visual; it is not an actual loan amortisation schedule."
        else:
            answer = f"Your current monthly net cash flow before debt servicing is {money(f['income']-f['expenses'])}. Try asking about runway, inflation, expenses, debt or a specific scenario in the simulator."
        st.markdown("### ArthDrishti's analysis")
        st.write(answer)
        st.caption("This response is generated by fixed rules and simplified assumptions, not an LLM or professional financial advice.")

elif page == "Reports & History":
    header("Reports & simulation history", "Review saved what-if analyses and export your results.")
    history = load_history()
    if history.empty:
        st.info("No saved simulations yet. Run a scenario and select 'Save this simulation'.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)
        st.download_button("Download history as CSV",history.to_csv(index=False).encode("utf-8"),"arthdrishti_simulation_history.csv","text/csv")
    st.subheader("Current assumptions")
    st.json(f)
    st.caption("History is stored locally in SQLite on the machine running this prototype.")
