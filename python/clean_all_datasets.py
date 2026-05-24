"""
clean_all_datasets.py
Gulf AutoServ Analytics — Data Cleaning Pipeline

Run this once. Reads from datasets/raw/, writes to datasets/cleaned/.
Each section is clearly labelled. Read the comments — they explain
the business logic behind every cleaning decision.
"""

import pandas as pd
import numpy as np
import os

RAW   = "datasets/raw"
CLEAN = "datasets/cleaned"
os.makedirs(CLEAN, exist_ok=True)

print("=" * 60)
print("GULF AUTOSERV ANALYTICS — DATA CLEANING PIPELINE")
print("=" * 60)


# ─────────────────────────────────────────────────────────────
# 1. BUDGET DATA
# ─────────────────────────────────────────────────────────────
print("\n[1/8] budget_data.csv")

df = pd.read_csv(f"{RAW}/budget_data.csv")

# No single PK — composite key is month + branch + category
# Validate: no duplicates on composite key
dupes = df.duplicated(subset=["month", "branch", "category"]).sum()
print(f"  Duplicate composite keys : {dupes}")

# Validate: no nulls in key columns
nulls = df[["month", "branch", "category", "budget_amount_aed"]].isnull().sum().sum()
print(f"  Null values in key cols  : {nulls}")

# Validate: budget amounts are positive
neg = (df["budget_amount_aed"] <= 0).sum()
print(f"  Non-positive amounts     : {neg}")

# Standardise branch names (strip whitespace)
df["branch"] = df["branch"].str.strip()

# Add composite key column for reference
df.insert(0, "composite_key", df["month"] + "|" + df["branch"] + "|" + df["category"])

