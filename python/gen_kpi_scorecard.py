"""
gen_kpi_scorecard.py
Generates kpi_scorecard.csv for Gulf AutoServ Analytics.

Real-world patterns baked in:
- KPIs tracked monthly per branch (standard management reporting cadence)
- Job completion rate dips in summer (staff absenteeism, heat, slower throughput)
- Customer satisfaction scores correlate with wait time (longer wait = lower score)
- Technician utilization varies by branch size and workload
- Revenue per job trends upward through the year (price adjustments, upsell)
- Return rate (repeat customers) is higher in Dubai (loyalty program)
- First-time fix rate (quality KPI) is lower in Sharjah (newer/less experienced team)
- Average job duration increases in summer (AC jobs are complex)
"""

import pandas as pd
import numpy as np

np.random.seed(13)

BRANCHES = ["Dubai-Al Quoz", "Abu Dhabi-Mussafah", "Sharjah-Industrial"]
MONTHS   = pd.date_range("2024-01-01", periods=12, freq="MS")

# Branch baseline KPIs
branch_baselines = {
    "Dubai-Al Quoz": {
        "jobs_target": 480, "tech_count": 12,
        "csat_base": 4.3, "ftfr_base": 0.88,
        "return_rate_base": 0.42, "rev_per_job_base": 380,
    },
    "Abu Dhabi-Mussafah": {
        "jobs_target": 340, "tech_count": 9,
        "csat_base": 4.1, "ftfr_base": 0.85,
        "return_rate_base": 0.36, "rev_per_job_base": 365,
    },
    "Sharjah-Industrial": {
        "jobs_target": 240, "tech_count": 7,
        "csat_base": 3.9, "ftfr_base": 0.80,
        "return_rate_base": 0.30, "rev_per_job_base": 340,
    },
}

# Monthly factors
summer_months = [7, 8]
ramadan_months = [3, 4]

records = []

for branch, bl in branch_baselines.items():
    for month in MONTHS:
        m = month.month

        # Seasonal adjustments
        is_summer  = m in summer_months
        is_ramadan = m in ramadan_months

        job_factor  = 0.78 if is_summer else (0.87 if is_ramadan else 1.0)
        util_factor = 0.82 if is_summer else (0.88 if is_ramadan else 1.0)
        csat_factor = -0.15 if is_summer else (-0.05 if is_ramadan else 0)

        jobs_completed = int(bl["jobs_target"] * job_factor * np.random.uniform(0.92, 1.05))
        jobs_target    = bl["jobs_target"]

        completion_rate = round(jobs_completed / jobs_target * 100, 1)

        # Technician utilization (available hours vs billed hours)
        available_hours = bl["tech_count"] * 8 * 26  # ~26 working days/month
        billed_hours    = round(available_hours * util_factor * np.random.uniform(0.88, 1.00), 0)
        utilization_pct = round(billed_hours / available_hours * 100, 1)

        # CSAT out of 5
        csat = round(
            min(5.0, max(1.0,
                bl["csat_base"] + csat_factor + np.random.normal(0, 0.12)
            )), 2
        )

        # Average wait time (minutes) — inversely correlated with CSAT
        avg_wait_min = round(35 + (5 - csat) * 12 + np.random.normal(0, 5), 0)

        # First time fix rate
        ftfr = round(
            min(1.0, max(0.5,
                bl["ftfr_base"] + (-0.05 if is_summer else 0) + np.random.normal(0, 0.02)
            )), 3
        )

        # Return customer rate (loyalty)
        return_rate = round(
            bl["return_rate_base"] + (m * 0.003) + np.random.normal(0, 0.02), 3
        )  # slight upward trend through year

        # Revenue per job
        rev_per_job = round(
            bl["rev_per_job_base"] * (1 + (m - 1) * 0.005) *  # +0.5% per month trend
            np.random.uniform(0.93, 1.07), 2
        )

        # Parts-to-labour ratio
        parts_ratio = round(np.random.uniform(0.30, 0.45), 3)

        # Complaints logged
        complaints = max(0, int(np.random.poisson(jobs_completed * 0.015)))

        records.append({
            "month":                 month.strftime("%Y-%m"),
            "quarter":               f"Q{month.quarter}",
            "branch":                branch,
            "jobs_target":           jobs_target,
            "jobs_completed":        jobs_completed,
            "completion_rate_pct":   completion_rate,
            "technician_count":      bl["tech_count"],
            "available_hours":       int(available_hours),
            "billed_hours":          int(billed_hours),
            "utilization_pct":       utilization_pct,
            "csat_score":            csat,
            "avg_wait_time_min":     int(avg_wait_min),
            "first_time_fix_rate":   ftfr,
            "return_customer_rate":  return_rate,
            "revenue_per_job_aed":   rev_per_job,
            "parts_to_labour_ratio": parts_ratio,
            "complaints_logged":     complaints,
        })

df = pd.DataFrame(records)
df.to_csv("/home/claude/Gulf-AutoServ-Analytics/datasets/raw/kpi_scorecard.csv", index=False)
print(f"kpi_scorecard.csv  →  {len(df)} rows")
print(df[["month","branch","jobs_completed","utilization_pct","csat_score","first_time_fix_rate","revenue_per_job_aed"]].head(9).to_string(index=False))
