import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import os

def run_customer_segmentation(engine):
    print("Executing Customer Segmentation...")
    # Load customers, accounts, and transactions
    df_cust = pd.read_sql("SELECT * FROM customers", con=engine)
    df_acc = pd.read_sql("SELECT * FROM accounts", con=engine)
    df_tx = pd.read_sql("SELECT * FROM transactions", con=engine)
    
    # Calculate key metrics per customer
    # 1. Total balance across all accounts
    balance_per_cust = df_acc.groupby("Customer_ID")["Balance"].sum().reset_index()
    balance_per_cust.columns = ["Customer_ID", "Total_Balance"]
    
    # 2. Transaction volume & frequency
    # We map accounts to customers
    acc_cust_map = df_acc.set_index("Account_Number")["Customer_ID"].to_dict()
    df_tx["Customer_ID"] = df_tx["Account_Number"].map(acc_cust_map)
    
    tx_metrics = df_tx[df_tx["Transaction_Type"] == 'Debit'].groupby("Customer_ID").agg(
        Total_Spend=("Amount", "sum"),
        Tx_Count=("Transaction_ID", "count")
    ).reset_index()
    
    # 3. Recency (days of inactivity)
    latest_date = pd.to_datetime(df_tx["Date"].max())
    last_tx = df_tx.groupby("Customer_ID")["Date"].max().reset_index()
    last_tx["Last_Active_Date"] = pd.to_datetime(last_tx["Date"])
    last_tx["Inactivity_Days"] = (latest_date - last_tx["Last_Active_Date"]).dt.days
    last_tx = last_tx[["Customer_ID", "Inactivity_Days"]]
    
    # Merge all into segment base
    df_seg = df_cust.merge(balance_per_cust, on="Customer_ID", how="left")
    df_seg = df_seg.merge(tx_metrics, on="Customer_ID", how="left")
    df_seg = df_seg.merge(last_tx, on="Customer_ID", how="left")
    
    df_seg["Total_Balance"] = df_seg["Total_Balance"].fillna(0.0)
    df_seg["Total_Spend"] = df_seg["Total_Spend"].fillna(0.0)
    df_seg["Tx_Count"] = df_seg["Tx_Count"].fillna(0)
    df_seg["Inactivity_Days"] = df_seg["Inactivity_Days"].fillna(365) # Max if no tx
    
    # Threshold percentiles
    balance_80th = df_seg["Total_Balance"].quantile(0.80)
    income_80th = df_seg["Income"].quantile(0.80)
    tx_count_80th = df_seg["Tx_Count"].quantile(0.80)
    
    # Segmentation Classification Logic
    def assign_segment(row):
        if row["Inactivity_Days"] >= 60:
            return "Dormant Customer"
        elif row["Total_Balance"] >= balance_80th or row["Income"] >= income_80th:
            return "High-Value Customer"
        elif row["Segment"] == "Salary":
            return "Salary Account Holder"
        elif row["Tx_Count"] >= tx_count_80th:
            return "Credit Card Heavy / Active Spender"
        else:
            return "Standard Retail Customer"
            
    df_seg["Calculated_Segment"] = df_seg.apply(assign_segment, axis=1)
    
    # Write customer segments to database
    df_upload = df_seg[["Customer_ID", "Total_Balance", "Total_Spend", "Tx_Count", "Inactivity_Days", "Calculated_Segment"]]
    df_upload.to_sql("customer_segments", con=engine, if_exists="replace", index=False)
    print(f"Customer segmentation complete. Uploaded {len(df_upload)} labeled rows.")
    return df_seg