df.to_csv(f"{CLEAN}/budget_data.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 2. ACTUALS DATA
# ─────────────────────────────────────────────────────────────
print("\n[2/8] actuals_data.csv")

df = pd.read_csv(f"{RAW}/actuals_data.csv")

# Composite key: month + branch + category
dupes = df.duplicated(subset=["month", "branch", "category"]).sum()
print(f"  Duplicate composite keys : {dupes}")

nulls = df[["month","branch","category","actual_amount_aed"]].isnull().sum().sum()
print(f"  Null values              : {nulls}")

# Recalculate variance to catch any drift
df["variance_aed_check"]  = (df["actual_amount_aed"] - df["budget_amount_aed"]).round(2)
df["variance_pct_check"]  = ((df["variance_aed_check"] / df["budget_amount_aed"]) * 100).round(2)

# Flag rows where stored variance doesn't match recalculated
df["variance_mismatch"] = (df["variance_aed"] - df["variance_aed_check"]).abs() > 0.05

mismatches = df["variance_mismatch"].sum()
print(f"  Variance recalc mismatches: {mismatches}")

# Use recalculated values as the clean version
df["variance_aed"] = df["variance_aed_check"]
df["variance_pct"] = df["variance_pct_check"]
df.drop(columns=["variance_aed_check","variance_pct_check","variance_mismatch"], inplace=True)

# Add overspend/underspend flag (business logic)
# For cost categories: positive variance = overspend (bad)
# For revenue: positive variance = over-revenue (good)
COST_CATS = ["Labour Cost", "Parts & Materials", "Overhead", "Marketing"]

def spend_flag(row):
    if row["category"] == "Revenue":
        return "Over-Revenue" if row["variance_aed"] > 0 else "Under-Revenue"
    else:
        return "Overspend" if row["variance_aed"] > 0 else "Underspend"

df["spend_flag"] = df.apply(spend_flag, axis=1)

df.insert(0, "composite_key", df["month"] + "|" + df["branch"] + "|" + df["category"])

df.to_csv(f"{CLEAN}/actuals_data.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 3. WALLET TRANSACTIONS
# ─────────────────────────────────────────────────────────────
print("\n[3/8] wallet_transactions.csv")

df = pd.read_csv(f"{RAW}/wallet_transactions.csv")

# PK: txn_id — must be unique and not null
pk_nulls  = df["txn_id"].isnull().sum()
pk_dupes  = df.duplicated(subset=["txn_id"]).sum()
print(f"  PK nulls   : {pk_nulls}")
print(f"  PK dupes   : {pk_dupes}")

# Date formatting
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

# Separate top-ups and expenses cleanly
# Expenses are stored as negative — add an absolute amount column
df["amount_abs_aed"] = df["amount_aed"].abs()

# Validate running balance: balance should never go negative
neg_balance = (df["balance_aed"] < 0).sum()
print(f"  Negative balances        : {neg_balance}")

# Standardise flag column — NaN → 'None'
df["flag"] = df["flag"].fillna("None")

# Count round-number flags
round_flags = (df["flag"] == "Round-Number Review").sum()
print(f"  Round-number flags       : {round_flags}")

df.to_csv(f"{CLEAN}/wallet_transactions.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 4. VAT INVOICES  ← most cleaning work here
# ─────────────────────────────────────────────────────────────
print("\n[4/8] vat_invoices.csv")

df = pd.read_csv(f"{RAW}/vat_invoices.csv")

# PK: invoice_number — unique, not null
pk_nulls = df["invoice_number"].isnull().sum()
pk_dupes = df.duplicated(subset=["invoice_number"]).sum()
print(f"  PK nulls   : {pk_nulls}")
print(f"  PK dupes   : {pk_dupes}")

# --- Cleaning step 1: Standardise TRN format ---
# TRN must be 15 digits. Flag malformed ones.
df["branch_trn"]   = df["branch_trn"].astype(str).str.strip()
df["customer_trn"] = df["customer_trn"].astype(str).str.strip()

# B2B invoices must have a customer TRN — flag if missing
df["b2b_missing_trn"] = (
    (df["customer_type"] == "B2B") &
    (df["customer_trn"].isin(["", "nan", "None"]))
)

# TRN length validation (15 digits)
def trn_valid(trn):
    trn = str(trn).strip()
    return trn.isdigit() and len(trn) == 15

df["branch_trn_valid"]   = df["branch_trn"].apply(trn_valid)
df["customer_trn_valid"] = df["customer_trn"].apply(
    lambda x: True if x in ["", "nan", "None"] else trn_valid(x)
)

# --- Cleaning step 2: Recalculate correct VAT ---
UAE_VAT_RATE = 0.05
df["recalc_vat_aed"] = df.apply(
    lambda r: round(r["subtotal_aed"] * UAE_VAT_RATE, 2) if r["is_taxable"] else 0.0,
    axis=1
)

# --- Cleaning step 3: VAT rate error flag ---
# Flag where charged VAT differs from correct VAT by more than AED 1 tolerance
df["vat_error_flag"] = (df["vat_charged_aed"] - df["recalc_vat_aed"]).abs() > 1.00

# --- Cleaning step 4: Total mismatch flag ---
# Correct total should be subtotal + correct VAT
df["correct_total_aed"] = (df["subtotal_aed"] + df["recalc_vat_aed"]).round(2)
df["total_mismatch_flag"] = (df["total_aed"] - df["correct_total_aed"]).abs() > 0.50

# --- Cleaning step 5: Exempt supply but VAT charged ---
df["exempt_vat_flag"] = (
    (~df["is_taxable"]) &
    (df["vat_charged_aed"] > 0)
)

# --- Cleaning step 6: Consolidated error flag ---
def consolidated_flag(row):
    flags = []
    if row["vat_error_flag"]:
        flags.append("VAT_RATE_ERROR")
    if row["b2b_missing_trn"]:
        flags.append("MISSING_TRN")
    if row["total_mismatch_flag"]:
        flags.append("TOTAL_MISMATCH")
    if row["exempt_vat_flag"]:
        flags.append("EXEMPT_VAT_CHARGED")
    return "|".join(flags) if flags else "CLEAN"

df["clean_error_flag"] = df.apply(consolidated_flag, axis=1)

# Summary
flag_summary = df["clean_error_flag"].value_counts()
print(f"\n  Error flag distribution:")
for flag, count in flag_summary.items():
    print(f"    {flag:<30} : {count}")

# Drop the raw error_flag column (replaced by clean_error_flag)
df.drop(columns=["error_flag", "correct_vat_aed"], inplace=True)
# correct_vat_aed is now recalc_vat_aed (more explicit name)

df.to_csv(f"{CLEAN}/vat_invoices.csv", index=False)
print(f"\n  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 5. POS SALES
# ─────────────────────────────────────────────────────────────
print("\n[5/8] pos_sales.csv")

df = pd.read_csv(f"{RAW}/pos_sales.csv")

# PK: transaction_id
pk_nulls = df["transaction_id"].isnull().sum()
pk_dupes = df.duplicated(subset=["transaction_id"]).sum()
print(f"  PK nulls   : {pk_nulls}")
print(f"  PK dupes   : {pk_dupes}")

# Validate: parts + labour should equal total (for completed transactions)
completed = df[df["status"] == "Completed"].copy()
completed["calc_total"] = (completed["parts_cost_aed"] + completed["labour_cost_aed"]).round(2)
total_mismatch = (
    (completed["calc_total"] - completed["total_amount_aed"]).abs() > 0.50
).sum()
print(f"  Parts+Labour≠Total (completed): {total_mismatch}")

# Void transactions should have zero amounts — validate
voids = df[df["status"] == "Void"]
void_nonzero = (voids["total_amount_aed"] != 0).sum()
print(f"  Voids with non-zero amount     : {void_nonzero}")

# Separate voids flag for reporting
df["is_void"] = df["status"] == "Void"

# Date as proper datetime
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

# Add revenue-only column (exclude voids) for analysis
df["revenue_aed"] = df.apply(
    lambda r: r["total_amount_aed"] if r["status"] == "Completed" else 0.0, axis=1
)

void_count = df["is_void"].sum()
print(f"  Void transactions            : {void_count} ({void_count/len(df)*100:.1f}%)")

df.to_csv(f"{CLEAN}/pos_sales.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 6. PARTNER PAYMENTS
# ─────────────────────────────────────────────────────────────
print("\n[6/8] partner_payments.csv")

df = pd.read_csv(f"{RAW}/partner_payments.csv")

# PK: invoice_id
pk_nulls = df["invoice_id"].isnull().sum()
pk_dupes = df.duplicated(subset=["invoice_id"]).sum()
print(f"  PK nulls   : {pk_nulls}")
print(f"  PK dupes   : {pk_dupes}")

# Date validation: paid_date must not be before issue_date
df["issue_date"] = pd.to_datetime(df["issue_date"])
df["due_date"]   = pd.to_datetime(df["due_date"])
df["paid_date"]  = pd.to_datetime(df["paid_date"], errors="coerce")

# Flag where paid_date < issue_date (data error)
invalid_dates = (df["paid_date"] < df["issue_date"]).sum()
print(f"  Paid before issued (error)   : {invalid_dates}")

# Flag late payments (paid after due_date)
df["days_overdue"] = (df["paid_date"] - df["due_date"]).dt.days
df["days_overdue"] = df["days_overdue"].apply(lambda x: max(0, x) if pd.notna(x) else None)

# Validate: subtotal + vat = total
df["calc_total"] = (df["subtotal_aed"] + df["vat_aed"]).round(2)
total_mismatch   = ((df["calc_total"] - df["total_aed"]).abs() > 0.05).sum()
print(f"  Subtotal+VAT≠Total           : {total_mismatch}")

# Payment status distribution
print(f"  Payment status breakdown:")
for status, count in df["payment_status"].value_counts().items():
    print(f"    {status:<15} : {count}")

# Reformat dates back to string
df["issue_date"] = df["issue_date"].dt.strftime("%Y-%m-%d")
df["due_date"]   = df["due_date"].dt.strftime("%Y-%m-%d")
df["paid_date"]  = df["paid_date"].dt.strftime("%Y-%m-%d").replace("NaT", "")

df.drop(columns=["calc_total"], inplace=True)

df.to_csv(f"{CLEAN}/partner_payments.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 7. KPI SCORECARD
# ─────────────────────────────────────────────────────────────
print("\n[7/8] kpi_scorecard.csv")

df = pd.read_csv(f"{RAW}/kpi_scorecard.csv")

# Composite key: month + branch
dupes = df.duplicated(subset=["month", "branch"]).sum()
nulls = df[["month", "branch"]].isnull().sum().sum()
print(f"  Composite key dupes : {dupes}")
print(f"  Key nulls           : {nulls}")

# Validate: completion rate should match jobs_completed / jobs_target
df["recalc_completion_pct"] = (
    (df["jobs_completed"] / df["jobs_target"]) * 100
).round(1)

completion_mismatch = (
    (df["completion_rate_pct"] - df["recalc_completion_pct"]).abs() > 0.5
).sum()
print(f"  Completion rate mismatches : {completion_mismatch}")
df["completion_rate_pct"] = df["recalc_completion_pct"]
df.drop(columns=["recalc_completion_pct"], inplace=True)

# Validate: utilization = billed_hours / available_hours
df["recalc_util_pct"] = (
    (df["billed_hours"] / df["available_hours"]) * 100
).round(1)
util_mismatch = (
    (df["utilization_pct"] - df["recalc_util_pct"]).abs() > 0.5
).sum()
print(f"  Utilization mismatches     : {util_mismatch}")
df["utilization_pct"] = df["recalc_util_pct"]
df.drop(columns=["recalc_util_pct"], inplace=True)

# Add performance band for CSAT (useful in Power BI)
def csat_band(score):
    if score >= 4.5:   return "Excellent"
    elif score >= 4.0: return "Good"
    elif score >= 3.5: return "Acceptable"
    else:              return "Poor"

df["csat_band"] = df["csat_score"].apply(csat_band)

# Add composite key
df.insert(0, "composite_key", df["month"] + "|" + df["branch"])

df.to_csv(f"{CLEAN}/kpi_scorecard.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# 8. FIVE YEAR PLAN
# ─────────────────────────────────────────────────────────────
print("\n[8/8] five_year_plan.csv")

df = pd.read_csv(f"{RAW}/five_year_plan.csv")

# Your audit note: rename Projection → Target
df["data_type"] = df["data_type"].replace("Projection", "Target")
print(f"  'Projection' renamed to 'Target'")

# Composite key: year + revenue_stream
dupes = df.duplicated(subset=["year", "revenue_stream"]).sum()
print(f"  Composite key dupes : {dupes}")

# Add statistical disclaimer column
df["statistical_note"] = df["data_type"].apply(
    lambda x: "Actual — base year" if x == "Actual"
    else "Target — single base year; treat as directional, not statistically validated"
)

# Validate: revenue_stream amounts should sum to total_revenue per year
rev_check = df.groupby("year")["revenue_aed_000s"].sum().reset_index()
rev_check.columns = ["year", "sum_streams"]
df = df.merge(rev_check, on="year", how="left")
df["revenue_sum_valid"] = (
    (df["sum_streams"] - df["total_revenue_aed_000s"]).abs() < 10
)
invalid_totals = (~df["revenue_sum_valid"]).sum()
print(f"  Revenue sum mismatches : {invalid_totals}")
df.drop(columns=["sum_streams", "revenue_sum_valid"], inplace=True)

df.to_csv(f"{CLEAN}/five_year_plan.csv", index=False)
print(f"  ✓ Cleaned → {len(df)} rows")


# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("CLEANING COMPLETE — files written to datasets/cleaned/")
print("=" * 60)

import glob
for f in sorted(glob.glob(f"{CLEAN}/*.csv")):
    rows = sum(1 for _ in open(f)) - 1
    print(f"  {os.path.basename(f):<35} {rows:>6} rows")
