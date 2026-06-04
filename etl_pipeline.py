import pandas as pd
import numpy as np
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean, ForeignKey
import os

def clean_and_transform():
    print("Extracting datasets...")
    # Load raw data
    if not os.path.exists("customers.csv") or not os.path.exists("accounts.csv") or not os.path.exists("raw_transactions.csv"):
        raise FileNotFoundError("Raw CSV files not found. Run generate_data.py first.")

    df_cust = pd.read_csv("customers.csv")
    df_acc = pd.read_csv("accounts.csv")
    df_tx = pd.read_csv("raw_transactions.csv")

    print(f"Initial raw rows - Customers: {len(df_cust)}, Accounts: {len(df_acc)}, Transactions: {len(df_tx)}")

    # 1. Clean Data: Remove Duplicates
    df_cust.drop_duplicates(subset=["Customer_ID"], inplace=True)
    df_acc.drop_duplicates(subset=["Account_Number"], inplace=True)
    df_tx.drop_duplicates(subset=["Transaction_ID"], inplace=True)

    # 2. Clean Data: Handle Missing Values
    # In a real environment we would impute or drop. Here we fill any blanks with defaults.
    df_cust["Name"] = df_cust["Name"].fillna("Unknown Customer")
    df_cust["Income"] = df_cust["Income"].fillna(df_cust["Income"].median())
    df_cust["Segment"] = df_cust["Segment"].fillna("Salary")
    
    df_acc["Balance"] = df_acc["Balance"].fillna(0.0)
    df_acc["Account_Type"] = df_acc["Account_Type"].fillna("Checking")

    df_tx["Amount"] = df_tx["Amount"].fillna(0.0)
    df_tx["Transaction_Type"] = df_tx["Transaction_Type"].fillna("Debit")
    df_tx["Category"] = df_tx["Category"].fillna("Shopping")
    df_tx["Merchant_Name"] = df_tx["Merchant_Name"].fillna("Unknown Merchant")

    # 3. Format Date/Times
    df_cust["Join_Date"] = pd.to_datetime(df_cust["Join_Date"]).dt.strftime("%Y-%m-%d")
    df_tx["Date"] = pd.to_datetime(df_tx["Date"]).dt.strftime("%Y-%m-%d")
    
    # 4. Feature Engineering
    # A. Transaction Hour
    df_tx["Transaction_Hour"] = pd.to_datetime(df_tx["Time"], format="%H:%M:%S").dt.hour
    
    # B. Transaction Month
    df_tx["Transaction_Month"] = pd.to_datetime(df_tx["Date"]).dt.strftime("%Y-%m")
    
    # C. High Value Transaction indicator (Debit amounts > $1,500)
    df_tx["is_high_value"] = ((df_tx["Amount"] > 1500) & (df_tx["Transaction_Type"] == "Debit")).astype(int)
    
    # D. Spending Category Flags
    df_tx["is_essential"] = df_tx["Category"].isin(["Food", "Bills", "EMI"]).astype(int)
    df_tx["is_leisure"] = df_tx["Category"].isin(["Travel", "Shopping"]).astype(int)
    df_tx["is_cash_out"] = df_tx["Category"].isin(["Cash Withdrawal"]).astype(int)

    print(f"Transformed data rows - Customers: {len(df_cust)}, Accounts: {len(df_acc)}, Transactions: {len(df_tx)}")
    
    return df_cust, df_acc, df_tx

def load_into_database(df_cust, df_acc, df_tx, db_url="sqlite:///banking.db"):
    print(f"Loading data into SQL Database: {db_url}...")
    engine = create_engine(db_url)
    
    # 1. Initialize schema from schema.sql
    if os.path.exists("schema.sql"):
        print("Executing schema.sql DDL setup...")
        with open("schema.sql", "r") as f:
            schema_sql = f.read()
        
        # SQLite cannot run multiple statements in a single connection.execute easily, so we split
        statements = schema_sql.split(";")
        with engine.begin() as connection:
            for statement in statements:
                stmt_stripped = statement.strip()
                if stmt_stripped:
                    connection.exec_driver_sql(stmt_stripped)
    else:
        print("Warning: schema.sql not found, writing directly.")

    with engine.begin() as connection:
        # Load customers
        df_cust.to_sql("customers", con=connection, if_exists="append", index=False)
        # Load accounts
        df_acc.to_sql("accounts", con=connection, if_exists="append", index=False)
        # Load transactions
        df_tx.to_sql("transactions", con=connection, if_exists="append", index=False)

    print("Database load completed successfully.")

def main():
    try:
        df_cust, df_acc, df_tx = clean_and_transform()
        load_into_database(df_cust, df_acc, df_tx)
        print("ETL Pipeline Execution Finished Successfully.")
    except Exception as e:
        print(f"Error executing ETL pipeline: {e}")
        raise e

if __name__ == "__main__":
    main()
