-- =============================================================
-- Gulf AutoServ Analytics — PostgreSQL DDL
-- Database : Gulf Auto serve
-- Port     : 5433
-- Version  : PostgreSQL 18.0
-- =============================================================

-- Drop tables if re-running (order matters — dependents first)
DROP TABLE IF EXISTS wallet_transactions  CASCADE;
DROP TABLE IF EXISTS vat_invoices         CASCADE;
DROP TABLE IF EXISTS pos_sales            CASCADE;
DROP TABLE IF EXISTS partner_payments     CASCADE;
DROP TABLE IF EXISTS kpi_scorecard        CASCADE;
DROP TABLE IF EXISTS actuals_data         CASCADE;
DROP TABLE IF EXISTS budget_data          CASCADE;
DROP TABLE IF EXISTS five_year_plan       CASCADE;

-- =============================================================
-- 1. BUDGET_DATA
-- Composite PK: month + branch + category
-- =============================================================
CREATE TABLE budget_data (
    composite_key       VARCHAR(120)    NOT NULL,
    month               CHAR(7)         NOT NULL,   -- format: YYYY-MM
    branch              VARCHAR(50)     NOT NULL,
    category            VARCHAR(50)     NOT NULL,
    budget_amount_aed   NUMERIC(12, 2)  NOT NULL CHECK (budget_amount_aed > 0),
    currency            CHAR(3)         DEFAULT 'AED',
    fiscal_year         SMALLINT        NOT NULL,
    quarter             CHAR(2)         NOT NULL,
    PRIMARY KEY (month, branch, category)
);

CREATE INDEX idx_budget_branch  ON budget_data (branch);
CREATE INDEX idx_budget_month   ON budget_data (month);
CREATE INDEX idx_budget_quarter ON budget_data (quarter);

-- =============================================================
-- 2. ACTUALS_DATA
-- Composite PK: month + branch + category
-- =============================================================
CREATE TABLE actuals_data (
    composite_key       VARCHAR(120)    NOT NULL,
    month               CHAR(7)         NOT NULL,
    branch              VARCHAR(50)     NOT NULL,
    category            VARCHAR(50)     NOT NULL,
    budget_amount_aed   NUMERIC(12, 2)  NOT NULL,
    actual_amount_aed   NUMERIC(12, 2)  NOT NULL,
    variance_aed        NUMERIC(12, 2)  NOT NULL,
    variance_pct        NUMERIC(8, 2)   NOT NULL,
    currency            CHAR(3)         DEFAULT 'AED',
    fiscal_year         SMALLINT        NOT NULL,
    quarter             CHAR(2)         NOT NULL,
    spend_flag          VARCHAR(20),
    PRIMARY KEY (month, branch, category)
);

CREATE INDEX idx_actuals_branch     ON actuals_data (branch);
CREATE INDEX idx_actuals_month      ON actuals_data (month);
CREATE INDEX idx_actuals_spend_flag ON actuals_data (spend_flag);

-- =============================================================
-- 3. POS_SALES
-- PK: transaction_id
-- =============================================================
CREATE TABLE pos_sales (
    transaction_id      VARCHAR(20)     NOT NULL PRIMARY KEY,
    date                DATE            NOT NULL,
    time                TIME            NOT NULL,
    branch              VARCHAR(50)     NOT NULL,
    service_type        VARCHAR(50)     NOT NULL,
    total_amount_aed    NUMERIC(12, 2)  NOT NULL CHECK (total_amount_aed >= 0),
    parts_cost_aed      NUMERIC(12, 2)  NOT NULL CHECK (parts_cost_aed >= 0),
    labour_cost_aed     NUMERIC(12, 2)  NOT NULL CHECK (labour_cost_aed >= 0),
    payment_method      VARCHAR(30),
    status              VARCHAR(15)     NOT NULL CHECK (status IN ('Completed', 'Void')),
    month               CHAR(7)         NOT NULL,
    quarter             CHAR(2)         NOT NULL,
    day_of_week         VARCHAR(10),
    is_void             BOOLEAN         NOT NULL DEFAULT FALSE,
    revenue_aed         NUMERIC(12, 2)  NOT NULL DEFAULT 0
);

