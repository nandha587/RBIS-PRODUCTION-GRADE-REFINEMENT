# Retail Banking Intelligence System (RBIS) — Operations & Risk Platform

**Retail Banking Intelligence System (RBIS)** is an end-to-end, banking-grade data engineering, analytics, and compliance surveillance platform. It simulates core banking operations (savings/checking account ledgers, credit card spend profiles, and recurring loan schedules), constructs a normalized relational database warehouse with optimized indexing, trains machine learning models to detect fraud anomalies, and serves reports via automated PDF generators and interactive web dashboards.

---

## 🏗️ System Architecture

```
                                  [ RAW DATA LAYER ]
                       Simulates customer & transaction histories
                                (generate_data.py)
                                        │
                                        ▼
                             raw_transactions.csv
                                        │
                                        ▼
                                 [ ETL ENGINE ]
                     Data Cleansing, Formats, engineered indices
                                (etl_pipeline.py)
                                        │
                                        ▼
                            [ DATABASE STORAGE LAYER ]
                        SQL tables with relational constraints
                                   (banking.db)
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
    [ SQL ANALYTICS ]                                       [ ML RISK ENGINE ]
CTEs, Window functions, RFM                     Isolation Forest ML & Z-Score stats
(analytics_queries.sql)                               (analytics_risk_engine.py)
             │                                                     │
             └──────────────────────────┬──────────────────────────┘
                                        ▼
                               [ PRESENTATION LAYER ]
              ┌─────────────────────────┴─────────────────────────┐
              ▼                                                   ▼
     [ STREAMLIT WEB APP ]                                [ PDF EXECUTIVE REPORT ]
Interactive charts, filters & drilldowns                    Aggregate KPI Summaries
            (app.py)                                     (automation_reporter.py)
```

---

## 🗂️ Project Directory Structure

```text
retail_banking_intelligence/
│
├── requirements.txt           # Library dependencies (pandas, scikit-learn, etc.)
├── generate_data.py           # Synthetic ledger generator (60,000+ records)
├── etl_pipeline.py            # Data cleaning and SQL database loading script
├── schema.sql                 # SQL schema definitions, constraints, and indices
├── analytics_queries.sql      # Advanced SQL analytical reporting queries
├── analytics_risk_engine.py   # RFM Customer Segmentation & ML Anomaly Detection
├── automation_reporter.py     # reportlab PDF generator script
├── app.py                     # Streamlit multi-tab analytics dashboard
├── run_pipeline.py            # End-to-end pipeline orchestrator
├── banking.db                 # Structured SQLite core database (Generated)
└── daily_risk_report.pdf      # Operations PDF audit report (Generated)
```

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.10 or higher
- `pip` (Python package installer)

### Quick Start Guide

1. **Clone or Navigate to the Workspace Directory:**
   ```powershell
   cd C:\Users\absuj\.gemini\antigravity\scratch\retail_banking_intelligence
   ```

2. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Orchestrate and Run the Full Pipeline:**
   ```powershell
   python run_pipeline.py
   ```
   *This single command triggers the data generation, builds database constraints, populates records, executes the SQL queries, trains the ML classifier, and creates the PDF report.*

4. **Launch the Surveillance Portal:**
   ```powershell
   streamlit run app.py
   ```

---

## 🛠️ Module Breakdown

### 1. Data Generation Engine (`generate_data.py`)
Generates 1,000 customers and 1,729 accounts (Checking/Savings) distributed across four profiles: **Salary, Business, Student, and Retired**.
- **Historical Window:** 12 Months (June 1, 2025 – May 31, 2026).
- **Core Ledger Consistency:** Simulates recurring monthly credits (salaries) and automated monthly checking debits (EMIs) to ensure data reflects typical transaction history.
- **Anomalies Injected:**
  - **Outliers:** 20 sudden large transaction amounts ($7,000 to $18,000) at high-risk merchants.
  - **Velocity Spikes:** 15 accounts with 4 rapid transactions within minutes.
  - **Dormancy:** Injecting 60+ days of inactivity into a subset of accounts.

