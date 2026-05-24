"""
gen_partner_payments.py
Generates partner_payments.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- Mix of suppliers (parts, lubricants, tyres) and fleet clients (corporates paying for vehicle servicing)
- Payment terms: Net-30 is standard; some suppliers offer Net-15 for early pay discount
- Late payments are realistic: ~12% of invoices paid late (cash flow issues)
- Partial payments exist (~5%): client pays installment, balance later
- Corporate fleet clients pay monthly consolidated invoices (not per transaction)
- Suppliers invoice twice a month typically
- Some invoices have early payment discounts applied (2/10 net 30 terms)
"""

import pandas as pd
import numpy as np
from faker import Faker

fake = Faker("en_US")
np.random.seed(21)

PARTNERS = {
    # Parts & lubricants suppliers (we pay them)
    "Al Futtaim Auto Parts":     {"type": "Supplier", "direction": "Outflow", "avg_invoice": 18000, "freq": 2},
    "Gulf Oil Distributors":     {"type": "Supplier", "direction": "Outflow", "avg_invoice": 9000,  "freq": 2},
    "Bridgestone UAE":           {"type": "Supplier", "direction": "Outflow", "avg_invoice": 22000, "freq": 1},
    "3M Gulf (Detailing)":       {"type": "Supplier", "direction": "Outflow", "avg_invoice": 4500,  "freq": 1},
    "Bosch Service Parts":       {"type": "Supplier", "direction": "Outflow", "avg_invoice": 12000, "freq": 2},
    # Fleet corporate clients (they pay us)
    "Emirates Transport Fleet":  {"type": "Fleet Client", "direction": "Inflow", "avg_invoice": 35000, "freq": 1},
    "ENOC Fleet Services":       {"type": "Fleet Client", "direction": "Inflow", "avg_invoice": 28000, "freq": 1},
    "Dubai Taxi Corporation":    {"type": "Fleet Client", "direction": "Inflow", "avg_invoice": 42000, "freq": 1},
    "Aramex UAE":                {"type": "Fleet Client", "direction": "Inflow", "avg_invoice": 19000, "freq": 1},
    "Careem Operations":         {"type": "Fleet Client", "direction": "Inflow", "avg_invoice": 15000, "freq": 1},
}

PAYMENT_TERMS = {
    "Supplier":     30,
    "Fleet Client": 30,
}

records = []
inv_counter = 5000

start = pd.Timestamp("2024-01-01")
end   = pd.Timestamp("2024-12-31")

for partner, meta in PARTNERS.items():
    # Generate invoice dates based on frequency per month
    for month_start in pd.date_range(start, end, freq="MS"):
        for issue_num in range(meta["freq"]):
            # Spread invoices across the month
            day_offset = issue_num * (28 // meta["freq"]) + np.random.randint(1, 5)
            issue_date = month_start + pd.Timedelta(days=int(day_offset))
            if issue_date > end:
                continue

            terms_days = PAYMENT_TERMS[meta["type"]]
            due_date   = issue_date + pd.Timedelta(days=terms_days)

            # Invoice amount with ±20% noise
            amount = round(meta["avg_invoice"] * np.random.uniform(0.80, 1.20), 2)
            vat    = round(amount * 0.05, 2)
            total  = round(amount + vat, 2)

            # Payment status
            rand = np.random.random()
            if rand < 0.05:
                # Partial payment
                paid_amount = round(total * np.random.uniform(0.40, 0.70), 2)
                status      = "Partial"
                paid_date   = due_date + pd.Timedelta(days=int(np.random.randint(0, 15)))
            elif rand < 0.17:
                # Late payment
                paid_amount = total
                status      = "Late"
                paid_date   = due_date + pd.Timedelta(days=int(np.random.randint(5, 45)))
            elif rand < 0.22:
                # Early payment with 2% discount
                discount    = round(total * 0.02, 2)
                paid_amount = round(total - discount, 2)
                status      = "Early-Paid"
                paid_date   = issue_date + pd.Timedelta(days=int(np.random.randint(5, 12)))
            else:
                paid_amount = total
                status      = "Paid"
                paid_date   = due_date + pd.Timedelta(days=int(np.random.randint(-3, 3)))

            if paid_date > end:
                paid_date = None
                status    = "Outstanding"
                paid_amount = 0.0

            records.append({
                "invoice_id":       f"INV-{inv_counter:05d}",
                "partner_name":     partner,
                "partner_type":     meta["type"],
                "direction":        meta["direction"],
                "issue_date":       issue_date.strftime("%Y-%m-%d"),
                "due_date":         due_date.strftime("%Y-%m-%d"),
                "paid_date":        paid_date.strftime("%Y-%m-%d") if paid_date else None,
                "subtotal_aed":     amount,
                "vat_aed":          vat,
                "total_aed":        total,
                "paid_amount_aed":  paid_amount,
                "outstanding_aed":  round(total - paid_amount, 2),
                "payment_status":   status,
                "payment_terms":    f"Net-{terms_days}",
                "month":            issue_date.strftime("%Y-%m"),
                "quarter":          f"Q{(issue_date.month - 1)//3 + 1}",
            })
            inv_counter += 1

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/partner_payments.csv", index=False)
print(f"partner_payments.csv  →  {len(df)} rows")
print(df[["invoice_id","partner_name","direction","total_aed","payment_status","paid_date"]].head(10).to_string(index=False))
