"""Adversarial persona tests for the Retirement Planning Service app (post-fix)."""
import sys
import importlib.util

import pathlib
APP = str(pathlib.Path(__file__).resolve().parents[1] / "projection30_10.py")
results = []

def record(persona, attack, outcome, detail=""):
    results.append((persona, attack, outcome, detail))
    print(f"[{outcome}] {persona} — {attack}")
    if detail:
        print(f"        {detail}")

# ---------------------------------------------------------------- UI personas
from streamlit.testing.v1 import AppTest

def fresh():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at

def widget(at, kind, label):
    for w in getattr(at.sidebar, kind):
        if w.label == label:
            return w
    raise KeyError(f"{kind} '{label}' not found")

def check_clean(at, persona, attack):
    excs = [f"{e.type}: {e.message}" for e in at.exception]
    if excs:
        record(persona, attack, "CRASH", "; ".join(excs)[:300])
        return False
    record(persona, attack, "PASS")
    return True

# P1: Doris, 78, just types her age
at = fresh()
try:
    widget(at, "number_input", "Current Age").set_value(78)
    at.run()
    check_clean(at, "P1 Doris (78)", "age 78 with default retirement age")
except Exception as e:
    record("P1 Doris (78)", "age 78 with default retirement age", "CRASH", str(e)[:300])

# P2: Bill, exactly 100
at = fresh()
try:
    widget(at, "number_input", "Current Age").set_value(100)
    at.run()
    if check_clean(at, "P2 Bill (100)", "boundary age 100 loads"):
        at.button[0].click()
        at.run()
        check_clean(at, "P2 Bill (100)", "full projection at age 100")
except Exception as e:
    record("P2 Bill (100)", "boundary age 100", "CRASH", str(e)[:300])

# P3: Rita retiring at 85
at = fresh()
try:
    widget(at, "number_input", "Target Retirement Age").set_value(85)
    at.run()
    check_clean(at, "P3 Rita (retire at 85)", "income end age must clamp to 100")
except Exception as e:
    record("P3 Rita (retire at 85)", "retire at 85", "CRASH", str(e)[:300])

# P8: Zara, zero everything
at = fresh()
try:
    widget(at, "number_input", "Current Annual Salary (£)").set_value(0)
    widget(at, "number_input", "Current Pension Fund Value (£)").set_value(0)
    widget(at, "number_input", "Your Monthly Pension Contribution (£)").set_value(0)
    widget(at, "number_input", "Employer Monthly Pension Contribution (£)").set_value(0)
    at.run()
    at.button[0].click()
    at.run()
    check_clean(at, "P8 Zara (all zeros)", "zero salary/fund/contributions projection")
except Exception as e:
    record("P8 Zara (all zeros)", "all-zero projection", "CRASH", str(e)[:300])

# P9: Max the millionaire via the real UI
at = fresh()
try:
    widget(at, "number_input", "Current Pension Fund Value (£)").set_value(10_000_000)
    widget(at, "selectbox", "Choose an option:").select("Full tax-free cash")
    at.run()
    at.button[0].click()
    at.run()
    check_clean(at, "P9 Max (£10m fund)", "full TFC via UI")
except Exception as e:
    record("P9 Max (£10m fund)", "full TFC via UI", "CRASH", str(e)[:300])

# ------------------------------------------------------- direct model attacks
spec = importlib.util.spec_from_file_location("app", APP)
m = importlib.util.module_from_spec(spec)
sys.modules["app"] = m
spec.loader.exec_module(m)
EN = m.assumptions["tax_bands_england"]
SC = m.assumptions["tax_bands_scotland"]
LSA = m.assumptions["lump_sum_allowance"]

def project(**kw):
    base = dict(current_age=55, retirement_age=65, initial_fund=50000,
        monthly_contribution=0, monthly_employer_contribution=0,
        investment_growth_rate=0.03, salary_growth_rate=0.0, inflation_rate=0.02,
        target_income=20000, annual_retirement_income=20000,
        include_state_pension=False, include_db_pension=False,
        db_pension_income=0, db_pension_age=65, income_start_age=65, income_end_age=85,
        tax_free_cash_option="No tax-free cash", strategy="Accumulation",
        max_age=92, tax_bands=EN)
    base.update(kw)
    return m.project_pension(**base)

# A1: conservation of money — fund + payouts can never exceed fund + growth
def conservation(name, **kw):
    y, u, c, t, inc, tax, net, sf = project(**kw)
    neg = [(int(y[i]), round(min(u[i], c[i]))) for i in range(len(y)) if u[i] < -0.01 or c[i] < -0.01]
    conjured = []
    for i in range(1, len(y)):
        delta = t[i] - t[i-1] + inc[i]
        if delta > t[i-1] * 0.05 + 1:
            conjured.append(int(y[i]))
    if neg:
        record(name, "no negative funds", "FAIL", f"negative pot at ages {neg}")
    elif conjured:
        record(name, "conservation of money", "FAIL", f"money conjured at ages {conjured}")
    else:
        record(name, "conservation + no negative funds", "PASS")

conservation("A1a small fund drawdown", initial_fund=20000)
conservation("A1b big fund drawdown", initial_fund=500000, annual_retirement_income=60000,
              target_income=60000)
conservation("A1c stagflation decumulation", strategy="Decumulation Income (capital)",
              retirement_age=58, initial_fund=100000, immediate_capital_goal=25000,
              investment_growth_rate=0.0, inflation_rate=0.10,
              income_start_age=58, annual_retirement_income=0, target_income=0)

