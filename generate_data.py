import csv
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

def generate_demographics():
    first_names = ["John", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Elizabeth", "David", "Barbara", 
                   "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy",
                   "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
                   "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna", "Kenneth", "Michelle",
                   "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa", "Edward", "Deborah", "Ronald", "Stephanie"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
                  "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
                  "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"]
    
    states = ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "AZ", "CO", "MA", "VA", "NJ"]
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    state = random.choice(states)
    return f"{first} {last}", state

def generate_customers_and_accounts(num_customers=1000):
    customers = []
    accounts = []
    
    segments = ["Salary", "Business", "Student", "Retired"]
    segment_weights = [0.60, 0.15, 0.15, 0.10]
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 1, 1)
    
    for i in range(1, num_customers + 1):
        cust_id = f"CUST{i:04d}"
        name, state = generate_demographics()
        segment = random.choices(segments, weights=segment_weights)[0]
        
        # Realistic income and join date based on segment
        if segment == "Salary":
            income = round(np.random.normal(75000, 25000))
            income = max(30000, min(income, 220000))
        elif segment == "Business":
            income = round(np.random.normal(120000, 50000))
            income = max(40000, min(income, 500000))
        elif segment == "Student":
            income = round(np.random.normal(15000, 5000))
            income = max(5000, min(income, 30000))
        else:  # Retired
            income = round(np.random.normal(45000, 15000))
            income = max(20000, min(income, 90000))
            
        days_active = random.randint(0, (end_date - start_date).days)
        join_date = (start_date + timedelta(days=days_active)).strftime("%Y-%m-%d")
        
        customers.append({
            "Customer_ID": cust_id,
            "Name": name,
            "Income": income,
            "Segment": segment,
            "Join_Date": join_date,
            "State": state
        })
        
        # Accounts
        # Standard: 1 Checking + optional Savings account
        checking_acc = f"ACC{10000000 + i*2:08d}"
        starting_bal = round(random.uniform(500, 5000) if segment == "Student" else random.uniform(2000, 20000))
        
        accounts.append({
            "Account_Number": checking_acc,
            "Customer_ID": cust_id,
            "Account_Type": "Checking",
            "Balance": starting_bal
        })
        
        # Savings account (80% of Salary/Business/Retired, 20% of Students)
        has_savings = random.random() < (0.80 if segment != "Student" else 0.20)
        if has_savings:
            savings_acc = f"ACC{10000000 + i*2 + 1:08d}"
            starting_bal_sav = round(random.uniform(1000, 10000) if segment == "Student" else random.uniform(5000, 100000))
            accounts.append({
                "Account_Number": savings_acc,
                "Customer_ID": cust_id,
                "Account_Type": "Savings",
                "Balance": starting_bal_sav
            })
            
    return pd.DataFrame(customers), pd.DataFrame(accounts)

