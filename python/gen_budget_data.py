"""
gen_budget_data.py
Generates budget_data.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- Budgets are set once per year (annual planning cycle), split by month
- Q1 budgets are conservative; Q3/Q4 get revised upward (mid-year review)
- Labour and parts cost more in summer (AC, cooling system jobs spike in UAE)
- Each branch has a different revenue target reflecting size
- Overhead is relatively flat (rent, utilities don't change much month to month)
"""

import pandas as pd
import numpy as np

np.random.seed(42)

BRANCHES   = ["Dubai-Al Quoz", "Abu Dhabi-Mussafah", "Sharjah-Industrial"]
CATEGORIES = ["Revenue", "Labour Cost", "Parts & Materials", "Overhead", "Marketing"]
MONTHS     = pd.date_range("2024-01-01", periods=12, freq="MS")

# Branch size multipliers (Dubai largest, Sharjah smallest)
branch_scale = {
    "Dubai-Al Quoz":        1.00,
    "Abu Dhabi-Mussafah":   0.78,
    "Sharjah-Industrial":   0.55,
}

# Base annual budget per category (AED) for the Dubai branch
base_annual = {
    "Revenue":           4_800_000,
    "Labour Cost":       1_440_000,
    "Parts & Materials": 1_080_000,
    "Overhead":            600_000,
    "Marketing":           240_000,
}

# Monthly seasonality index (UAE: slow Jan, peak Mar-May, summer dip Jul-Aug, recovery Oct-Dec)
seasonality = {
    "Revenue":           [0.07, 0.08, 0.10, 0.10, 0.09, 0.08, 0.07, 0.07, 0.08, 0.09, 0.09, 0.08],
    "Labour Cost":       [0.07, 0.08, 0.09, 0.09, 0.09, 0.09, 0.10, 0.10, 0.08, 0.08, 0.07, 0.06],
    "Parts & Materials": [0.07, 0.08, 0.09, 0.09, 0.09, 0.09, 0.10, 0.10, 0.08, 0.08, 0.07, 0.06],
    "Overhead":          [1/12]*12,   # flat
    "Marketing":         [0.05, 0.06, 0.12, 0.10, 0.08, 0.07, 0.06, 0.06, 0.10, 0.12, 0.10, 0.08],
}

records = []

for branch in BRANCHES:
    scale = branch_scale[branch]
    for cat in CATEGORIES:
        annual = base_annual[cat] * scale
        for i, month in enumerate(MONTHS):
            # Q3/Q4 mid-year upward revision (+3% to +6%)
            revision = 1.0 if month.quarter <= 2 else np.random.uniform(1.03, 1.06)
            budget_amount = round(annual * seasonality[cat][i] * revision, 2)
            records.append({
                "month":           month.strftime("%Y-%m"),
                "branch":          branch,
                "category":        cat,
                "budget_amount_aed": budget_amount,
                "currency":        "AED",
                "fiscal_year":     2024,
                "quarter":         f"Q{month.quarter}",
            })

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/budget_data.csv", index=False)
print(f"budget_data.csv  →  {len(df)} rows")
print(df.head(10).to_string(index=False))
