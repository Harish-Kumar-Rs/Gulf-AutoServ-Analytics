"""
gen_actuals_data.py
Generates actuals_data.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- Actuals are never exactly on budget (noise ±5-15%)
- Labour cost overruns are common (overtime, agency staff)
- Revenue misses in summer months (Jul-Aug slowdown in UAE)
- Parts costs spike unpredictably (supply chain, import delays)
- Marketing underspend is common (campaigns get delayed or cancelled)
- Sharjah branch underperforms vs budget more often (smaller market)
"""

import pandas as pd
import numpy as np

np.random.seed(99)

# Load budget as the base — actuals are derived from it with variance
budget = pd.read_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/budget_data.csv")

# Variance profiles per category (mean, std) — positive = overspend/over-revenue
variance_profile = {
    "Revenue":           {"mean": -0.03, "std": 0.07},   # usually slightly misses budget
    "Labour Cost":       {"mean":  0.06, "std": 0.05},   # consistently overspends
    "Parts & Materials": {"mean":  0.04, "std": 0.08},   # volatile
    "Overhead":          {"mean":  0.01, "std": 0.02},   # very stable
    "Marketing":         {"mean": -0.08, "std": 0.06},   # consistently underspends
}

# Summer revenue penalty (Jul=6, Aug=7 index months)
SUMMER_MONTHS = ["2024-07", "2024-08"]

records = []

for _, row in budget.iterrows():
    cat    = row["category"]
    branch = row["branch"]
    month  = row["month"]
    budget_amt = row["budget_amount_aed"]

    profile = variance_profile[cat]
    variance_pct = np.random.normal(profile["mean"], profile["std"])

    # Extra revenue penalty in summer
    if cat == "Revenue" and month in SUMMER_MONTHS:
        variance_pct -= np.random.uniform(0.04, 0.09)

    # Sharjah underperforms revenue more
    if cat == "Revenue" and branch == "Sharjah-Industrial":
        variance_pct -= np.random.uniform(0.02, 0.05)

    actual_amt = round(budget_amt * (1 + variance_pct), 2)
    variance_amt = round(actual_amt - budget_amt, 2)
    variance_pct_final = round((variance_amt / budget_amt) * 100, 2)

    records.append({
        "month":              month,
        "branch":             branch,
        "category":           cat,
        "budget_amount_aed":  budget_amt,
        "actual_amount_aed":  actual_amt,
        "variance_aed":       variance_amt,
        "variance_pct":       variance_pct_final,
        "currency":           "AED",
        "fiscal_year":        row["fiscal_year"],
        "quarter":            row["quarter"],
    })

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/actuals_data.csv", index=False)
print(f"actuals_data.csv  →  {len(df)} rows")
print(df[["month","branch","category","budget_amount_aed","actual_amount_aed","variance_pct"]].head(10).to_string(index=False))
