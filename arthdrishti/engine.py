import pandas as pd

def financial_health(income, expenses, savings, debt):
    if income <= 0:
        return 0
    savings_ratio = min(savings / max(expenses * 6, 1), 1)
    surplus_ratio = max(min((income-expenses)/income, 1), 0)
    debt_ratio = min(debt / max(income*12, 1), 1)
    score = 35*savings_ratio + 45*surplus_ratio + 20*(1-debt_ratio)
    return int(round(max(0,min(score,100))))

def build_monthly_projection(finance, months=24):
    income, expenses = finance["income"], finance["expenses"]
    cash = finance["savings"]
    inflation = finance.get("inflation",6)/100
    growth = finance.get("income_growth",4)/100
    rows=[]
    for m in range(months+1):
        if m > 0:
            inc = income*((1+growth)**(m/12))
            exp = expenses*((1+inflation)**(m/12))
            cash += inc-exp
        rows.append({"month":f"M{m}" if m else "Now","baseline":round(cash,2)})
    return pd.DataFrame(rows)

def simulate(finance, income_change=0, expense_change=0, duration=12,
             one_off_cost=0, extra_cash=0, months=24):
    income, expenses = finance["income"], finance["expenses"]
    inflation = finance.get("inflation",6)/100
    growth = finance.get("income_growth",4)/100
    base_cash = finance["savings"]
    baseline, scenario = base_cash, base_cash + extra_cash - one_off_cost
    rows=[{"month":"Now","baseline":baseline,"scenario":scenario}]
    first_negative = 0 if scenario < 0 else None
    explanation=[]
    for m in range(1,months+1):
        inc = income*((1+growth)**(m/12))
        exp = expenses*((1+inflation)**(m/12))
        baseline += inc-exp
        shocked_inc = inc*(1+income_change/100) if m <= duration else inc
        shocked_exp = exp*(1+expense_change/100) if m <= duration else exp
        scenario += shocked_inc-shocked_exp
        rows.append({"month":f"M{m}","baseline":round(baseline,2),"scenario":round(scenario,2)})
        if scenario < 0 and first_negative is None:
            first_negative = m
    net_monthly = income*(1+income_change/100)-expenses*(1+expense_change/100)
    runway = max(0, scenario / max(-net_monthly,1)) if net_monthly < 0 else float("inf")
    if income_change:
        explanation.append(f"Income/revenue changes by {income_change}% for {duration} months.")
    if expense_change:
        explanation.append(f"Expenses change by {expense_change}% for {duration} months.")
    if one_off_cost:
        explanation.append(f"A one-time cash expense of ₹{one_off_cost:,.0f} is applied at the start.")
    if extra_cash:
        explanation.append(f"Additional cash/credit of ₹{extra_cash:,.0f} is added at the start.")
    if not explanation:
        explanation.append("No shock was applied; this is the baseline trajectory.")
    if first_negative:
        explanation.append(f"Projected cash first falls below zero in month {first_negative}.")
    else:
        explanation.append("Projected cash remains non-negative over the selected horizon.")
    return {"projection":pd.DataFrame(rows),"baseline_end":round(baseline,2),
            "scenario_end":round(scenario,2),"runway":round(runway,1) if runway != float("inf") else 999.0,
            "first_negative":first_negative,"explanation":" ".join(explanation)}