# A2: immediate capital goal honoured in the DEFAULT decumulation setup
y, u, c, t, inc, tax, net, sf = project(strategy="Decumulation Income (capital)",
    retirement_age=55, initial_fund=100000, immediate_capital_goal=25000,
    income_start_age=55, income_end_age=55, annual_retirement_income=0, target_income=0)
if abs(inc[0] - 25000) < 1 and abs(tax[0]) < 0.01:
    record("A2 immediate-goal", "£25k immediate tax-free capital, retiring now", "PASS")
else:
    record("A2 immediate-goal", "£25k immediate tax-free capital, retiring now",
           "FAIL", f"year-1 income £{inc[0]:,.0f} (tax £{tax[0]:,.0f}), expected £25,000 tax-free")

# A3: UFPLS + income top-up taxed correctly
y, u, c, t, inc, tax, net, sf = project(initial_fund=300000, tax_free_cash_option="UFPLS",
    ufpls_amount=100000, annual_retirement_income=150000, target_income=150000)
i65 = list(y).index(65)
correct = m.calculate_taxes(75000, EN)  # taxable = 75% of UFPLS; top-up slice is tax-free
if abs(tax[i65] - correct) < 1:
    record("A3 UFPLS-tax", "£100k UFPLS + £50k tax-free top-up", "PASS",
           f"tax £{tax[i65]:,.0f} matches hand-computed £{correct:,.0f}")
else:
    record("A3 UFPLS-tax", "£100k UFPLS + £50k tax-free top-up", "FAIL",
           f"model tax £{tax[i65]:,.0f}, correct £{correct:,.0f}")

# A4: tax engine spot-checks (2026/27 bands)
checks = [
    ("England £60,000", 60000, EN, (50270-12570)*0.20 + (60000-50270)*0.40),
    ("England £12,570 (PA boundary)", 12570, EN, 0.0),
    ("Scotland £60,000", 60000, SC,
     (16537-12570)*0.19 + (29526-16537)*0.20 + (43662-29526)*0.21 + (60000-43662)*0.42),
    ("Scotland £130,000 (top rate)", 130000, SC,
     (16537-12570)*0.19 + (29526-16537)*0.20 + (43662-29526)*0.21
     + (75000-43662)*0.42 + (125140-75000)*0.45 + (130000-125140)*0.48),
    ("England £0", 0, EN, 0.0),
    ("England £-5,000 (negative)", -5000, EN, 0.0),
]
bad = [f"{n}: got £{m.calculate_taxes(i, b):,.2f}, expected £{e:,.2f}"
       for n, i, b, e in checks if abs(m.calculate_taxes(i, b) - e) > 0.01]
record("A4 tax-engine", "hand-computed 2026/27 tax comparisons",
       "FAIL" if bad else "PASS", "; ".join(bad))

# A5: LSA cap — £10m fund gets exactly £268,275 tax-free, remainder taxable
y, u, c, t, inc, tax, net, sf = project(initial_fund=10_000_000,
    tax_free_cash_option="Full tax-free cash")
i65 = list(y).index(65)
if abs(inc[i65] - LSA) < 1 and tax[i65] < 0.01:
    record("A5 LSA-cap", "£10m fund, full TFC", "PASS",
           f"tax-free cash capped at £{LSA:,} exactly")
else:
    record("A5 LSA-cap", "£10m fund, full TFC", "FAIL",
           f"year-65 income £{inc[i65]:,.0f}, tax £{tax[i65]:,.0f}, expected £{LSA:,} tax-free")

# A5b: LSA is a LIFETIME cap — existing withdrawals reduce what's left
y, u, c, t, inc, tax, net, sf = project(initial_fund=10_000_000,
    tax_free_cash_option="Full tax-free cash", existing_tfc_withdrawals=200000)
i65 = list(y).index(65)
if abs(inc[i65] - (LSA - 200000)) < 1:
    record("A5b LSA-lifetime", "£200k already taken elsewhere", "PASS")
else:
    record("A5b LSA-lifetime", "£200k already taken elsewhere", "FAIL",
           f"granted £{inc[i65]:,.0f} tax-free, expected £{LSA-200000:,}")

# A6: shortfall honesty — zero fund must show the full gap
y, u, c, t, inc, tax, net, sf = project(initial_fund=0)
i70 = list(y).index(70)
record("A6 shortfall-honesty", "zero fund, £20k target",
       "PASS" if abs(sf[i70] - 20000) < 1 else "FAIL",
       "" if abs(sf[i70] - 20000) < 1 else f"shortfall £{sf[i70]:,.0f}")

# A7: real-terms consistency — state pension constant in today's money
y, u, c, t, inc, tax, net, sf = project(include_state_pension=True, initial_fund=0,
    annual_retirement_income=0, target_income=0, income_start_age=67, max_age=92)
i67, i77 = list(y).index(67), list(y).index(77)
ratio = inc[i77] / inc[i67] if inc[i67] else 0
record("A7 real-vs-nominal", "state pension held in today's money",
       "PASS" if abs(ratio - 1.0) < 0.001 else "FAIL",
       f"age-67 £{inc[i67]:,.0f}/yr vs age-77 £{inc[i77]:,.0f}/yr")

print("\n" + "=" * 70)
counts = {}
for _, _, o, _ in results:
    counts[o] = counts.get(o, 0) + 1
print("SUMMARY:", counts)
sys.exit(1 if counts.get("FAIL") or counts.get("CRASH") else 0)