### 2. Clean, Transform, & Load Engine (`etl_pipeline.py`)
Cleanses the generated data, handles missing metrics, formats dates, and applies feature engineering.
- **Engineered Fields:**
  - `Transaction_Hour` & `Transaction_Month`
  - `is_high_value`: Boolean flag highlighting debits exceeding $1,500.
  - `is_essential`: Flags utility, food, and loan expenses.
  - `is_leisure`: Flags dining, shopping, and travel expenses.
  - `is_cash_out`: Flags ATM withdrawals.

### 3. Core SQL Database Schema (`schema.sql`)
Initializes tables with explicit primary keys, relational foreign keys, and indices.
- **Schema Entities:** `customers`, `accounts`, `transactions`.
- **Indexing Strategy:** Optimized lookup performance via indices on filtering columns:
  - `idx_transactions_account` on `transactions(Account_Number)`
  - `idx_transactions_date` on `transactions(Date)`
  - `idx_transactions_composite` on `transactions(Account_Number, Date, Amount)`

### 4. Advanced Database Analytics (`analytics_queries.sql`)
Contains complex queries designed to answer corporate finance questions:
- **Monthly Spend Trends:** Evaluates customer spending behaviors over time.
- **High-Value Client Rankings:** Ranks customers using `DENSE_RANK() OVER (ORDER BY SUM(Amount) DESC)` to support targeted wealth management offers.
- **Category Share:** Evaluates merchant category spend percentages.
- **Portfolio Dormancy:** Identifies accounts with zero transactions over the last 60 days using Julian date calculations.

### 5. Risk Intelligence & ML Engine (`analytics_risk_engine.py`)
- **Customer Segmentation:** Applies RFM logic using customer income, transaction counts, balance sizes, and inactivity metrics to classify portfolios into:
  - *High-Value Customers* (top 20% in balance/income)
  - *Salary Account Holders* (active users with recurring salary deposits)
  - *Active Spenders* (top 20% in transaction count)
  - *Dormant Customers* (inactive for > 60 days)
  - *Standard Retail Customers*
- **Fraud Engine:** Trains a scikit-learn **Isolation Forest** classifier on transaction amounts, velocity spikes, and category indices. Combines these predictions with historical transaction **Z-Scores** to generate a continuous `risk_score` (0.0 to 1.0) and log flagged transactions to the `fraud_alerts` table.

### 6. Interactive Portal (`app.py`)
A dashboard built in Streamlit and styled with a professional corporate color palette (Navy and Charcoal), featuring four interactive pages:
- **Executive Overview:** High-level metrics showing deposit totals, spend volumes, and active alerts.
- **Customer RFM:** Features segment pie charts and searchable customer tables.
- **Spending & Revenue:** Interactive category charts and merchant concentration bars.
- **Fraud Surveillance:** Filters fraud tables by risk score thresholds and maps outliers.

### 7. PDF Report Generator (`automation_reporter.py`)
Uses ReportLab to generate a styled operational report `daily_risk_report.pdf`. Features formatted summary tables, recent compliance alerts, and embedded spending category and risk distribution charts.

---

## 📈 Enterprise Production Scaling

To transition this system from a local prototype to a production environment:

### 1. Database Migration Path (SQLite ➔ PostgreSQL)
For high-concurrency production usage:
- Update database endpoints in python configurations using environment variables.
- Scale SQL data types to PostgreSQL: change SQLite's `REAL` to `DECIMAL(15, 2)` to prevent rounding errors.
- Create read replicas to handle dashboard queries without degrading transaction processing speeds.

### 2. High-Volume Spark ETL Integration
For processing millions of daily transactions, convert `etl_pipeline.py` to run on an Apache Spark cluster:
```python
# PySpark equivalent for feature engineering
from pyspark.sql import functions as F

df_tx = df_tx.withColumn("is_high_value", F.when((F.col("Amount") > 1500) & (F.col("Transaction_Type") == "Debit"), 1).otherwise(0))
```

### 3. Kafka Real-Time Ingestion
Rather than executing batch loads, ingest transactions using Apache Kafka streams. Standardize JSON validation on input streams and pass records through trained ML models in real-time before writing them to database tables.
