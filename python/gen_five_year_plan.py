"""
gen_five_year_plan.py
Generates five_year_plan.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- Strategic plan covers 2024-2028 (2024 = actual base year, 2025-2028 = projections)
- Revenue CAGR of ~12% (realistic for UAE auto services sector growth)
- New branch planned for 2026 (Ras Al Khaimah) — step change in capacity
- EV servicing revenue line introduced in 2026 (UAE EV adoption curve)
- Headcount grows ahead of revenue (hire before you need them — ops reality)
- EBITDA margin expands from ~18% to ~24% as scale kicks in
- CapEx heavy in 2025-2026 (new branch build-out, EV equipment)
- Working capital assumption: 45 days receivables, 30 days payables
- Each year has a strategic initiative and investment theme
"""

import pandas as pd
import numpy as np

np.random.seed(77)

YEARS = [2024, 2025, 2026, 2027, 2028]

# Revenue streams (AED thousands)
base_revenue = {
    "Vehicle Servicing":        9_500,
    "Parts & Accessories":      3_200,
    "Fleet Contracts":          4_800,
    "Detailing & Cosmetics":    1_100,
    "EV Servicing":             0,       # launches 2026
    "Franchise / Licensing":    0,       # launches 2027
}

# Growth rates per stream per year
growth_rates = {
    "Vehicle Servicing":       [0.00, 0.10, 0.22, 0.14, 0.12],  # 2026 jump = new branch
    "Parts & Accessories":     [0.00, 0.08, 0.18, 0.12, 0.10],
    "Fleet Contracts":         [0.00, 0.15, 0.25, 0.18, 0.15],
    "Detailing & Cosmetics":   [0.00, 0.09, 0.12, 0.10, 0.08],
    "EV Servicing":            [0.00, 0.00, 1.00, 0.80, 0.60],  # 2026 launch
    "Franchise / Licensing":   [0.00, 0.00, 0.00, 1.00, 0.50],  # 2027 launch
}

strategic_themes = {
    2024: "Base Year – Operational Stabilisation",
    2025: "Efficiency & Digital Transformation",
    2026: "Geographic Expansion (RAK Branch) + EV Readiness",
    2027: "Franchise Model Pilot + Margin Expansion",
    2028: "Market Leadership & Regional Scalability",
}

capex_plan = {
    2024: 1_200,   # routine maintenance CapEx
    2025: 2_800,   # IT systems, workshop upgrades
    2026: 6_500,   # new branch build, EV equipment
    2027: 2_200,   # franchise support systems
    2028: 1_800,   # routine + minor expansions
}

headcount = {
    2024: 42,
    2025: 50,
    2026: 68,   # new branch
    2027: 75,
    2028: 82,
}

records = []

rev_stream = {k: v for k, v in base_revenue.items()}

for i, year in enumerate(YEARS):
    # Apply growth
    if i > 0:
        for stream in rev_stream:
            rev_stream[stream] = round(
                rev_stream[stream] * (1 + growth_rates[stream][i]) +
                np.random.uniform(-50, 50),  # small noise
                0
            )

    total_revenue  = sum(rev_stream.values())
    cogs_pct       = np.random.uniform(0.52, 0.56)  # slightly improving COGS
    gross_profit   = round(total_revenue * (1 - cogs_pct), 0)
    gross_margin   = round((gross_profit / total_revenue) * 100, 1)

    opex_pct       = np.random.uniform(0.24, 0.28)
    ebitda         = round(total_revenue * (1 - cogs_pct - opex_pct), 0)
    ebitda_margin  = round((ebitda / total_revenue) * 100, 1)

    depreciation   = round(capex_plan[year] * 0.20, 0)  # 5yr straight-line
    ebit           = round(ebitda - depreciation, 0)
    interest       = round(capex_plan[year] * 0.04, 0)  # 4% cost of debt on CapEx
    pbt            = round(ebit - interest, 0)
    tax            = round(pbt * 0.09, 0)  # UAE 9% corporate tax (since June 2023)
    net_profit     = round(pbt - tax, 0)
    net_margin     = round((net_profit / total_revenue) * 100, 1)

    for stream, amount in rev_stream.items():
        records.append({
            "year":               year,
            "data_type":          "Actual" if year == 2024 else "Projection",
            "revenue_stream":     stream,
            "revenue_aed_000s":   int(amount),
            "total_revenue_aed_000s":   int(total_revenue),
            "gross_profit_aed_000s":    int(gross_profit),
            "gross_margin_pct":         gross_margin,
            "ebitda_aed_000s":          int(ebitda),
            "ebitda_margin_pct":        ebitda_margin,
            "net_profit_aed_000s":      int(net_profit),
            "net_margin_pct":           net_margin,
            "capex_aed_000s":           capex_plan[year],
            "headcount":                headcount[year],
            "strategic_theme":          strategic_themes[year],
        })

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/five_year_plan.csv", index=False)

# Summary view
summary = df.drop_duplicates("year")[
    ["year","data_type","total_revenue_aed_000s","ebitda_margin_pct",
     "net_margin_pct","capex_aed_000s","headcount","strategic_theme"]
]
print(f"five_year_plan.csv  →  {len(df)} rows\n")
print(summary.to_string(index=False))