def run_fraud_detection(engine):
    print("Executing Fraud and Anomaly Detection Engine...")
    
    # Load transactions and account details
    df_tx = pd.read_sql("SELECT * FROM transactions", con=engine)
    df_acc = pd.read_sql("SELECT * FROM accounts", con=engine)
    acc_cust_map = df_acc.set_index("Account_Number")["Customer_ID"].to_dict()
    
    # We analyze Debit transactions for fraud/risk
    df_debit = df_tx[df_tx["Transaction_Type"] == 'Debit'].copy()
    
    if len(df_debit) == 0:
        print("No debit transactions found to analyze.")
        return
        
    print(f"Analyzing {len(df_debit)} debit transactions...")
    
    # Feature 1: Historical average transaction size ratio
    # Calculate account average transaction size
    acct_avg = df_debit.groupby("Account_Number")["Amount"].mean().to_dict()
    acct_std = df_debit.groupby("Account_Number")["Amount"].std().to_dict()
    
    df_debit["Acct_Avg_Amount"] = df_debit["Account_Number"].map(acct_avg)
    df_debit["Acct_Std_Amount"] = df_debit["Account_Number"].map(acct_std).fillna(1.0)
    df_debit["Amount_Ratio"] = df_debit["Amount"] / (df_debit["Acct_Avg_Amount"] + 1e-5)
    
    # Feature 2: Z-Score (Statistical Anomaly)
    df_debit["Z_Score"] = (df_debit["Amount"] - df_debit["Acct_Avg_Amount"]) / df_debit["Acct_Std_Amount"]
    df_debit["Z_Score"] = df_debit["Z_Score"].fillna(0.0)
    
    # Feature 3: Transaction Velocity (number of transactions on the same day for this account)
    velocity = df_debit.groupby(["Account_Number", "Date"])["Transaction_ID"].count().reset_index()
    velocity.columns = ["Account_Number", "Date", "Daily_Tx_Count"]
    df_debit = df_debit.merge(velocity, on=["Account_Number", "Date"], how="left")
    
    # Define features for Isolation Forest
    features = ["Amount", "Transaction_Hour", "Amount_Ratio", "Daily_Tx_Count", "is_high_value", "is_essential", "is_leisure", "is_cash_out"]
    
    # Standardize features
    scaler = StandardScaler()
    X = scaler.fit_transform(df_debit[features])
    
    # Fit Isolation Forest (Unsupervised ML)
    # Contamination set to 1.5% to capture standard deviations
    iso = IsolationForest(n_estimators=100, contamination=0.015, random_state=42)
    iso.fit(X)
    
    # -1 for anomaly, 1 for normal
    predictions = iso.predict(X)
    decision_scores = iso.decision_function(X) # Lower = more anomalous
    
    # Create output flags
    df_debit["Iso_Anomaly"] = (predictions == -1).astype(int)
    
    # Normalize decision scores to a 0-1 risk score (where 1 is highest risk)
    # Decision scores are typically in range [-0.5, 0.5]. Let's invert and min-max scale.
    min_score = decision_scores.min()
    max_score = decision_scores.max()
    df_debit["Risk_Score_ML"] = 1.0 - ((decision_scores - min_score) / (max_score - min_score + 1e-5))
    
    # Composite Risk Score (combining ML risk score and Z-score deviation)
    # Z-score of 3 or more is extremely rare, we cap and normalize Z-score to [0, 1]
    df_debit["Risk_Score_Stat"] = np.clip(df_debit["Z_Score"] / 5.0, 0, 1)
    
    # Composite Risk Score weighting: 60% ML, 40% Statistical
    df_debit["risk_score"] = (df_debit["Risk_Score_ML"] * 0.6) + (df_debit["Risk_Score_Stat"] * 0.4)
    df_debit["risk_score"] = df_debit["risk_score"].round(4)
    
    # Fraud flag (1 if flagged by Isolation Forest OR Z-Score > 3.5 OR risk_score > 0.70)
    df_debit["fraud_flag"] = ((df_debit["Iso_Anomaly"] == 1) | (df_debit["Z_Score"] > 3.5) | (df_debit["risk_score"] > 0.70)).astype(int)
    
    # Determine alert reason
    def get_alert_reason(row):
        if row["fraud_flag"] == 0:
            return "Normal"
        reasons = []
        if row["Iso_Anomaly"] == 1:
            reasons.append("ML Outlier")
        if row["Z_Score"] > 3.5:
            reasons.append(f"Z-Score Spike ({row['Z_Score']:.1f})")
        if row["Daily_Tx_Count"] >= 4:
            reasons.append(f"High Velocity ({row['Daily_Tx_Count']} tx/day)")
        if row["Merchant_Name"] == "LUXURY_JEWELERS_INC":
            reasons.append("Suspicious Merchant Location")
        return ", ".join(reasons) if reasons else "High Risk Flag"

    df_debit["alert_reason"] = df_debit.apply(get_alert_reason, axis=1)
    
    # Upload alerts to fraud_alerts table
    df_alerts = df_debit[df_debit["fraud_flag"] == 1][["Transaction_ID", "Account_Number", "risk_score", "fraud_flag", "alert_reason"]]
    df_alerts.to_sql("fraud_alerts", con=engine, if_exists="replace", index=False)
    
    # Also save the full transaction scoring table
    df_risk_full = df_debit[["Transaction_ID", "Z_Score", "Daily_Tx_Count", "Iso_Anomaly", "risk_score", "fraud_flag", "alert_reason"]]
    df_risk_full.to_sql("transaction_risk_scores", con=engine, if_exists="replace", index=False)
    
    print(f"Risk analysis complete. Identified {len(df_alerts)} anomalous transactions. Risk results saved in SQL database.")

def main():
    db_url = "sqlite:///banking.db"
    engine = create_engine(db_url)
    
    try:
        run_customer_segmentation(engine)
        run_fraud_detection(engine)
        print("ML Risk and Segmentation Engine completed successfully.")
    except Exception as e:
        print(f"Error executing ML Risk and Segmentation engine: {e}")
        raise e

if __name__ == "__main__":
    main()
