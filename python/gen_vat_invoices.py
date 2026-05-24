"""
gen_vat_invoices.py
Generates vat_invoices.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- UAE VAT is 5% flat on all taxable supplies
- Invoices must have a valid TRN (Tax Registration Number) — 15 digits
- ~4% of invoices have a VAT calculation error (rounding mistake or wrong rate)
- ~3% have a missing or malformed TRN (common with smaller suppliers)
- ~2% are exempt supplies (international transport, certain medical) — VAT = 0
- ~1.5% have mismatched totals (subtotal + VAT ≠ total — data entry error)
- Invoice numbering follows a sequential format per branch
- B2B invoices are larger; B2C invoices are smaller
"""

import pandas as pd
import numpy as np

np.random.seed(33)

BRANCHES = ["Dubai-Al Quoz", "Abu Dhabi-Mussafah", "Sharjah-Industrial"]

# Gulf AutoServ TRNs per branch (15 digits, UAE format)
COMPANY_TRN = {
    "Dubai-Al Quoz":        "100234567890123",
    "Abu Dhabi-Mussafah":   "100234567890456",
    "Sharjah-Industrial":   "100234567890789",
}

CUSTOMER_TYPES = ["B2B", "B2C"]

SERVICE_CATEGORIES = {
    "Vehicle Service":      {"avg": 450,  "taxable": True},
    "Parts Supply":         {"avg": 800,  "taxable": True},
    "Fleet Contract":       {"avg": 8500, "taxable": True},
    "International Transport": {"avg": 1200, "taxable": False},  # zero-rated
    "Detailing Package":    {"avg": 350,  "taxable": True},
}

CAT_NAMES  = list(SERVICE_CATEGORIES.keys())
CAT_PROPS  = list(SERVICE_CATEGORIES.values())

records = []
inv_counters = {b: 1 for b in BRANCHES}

dates = pd.date_range("2024-01-01", "2024-12-31", freq="B")  # business days

for branch in BRANCHES:
    # ~6-8 invoices per business day
    for date in dates:
        month = date.month
        n_inv = np.random.randint(5, 10)

        # Summer slowdown
        if month in [7, 8]:
            n_inv = max(3, n_inv - 2)

        for _ in range(n_inv):
            cat_idx  = np.random.choice(len(CAT_NAMES), p=[0.40, 0.25, 0.15, 0.05, 0.15])
            cat_name = CAT_NAMES[cat_idx]
            cat_prop = CAT_PROPS[cat_idx]

            cust_type = "B2B" if cat_name in ["Fleet Contract", "Parts Supply", "International Transport"] else np.random.choice(CUSTOMER_TYPES, p=[0.35, 0.65])

            subtotal = round(cat_prop["avg"] * np.random.uniform(0.70, 1.40), 2)

            # Taxable or zero-rated
            is_taxable = cat_prop["taxable"]
            correct_vat = round(subtotal * 0.05, 2) if is_taxable else 0.0

            # Inject errors
            rand = np.random.random()
            error_type = None

            if rand < 0.04:
                # VAT calculation error (wrong rate or rounding)
                wrong_rate = np.random.choice([0.04, 0.055, 0.10, 0.0])
                vat_charged = round(subtotal * wrong_rate, 2)
                error_type  = "VAT_RATE_ERROR"
            elif rand < 0.07:
                # Missing TRN
                customer_trn = ""
                vat_charged  = correct_vat
                error_type   = "MISSING_TRN"
            elif rand < 0.09:
                # Exempt supply but VAT still charged
                vat_charged = round(subtotal * 0.05, 2) if not is_taxable else correct_vat
                error_type  = "EXEMPT_VAT_CHARGED" if not is_taxable else None
            elif rand < 0.105:
                # Mismatched total
                vat_charged = correct_vat
                error_type  = "TOTAL_MISMATCH"
            else:
                vat_charged = correct_vat

            total = round(subtotal + vat_charged, 2)

            # Introduce total mismatch
            if error_type == "TOTAL_MISMATCH":
                total = round(total + np.random.uniform(1, 20), 2)

            # TRN generation
            if error_type == "MISSING_TRN":
                customer_trn = ""
            elif cust_type == "B2B":
                # Valid 15-digit TRN for corporate customer
                customer_trn = str(np.random.randint(10**14, 10**15 - 1))
            else:
                customer_trn = ""  # B2C doesn't need TRN

            inv_num = f"GINV-{branch[:3].upper()}-{date.year}-{inv_counters[branch]:05d}"
            inv_counters[branch] += 1

            records.append({
                "invoice_number":    inv_num,
                "invoice_date":      date.strftime("%Y-%m-%d"),
                "branch":            branch,
                "branch_trn":        COMPANY_TRN[branch],
                "customer_type":     cust_type,
                "customer_trn":      customer_trn,
                "service_category":  cat_name,
                "subtotal_aed":      subtotal,
                "vat_charged_aed":   vat_charged,
                "total_aed":         total,
                "correct_vat_aed":   correct_vat,
                "is_taxable":        is_taxable,
                "error_flag":        error_type,
                "month":             date.strftime("%Y-%m"),
                "quarter":           f"Q{(date.month-1)//3+1}",
            })

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/vat_invoices.csv", index=False)
error_summary = df[df["error_flag"].notna()]["error_flag"].value_counts()
print(f"vat_invoices.csv  →  {len(df):,} rows")
print(f"\nError distribution:\n{error_summary.to_string()}")
print(f"\nSample flagged invoices:")
print(df[df["error_flag"].notna()][["invoice_number","subtotal_aed","vat_charged_aed","correct_vat_aed","error_flag"]].head(8).to_string(index=False))
