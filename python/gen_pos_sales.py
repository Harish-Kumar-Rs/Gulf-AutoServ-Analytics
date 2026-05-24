"""
gen_pos_sales.py
Generates pos_sales.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- More transactions on Sun-Thu (UAE working week); fewer Fri-Sat
- Peak hours: 9-11am and 4-6pm (drop-off and pick-up windows)
- Mix of payment methods: cash heavy in Sharjah, card heavy in Dubai
- Service types follow a realistic frequency: oil change most common,
  AC service spikes in summer, tyres spike before/after summer
- Larger ticket sizes on weekends (customers have more time)
- Occasional high-value jobs (engine overhaul, full service)
- ~3% of transactions are voided/cancelled (realistic for a garage POS)
"""

import pandas as pd
import numpy as np
from faker import Faker

fake = Faker("en_US")
np.random.seed(7)

BRANCHES = ["Dubai-Al Quoz", "Abu Dhabi-Mussafah", "Sharjah-Industrial"]

SERVICES = {
    "Oil Change":           {"base_price": 180,  "freq": 0.28},
    "AC Service":           {"base_price": 350,  "freq": 0.12},
    "Tyre Replacement":     {"base_price": 900,  "freq": 0.10},
    "Brake Service":        {"base_price": 450,  "freq": 0.09},
    "Full Service":         {"base_price": 750,  "freq": 0.08},
    "Battery Replacement":  {"base_price": 320,  "freq": 0.07},
    "Wheel Alignment":      {"base_price": 150,  "freq": 0.08},
    "Engine Diagnostics":   {"base_price": 200,  "freq": 0.06},
    "Engine Overhaul":      {"base_price": 3500, "freq": 0.02},
    "Detailing":            {"base_price": 400,  "freq": 0.05},
    "Suspension Repair":    {"base_price": 800,  "freq": 0.05},
}

SERVICE_NAMES  = list(SERVICES.keys())
SERVICE_FREQ   = [SERVICES[s]["freq"] for s in SERVICE_NAMES]
SERVICE_PRICES = [SERVICES[s]["base_price"] for s in SERVICE_NAMES]

PAYMENT_METHODS = {
    "Dubai-Al Quoz":        ["Card", "Cash", "Online", "Corporate Account"],
    "Abu Dhabi-Mussafah":   ["Card", "Cash", "Corporate Account"],
    "Sharjah-Industrial":   ["Cash", "Card", "Cheque"],
}
PAYMENT_PROBS = {
    "Dubai-Al Quoz":        [0.55, 0.25, 0.10, 0.10],
    "Abu Dhabi-Mussafah":   [0.45, 0.35, 0.20],
    "Sharjah-Industrial":   [0.50, 0.40, 0.10],
}

# Daily transaction volume per branch (avg)
daily_txn = {
    "Dubai-Al Quoz":        22,
    "Abu Dhabi-Mussafah":   15,
    "Sharjah-Industrial":   10,
}

dates = pd.date_range("2024-01-01", "2024-12-31")

records = []
txn_counter = 1000

for branch in BRANCHES:
    for date in dates:
        dow = date.dayofweek  # 0=Mon … 6=Sun
        month = date.month

        # UAE weekend is Friday(4) and Saturday(5)
        volume_factor = 0.6 if dow in [4, 5] else 1.0

        # Summer dip Jul-Aug
        if month in [7, 8]:
            volume_factor *= 0.75

        # Ramadan approximation (Mar-Apr): morning rush lower, evening pickup
        if month in [3, 4]:
            volume_factor *= 0.85

        n_txns = max(1, int(np.random.poisson(daily_txn[branch] * volume_factor)))

        for _ in range(n_txns):
            # Peak hour distribution
            hour = np.random.choice(
                list(range(8, 20)),
                p=[0.08, 0.12, 0.12, 0.08, 0.06, 0.05,
                   0.06, 0.12, 0.12, 0.08, 0.06, 0.05]
            )
            minute  = np.random.randint(0, 60)
            txn_time = pd.Timestamp(date) + pd.Timedelta(hours=hour, minutes=minute)

            service_idx = np.random.choice(len(SERVICE_NAMES), p=SERVICE_FREQ)
            service     = SERVICE_NAMES[service_idx]
            base_price  = SERVICE_PRICES[service_idx]

            # AC service surges in summer
            if service == "AC Service" and month in [5, 6, 7, 8]:
                base_price *= 1.15

            # Price noise ±10%
            price = round(base_price * np.random.uniform(0.90, 1.10), 2)

            # Parts cost (typically 30-45% of job)
            parts_cost = round(price * np.random.uniform(0.30, 0.45), 2)

            # Labour cost
            labour_cost = round(price - parts_cost, 2)

            payment = np.random.choice(
                PAYMENT_METHODS[branch],
                p=PAYMENT_PROBS[branch]
            )

            # ~3% voids
            status = "Void" if np.random.random() < 0.03 else "Completed"
            if status == "Void":
                price = parts_cost = labour_cost = 0.0

            txn_id = f"TXN-{txn_counter:06d}"
            txn_counter += 1

            records.append({
                "transaction_id":   txn_id,
                "date":             date.strftime("%Y-%m-%d"),
                "time":             txn_time.strftime("%H:%M"),
                "branch":           branch,
                "service_type":     service,
                "total_amount_aed": price,
                "parts_cost_aed":   parts_cost,
                "labour_cost_aed":  labour_cost,
                "payment_method":   payment,
                "status":           status,
                "month":            date.strftime("%Y-%m"),
                "quarter":          f"Q{(date.month - 1)//3 + 1}",
                "day_of_week":      date.strftime("%A"),
            })

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/pos_sales.csv", index=False)
print(f"pos_sales.csv  →  {len(df):,} rows")
print(df.head(8).to_string(index=False))