def generate_transactions(df_customers, df_accounts, num_transactions=60000):
    # Setup categories and merchants
    merchants = {
        "Food": ["Starbucks", "McDonalds", "Whole Foods", "Subway", "Dominos", "UberEats", "Kroger", "Chipotle"],
        "Travel": ["Uber", "Delta Airlines", "Chevron", "Shell", "Airbnb", "Lyft", "Expedia", "Amtrack"],
        "Bills": ["Verizon", "Comcast", "Electric Co", "State Farm", "Water Utility", "Geico", "Netflix", "Spotify"],
        "EMI": ["Chase Auto Finance", "Wells Fargo Home Mortgage", "Sallie Mae Student Loan", "Ally Financial"],
        "Shopping": ["Amazon", "Walmart", "Target", "Apple Store", "BestBuy", "Macy's", "Nike", "Home Depot"],
        "Cash Withdrawal": ["ATM Withdrawal", "ATM Cash Out"]
    }
    
    credit_categories = ["Salary", "Interest", "Deposit", "Refund"]
    credit_merchants = ["Employer Direct Deposit", "Bank Interest Payment", "Cash Deposit ATM", "Merchant Refund"]
    
    transactions = []
    
    # Track current balances in a dict for performance
    balances = df_accounts.set_index("Account_Number")["Balance"].to_dict()
    account_customer_map = df_accounts.set_index("Account_Number")["Customer_ID"].to_dict()
    customer_segment_map = df_customers.set_index("Customer_ID")["Segment"].to_dict()
    customer_income_map = df_customers.set_index("Customer_ID")["Income"].to_dict()
    
    # Establish transaction schedule over a 12-month period (June 1, 2025 to May 31, 2026)
    start_date = datetime(2025, 6, 1, 0, 0, 0)
    total_seconds = 365 * 24 * 60 * 60 # 1 year
    
    # Generate structured base transactions (salaries, EMIs) to ensure realism
    account_numbers = df_accounts["Account_Number"].tolist()
    
    print("Generating base credits and recurring expenses...")
    # Add Monthly Salary Deposits for Salary Segment & monthly Interest/Refunds
    for acc in account_numbers:
        cust_id = account_customer_map[acc]
        segment = customer_segment_map[cust_id]
        acc_type = df_accounts[df_accounts["Account_Number"] == acc]["Account_Type"].values[0]
        
        if acc_type == "Checking" and segment == "Salary":
            # Direct deposit monthly on the 1st
            income = customer_income_map[cust_id]
            monthly_salary = round((income / 12) * 0.75) # After tax estimate
            for m in range(12):
                tx_date = start_date + timedelta(days=m*30 + random.randint(0, 2))
                tx_time = f"{random.randint(8, 11):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                balances[acc] += monthly_salary
                
                transactions.append({
                    "Transaction_ID": f"TXN{len(transactions)+1:06d}",
                    "Account_Number": acc,
                    "Date": tx_date.strftime("%Y-%m-%d"),
                    "Time": tx_time,
                    "Amount": monthly_salary,
                    "Transaction_Type": "Credit",
                    "Category": "Salary",
                    "Merchant_Name": "Employer Direct Deposit",
                    "Account_Balance": balances[acc]
                })
                
        # Add monthly EMI if they have checking
        if acc_type == "Checking" and segment != "Student":
            # Recurring EMI on the 10th
            emi_amount = round(random.uniform(300, 1800) if segment == "Business" else random.uniform(200, 1200))
            emi_merchant = random.choice(merchants["EMI"])
            for m in range(12):
                tx_date = start_date + timedelta(days=m*30 + 9) # 10th of the month
                tx_time = f"08:00:00"
                balances[acc] -= emi_amount
                
                transactions.append({
                    "Transaction_ID": f"TXN{len(transactions)+1:06d}",
                    "Account_Number": acc,
                    "Date": tx_date.strftime("%Y-%m-%d"),
                    "Time": tx_time,
                    "Amount": emi_amount,
                    "Transaction_Type": "Debit",
                    "Category": "EMI",
                    "Merchant_Name": emi_merchant,
                    "Account_Balance": balances[acc]
                })

    print(f"Generated {len(transactions)} base transactions. Simulating general transaction activity...")
    
    # Fill remaining transactions to reach target
    remaining_tx = num_transactions - len(transactions)
    
    # Select account frequencies based on customer segments (Business and CC Heavy spend more frequently)
    acc_weights = []
    for acc in account_numbers:
        cust_id = account_customer_map[acc]
        segment = customer_segment_map[cust_id]
        if segment == "Business":
            acc_weights.append(5.0)
        elif segment == "Salary":
            acc_weights.append(3.0)
        elif segment == "Retired":
            acc_weights.append(1.5)
        else: # Student
            acc_weights.append(1.0)
            
    # Normalize weights
    acc_weights = np.array(acc_weights) / sum(acc_weights)
    
    # Pre-generate dates to keep them uniformly distributed across the year
    random_seconds = np.random.randint(0, total_seconds, size=remaining_tx)
    random_dates = [start_date + timedelta(seconds=int(s)) for s in random_seconds]
    random_dates.sort() # Keep chronological
    
    # Track dormant customer IDs to inject 60+ days dormancy for some customers (e.g. 5% of customers)
    num_dormant = int(len(df_customers) * 0.05)
    dormant_customers = df_customers.sample(n=num_dormant, random_state=42)["Customer_ID"].tolist()
    dormant_accounts = df_accounts[df_accounts["Customer_ID"].isin(dormant_customers)]["Account_Number"].tolist()
    
    # Filter active accounts for regular transaction generation
    active_acc_mask = ~df_accounts["Account_Number"].isin(dormant_accounts)
    active_accounts = df_accounts[active_acc_mask]["Account_Number"].tolist()
    active_acc_weights = [acc_weights[df_accounts["Account_Number"] == acc][0] for acc in active_accounts]
    active_acc_weights = np.array(active_acc_weights) / sum(active_acc_weights)

    # We will generate dormant customer transactions only in the first 6 months, ensuring they have 60+ days of dormancy in the final period
    cutoff_date = start_date + timedelta(days=180)

    for i in range(remaining_tx):
        tx_dt = random_dates[i]
        
        # Decide if this transaction is for a dormant account (skip if date is after cutoff)
        if random.random() < 0.05: # 5% transactions go to dormant accounts
            acc = random.choice(dormant_accounts)
            if tx_dt > cutoff_date:
                # Re-route to an active account
                acc = np.random.choice(active_accounts, p=active_acc_weights)
        else:
            acc = np.random.choice(active_accounts, p=active_acc_weights)
            
        cust_id = account_customer_map[acc]
        segment = customer_segment_map[cust_id]
        
        # Decide Debit vs Credit
        # Debits are 85% likely, Credits (deposits, refunds) are 15% likely
        tx_type = random.choices(["Debit", "Credit"], weights=[0.85, 0.15])[0]
        
        if tx_type == "Debit":
            # Spending Categories
            cats = ["Food", "Travel", "Bills", "Shopping", "Cash Withdrawal"]
            cat_w = [0.40, 0.20, 0.15, 0.20, 0.05]
            category = random.choices(cats, weights=cat_w)[0]
            merchant = random.choice(merchants[category])
            
            # Amount details based on category and segment
            if category == "Food":
                amount = round(random.uniform(5, 50) if segment == "Student" else random.uniform(10, 150), 2)
            elif category == "Travel":
                amount = round(random.uniform(8, 40) if random.random() < 0.8 else random.uniform(150, 600), 2) # Ride sharing vs Flight
            elif category == "Bills":
                amount = round(random.uniform(15, 120) if segment == "Student" else random.uniform(40, 450), 2)
            elif category == "Shopping":
                amount = round(random.uniform(10, 100) if segment == "Student" else random.uniform(20, 1200), 2)
            else: # Cash Withdrawal
                amount = round(random.choice([20, 40, 60, 100, 200, 300, 400]))
                
            balances[acc] -= amount
            
        else: # Credit
            category = random.choices(credit_categories[1:], weights=[0.40, 0.40, 0.20])[0] # Exclude Salary
            merchant = random.choice(credit_merchants[1:])
            
            if category == "Deposit":
                amount = round(random.choice([50, 100, 200, 500, 1000]))
            elif category == "Refund":
                amount = round(random.uniform(10, 150), 2)
            else: # Interest
                amount = round(balances[acc] * 0.0015, 2) # Small interest
                
            balances[acc] += amount
            
        transactions.append({
            "Transaction_ID": f"TXN{len(transactions)+1:06d}",
            "Account_Number": acc,
            "Date": tx_dt.strftime("%Y-%m-%d"),
            "Time": tx_dt.strftime("%H:%M:%S"),
            "Amount": amount,
            "Transaction_Type": tx_type,
            "Category": category,
            "Merchant_Name": merchant,
            "Account_Balance": round(balances[acc], 2)
        })

    # Now let's inject explicit fraud anomalies to be caught by scikit-learn Isolation Forest & Z-Score
    print("Injecting fraud and anomaly patterns...")
    
    # 1. Sudden massive shopping transaction (Outlier) - 20 records
    anomaly_accounts = random.sample(active_accounts, 20)
    for acc in anomaly_accounts:
        tx_dt = start_date + timedelta(days=random.randint(15, 350))
        # Massive amount relative to average transaction
        amount = round(random.uniform(7000, 18000), 2)
        balances[acc] -= amount
        
        transactions.append({
            "Transaction_ID": f"TXN{len(transactions)+1:06d}",
            "Account_Number": acc,
            "Date": tx_dt.strftime("%Y-%m-%d"),
            "Time": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
            "Amount": amount,
            "Transaction_Type": "Debit",
            "Category": "Shopping",
            "Merchant_Name": "LUXURY_JEWELERS_INC", # Flagged merchant
            "Account_Balance": round(balances[acc], 2)
        })
        
    # 2. Rapid successive transactions (Velocity spike) - 15 sets of 4 transactions
    velocity_accounts = random.sample(active_accounts, 15)
    for acc in velocity_accounts:
        base_dt = start_date + timedelta(days=random.randint(20, 340))
        for j in range(4):
            tx_dt = base_dt + timedelta(minutes=j * random.randint(1, 3))
            amount = round(random.uniform(400, 950), 2)
            balances[acc] -= amount
            
            transactions.append({
                "Transaction_ID": f"TXN{len(transactions)+1:06d}",
                "Account_Number": acc,
                "Date": tx_dt.strftime("%Y-%m-%d"),
                "Time": tx_dt.strftime("%H:%M:%S"),
                "Amount": amount,
                "Transaction_Type": "Debit",
                "Category": "Shopping",
                "Merchant_Name": "ELECTRONICS_ONLINE_STORE",
                "Account_Balance": round(balances[acc], 2)
            })

    # Sort final transactions chronologically to build a realistic ledger
    df_tx = pd.DataFrame(transactions)
    df_tx["DateTime"] = pd.to_datetime(df_tx["Date"] + " " + df_tx["Time"])
    df_tx = df_tx.sort_values("DateTime").drop(columns=["DateTime"])
    
    # Recalculate transaction balance ledger from starting balances to be mathematically consistent
    acc_start_balances = df_accounts.set_index("Account_Number")["Balance"].to_dict()
    running_balances = acc_start_balances.copy()
    
    correct_ledger_balances = []
    for idx, row in df_tx.iterrows():
        acc = row["Account_Number"]
        amt = row["Amount"]
        t_type = row["Transaction_Type"]
        
        if t_type == "Debit":
            running_balances[acc] -= amt
        else:
            running_balances[acc] += amt
            
        correct_ledger_balances.append(round(running_balances[acc], 2))
        
    df_tx["Account_Balance"] = correct_ledger_balances
    
    # Update the final account balances in df_accounts to reflect correct state
    for acc in running_balances:
        df_accounts.loc[df_accounts["Account_Number"] == acc, "Balance"] = running_balances[acc]

    return df_customers, df_accounts, df_tx

def main():
    print("Starting synthetic data generation...")
    df_customers, df_accounts = generate_customers_and_accounts()
    df_customers, df_accounts, df_transactions = generate_transactions(df_customers, df_accounts)
    
    # Export datasets
    df_customers.to_csv("customers.csv", index=False)
    df_accounts.to_csv("accounts.csv", index=False)
    df_transactions.to_csv("raw_transactions.csv", index=False)
    
    print(f"Data generation complete!")
    print(f"Generated {len(df_customers)} customers.")
    print(f"Generated {len(df_accounts)} accounts.")
    print(f"Generated {len(df_transactions)} transactions.")

if __name__ == "__main__":
    main()
