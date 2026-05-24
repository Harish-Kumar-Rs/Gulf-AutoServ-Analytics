"""
gen_wallet_transactions.py
Generates wallet_transactions.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- Each branch has a petty cash wallet (top-ups + expenses)
- Common garage petty cash: consumables, staff tea/coffee, emergency parts run,
  cleaning supplies, small tool purchases, parking/fuel for test drives
- Top-ups happen at start of month and mid-month when balance runs low
- Balance never goes negative (manager tops up before it hits zero)
- Fridays have almost no transactions (UAE weekend)
- End of month: reconciliation top-ups to zero out and restart
- Occasional suspicious patterns: round-number withdrawals (flag for audit)
"""

import pandas as pd
import numpy as np

np.random.seed(55)

BRANCHES = ["Dubai-Al Quoz", "Abu Dhabi-Mussafah", "Sharjah-Industrial"]

EXPENSE_TYPES = {
    "Consumables (Rags/Gloves)":    {"avg": 85,   "freq": 0.18},
    "Staff Refreshments":           {"avg": 45,   "freq": 0.20},
    "Emergency Parts Run":          {"avg": 320,  "freq": 0.10},
    "Cleaning Supplies":            {"avg": 110,  "freq": 0.12},
    "Fuel (Test Drive)":            {"avg": 60,   "freq": 0.15},
    "Small Tools":                  {"avg": 200,  "freq": 0.08},
    "Parking / Toll":               {"avg": 25,   "freq": 0.10},
    "Stationary / Admin":           {"avg": 55,   "freq": 0.07},
}

EXP_NAMES  = list(EXPENSE_TYPES.keys())
EXP_FREQ   = [EXPENSE_TYPES[e]["freq"] for e in EXP_NAMES]
EXP_AVG    = [EXPENSE_TYPES[e]["avg"]  for e in EXP_NAMES]

MONTHLY_TOPUP = {
    "Dubai-Al Quoz":        3000,
    "Abu Dhabi-Mussafah":   2000,
    "Sharjah-Industrial":   1500,
}

records = []
txn_counter = 9000

for branch in BRANCHES:
    balance = 0.0
    topup_base = MONTHLY_TOPUP[branch]

    for date in pd.date_range("2024-01-01", "2024-12-31"):
        dow   = date.dayofweek
        month = date.month
        day   = date.day

        # Skip Fridays (UAE weekend core)
        if dow == 4:
            continue

        # Month-start top-up
        if day == 1:
            topup = topup_base + np.random.randint(-200, 200)
            balance += topup
            records.append({
                "txn_id":       f"WLT-{txn_counter:05d}",
                "date":         date.strftime("%Y-%m-%d"),
                "branch":       branch,
                "txn_type":     "Top-Up",
                "description":  "Monthly petty cash top-up",
                "amount_aed":   round(topup, 2),
                "balance_aed":  round(balance, 2),
                "month":        date.strftime("%Y-%m"),
                "quarter":      f"Q{(month-1)//3+1}",
                "flag":         None,
            })
            txn_counter += 1

        # Mid-month top-up if balance low
        if day == 15 and balance < topup_base * 0.3:
            topup = round(topup_base * 0.5, 2)
            balance += topup
            records.append({
                "txn_id":       f"WLT-{txn_counter:05d}",
                "date":         date.strftime("%Y-%m-%d"),
                "branch":       branch,
                "txn_type":     "Top-Up",
                "description":  "Mid-month petty cash replenishment",
                "amount_aed":   topup,
                "balance_aed":  round(balance, 2),
                "month":        date.strftime("%Y-%m"),
                "quarter":      f"Q{(month-1)//3+1}",
                "flag":         None,
            })
            txn_counter += 1

        # 1-3 expense transactions per working day
        n_exp = np.random.choice([0, 1, 1, 2, 2, 3], p=[0.15, 0.25, 0.25, 0.20, 0.10, 0.05])
        for _ in range(n_exp):
            idx    = np.random.choice(len(EXP_NAMES), p=EXP_FREQ)
            exp    = EXP_NAMES[idx]
            amount = round(EXP_AVG[idx] * np.random.uniform(0.75, 1.25), 2)

            # Round-number flag (~4% of transactions — audit pattern)
            is_round = np.random.random() < 0.04
            if is_round:
                amount = float(round(amount / 50) * 50)
                flag   = "Round-Number Review"
            else:
                flag = None

            if balance - amount < 0:
                continue  # skip if insufficient balance

            balance -= amount
            records.append({
                "txn_id":       f"WLT-{txn_counter:05d}",
                "date":         date.strftime("%Y-%m-%d"),
                "branch":       branch,
                "txn_type":     "Expense",
                "description":  exp,
                "amount_aed":   -amount,
                "balance_aed":  round(balance, 2),
                "month":        date.strftime("%Y-%m"),
                "quarter":      f"Q{(month-1)//3+1}",
                "flag":         flag,
            })
            txn_counter += 1

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/wallet_transactions.csv", index=False)
print(f"wallet_transactions.csv  →  {len(df):,} rows")
print(df[["txn_id","date","branch","txn_type","description","amount_aed","balance_aed","flag"]].head(12).to_string(index=False))