CREATE INDEX idx_pos_date    ON pos_sales (date);
CREATE INDEX idx_pos_branch  ON pos_sales (branch);
CREATE INDEX idx_pos_month   ON pos_sales (month);
CREATE INDEX idx_pos_status  ON pos_sales (status);
CREATE INDEX idx_pos_service ON pos_sales (service_type);

-- =============================================================
-- 4. VAT_INVOICES
-- PK: invoice_number
-- =============================================================
CREATE TABLE vat_invoices (
    invoice_number      VARCHAR(30)     NOT NULL PRIMARY KEY,
    invoice_date        DATE            NOT NULL,
    branch              VARCHAR(50)     NOT NULL,
    branch_trn          VARCHAR(15)     NOT NULL,
    customer_type       VARCHAR(5)      NOT NULL CHECK (customer_type IN ('B2B', 'B2C')),
    customer_trn        VARCHAR(15),
    service_category    VARCHAR(40),
    subtotal_aed        NUMERIC(12, 2)  NOT NULL CHECK (subtotal_aed > 0),
    vat_charged_aed     NUMERIC(12, 2)  NOT NULL CHECK (vat_charged_aed >= 0),
    total_aed           NUMERIC(12, 2)  NOT NULL CHECK (total_aed > 0),
    recalc_vat_aed      NUMERIC(12, 2)  NOT NULL,
    correct_total_aed   NUMERIC(12, 2)  NOT NULL,
    is_taxable          BOOLEAN         NOT NULL,
    b2b_missing_trn     BOOLEAN         NOT NULL DEFAULT FALSE,
    branch_trn_valid    BOOLEAN         NOT NULL DEFAULT TRUE,
    customer_trn_valid  BOOLEAN         NOT NULL DEFAULT TRUE,
    vat_error_flag      BOOLEAN         NOT NULL DEFAULT FALSE,
    total_mismatch_flag BOOLEAN         NOT NULL DEFAULT FALSE,
    exempt_vat_flag     BOOLEAN         NOT NULL DEFAULT FALSE,
    clean_error_flag    VARCHAR(80)     NOT NULL DEFAULT 'CLEAN',
    month               CHAR(7)         NOT NULL,
    quarter             CHAR(2)         NOT NULL
);

CREATE INDEX idx_vat_date       ON vat_invoices (invoice_date);
CREATE INDEX idx_vat_branch     ON vat_invoices (branch);
CREATE INDEX idx_vat_error_flag ON vat_invoices (clean_error_flag);
CREATE INDEX idx_vat_customer   ON vat_invoices (customer_type);

-- =============================================================
-- 5. PARTNER_PAYMENTS
-- PK: invoice_id
-- =============================================================
CREATE TABLE partner_payments (
    invoice_id          VARCHAR(15)     NOT NULL PRIMARY KEY,
    partner_name        VARCHAR(60)     NOT NULL,
    partner_type        VARCHAR(20)     NOT NULL,
    direction           VARCHAR(10)     NOT NULL CHECK (direction IN ('Inflow', 'Outflow')),
    issue_date          DATE            NOT NULL,
    due_date            DATE            NOT NULL,
    paid_date           DATE,
    subtotal_aed        NUMERIC(12, 2)  NOT NULL,
    vat_aed             NUMERIC(12, 2)  NOT NULL,
    total_aed           NUMERIC(12, 2)  NOT NULL,
    paid_amount_aed     NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    outstanding_aed     NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    payment_status      VARCHAR(15)     NOT NULL,
    payment_terms       VARCHAR(10),
    month               CHAR(7)         NOT NULL,
    quarter             CHAR(2)         NOT NULL,
    days_overdue        SMALLINT,
    CONSTRAINT chk_paid_date CHECK (paid_date IS NULL OR paid_date >= issue_date)
);

CREATE INDEX idx_partner_status    ON partner_payments (payment_status);
CREATE INDEX idx_partner_direction ON partner_payments (direction);
CREATE INDEX idx_partner_month     ON partner_payments (month);
CREATE INDEX idx_partner_name      ON partner_payments (partner_name);

-- =============================================================
-- 6. WALLET_TRANSACTIONS
-- PK: txn_id
-- =============================================================
CREATE TABLE wallet_transactions (
    txn_id              VARCHAR(15)     NOT NULL PRIMARY KEY,
    date                DATE            NOT NULL,
    branch              VARCHAR(50)     NOT NULL,
    txn_type            VARCHAR(15)     NOT NULL CHECK (txn_type IN ('Top-Up', 'Expense')),
    description         VARCHAR(80)     NOT NULL,
    amount_aed          NUMERIC(10, 2)  NOT NULL,
    amount_abs_aed      NUMERIC(10, 2)  NOT NULL CHECK (amount_abs_aed >= 0),
    balance_aed         NUMERIC(10, 2)  NOT NULL CHECK (balance_aed >= 0),
    flag                VARCHAR(30)     NOT NULL DEFAULT 'None',
    month               CHAR(7)         NOT NULL,
    quarter             CHAR(2)         NOT NULL
);

CREATE INDEX idx_wallet_branch ON wallet_transactions (branch);
CREATE INDEX idx_wallet_month  ON wallet_transactions (month);
CREATE INDEX idx_wallet_flag   ON wallet_transactions (flag);

-- =============================================================
-- 7. KPI_SCORECARD
-- Composite PK: month + branch
-- =============================================================
CREATE TABLE kpi_scorecard (
    composite_key           VARCHAR(60)     NOT NULL,
    month                   CHAR(7)         NOT NULL,
    quarter                 CHAR(2)         NOT NULL,
    branch                  VARCHAR(50)     NOT NULL,
    jobs_target             SMALLINT        NOT NULL,
    jobs_completed          SMALLINT        NOT NULL,
    completion_rate_pct     NUMERIC(5, 1)   NOT NULL,
    technician_count        SMALLINT        NOT NULL,
    available_hours         INTEGER         NOT NULL,
    billed_hours            INTEGER         NOT NULL,
    utilization_pct         NUMERIC(5, 1)   NOT NULL,
    csat_score              NUMERIC(3, 2)   NOT NULL CHECK (csat_score BETWEEN 1 AND 5),
    avg_wait_time_min       SMALLINT        NOT NULL,
    first_time_fix_rate     NUMERIC(5, 3)   NOT NULL CHECK (first_time_fix_rate BETWEEN 0 AND 1),
    return_customer_rate    NUMERIC(5, 3)   NOT NULL CHECK (return_customer_rate BETWEEN 0 AND 1),
    revenue_per_job_aed     NUMERIC(10, 2)  NOT NULL,
    parts_to_labour_ratio   NUMERIC(5, 3)   NOT NULL,
    complaints_logged       SMALLINT        NOT NULL DEFAULT 0,
    csat_band               VARCHAR(15)     NOT NULL,
    PRIMARY KEY (month, branch)
);

CREATE INDEX idx_kpi_branch  ON kpi_scorecard (branch);
CREATE INDEX idx_kpi_quarter ON kpi_scorecard (quarter);

-- =============================================================
-- 8. FIVE_YEAR_PLAN
-- Composite PK: year + revenue_stream
-- =============================================================
CREATE TABLE five_year_plan (
    year                        SMALLINT        NOT NULL,
    data_type                   VARCHAR(10)     NOT NULL CHECK (data_type IN ('Actual', 'Target')),
    revenue_stream              VARCHAR(30)     NOT NULL,
    revenue_aed_000s            INTEGER         NOT NULL,
    total_revenue_aed_000s      INTEGER         NOT NULL,
    gross_profit_aed_000s       INTEGER         NOT NULL,
    gross_margin_pct            NUMERIC(5, 1)   NOT NULL,
    ebitda_aed_000s             INTEGER         NOT NULL,
    ebitda_margin_pct           NUMERIC(5, 1)   NOT NULL,
    net_profit_aed_000s         INTEGER         NOT NULL,
    net_margin_pct              NUMERIC(5, 1)   NOT NULL,
    capex_aed_000s              INTEGER         NOT NULL,
    headcount                   SMALLINT        NOT NULL,
    strategic_theme             VARCHAR(80)     NOT NULL,
    statistical_note            VARCHAR(120)    NOT NULL,
    PRIMARY KEY (year, revenue_stream)
);

CREATE INDEX idx_plan_year      ON five_year_plan (year);
CREATE INDEX idx_plan_data_type ON five_year_plan (data_type);

-- =============================================================
-- Verify all tables created
-- =============================================================
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = t.table_name
     AND table_schema = 'public') AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND   table_type   = 'BASE TABLE'
ORDER BY table_name;
