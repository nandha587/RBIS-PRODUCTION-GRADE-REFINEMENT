-- Retail Banking Intelligence System Schema Definition

-- Drop tables if they exist (ensures clean rebuild)
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS customers;

-- 1. Customers Table
CREATE TABLE customers (
    Customer_ID VARCHAR(50) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Income INTEGER NOT NULL,
    Segment VARCHAR(50) NOT NULL,
    Join_Date DATE NOT NULL,
    State VARCHAR(2) NOT NULL
);

-- 2. Accounts Table
CREATE TABLE accounts (
    Account_Number VARCHAR(50) PRIMARY KEY,
    Customer_ID VARCHAR(50) NOT NULL,
    Account_Type VARCHAR(50) NOT NULL,
    Balance REAL NOT NULL,
    FOREIGN KEY (Customer_ID) REFERENCES customers(Customer_ID) ON DELETE CASCADE
);

-- 3. Transactions Table
CREATE TABLE transactions (
    Transaction_ID VARCHAR(50) PRIMARY KEY,
    Account_Number VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Time TIME NOT NULL,
    Amount REAL NOT NULL,
    Transaction_Type VARCHAR(10) NOT NULL,
    Category VARCHAR(50) NOT NULL,
    Merchant_Name VARCHAR(100) NOT NULL,
    Account_Balance REAL NOT NULL,
    Transaction_Hour INTEGER NOT NULL,
    Transaction_Month VARCHAR(7) NOT NULL,
    is_high_value INTEGER NOT NULL,
    is_essential INTEGER NOT NULL,
    is_leisure INTEGER NOT NULL,
    is_cash_out INTEGER NOT NULL,
    FOREIGN KEY (Account_Number) REFERENCES accounts(Account_Number) ON DELETE CASCADE
);

-- Indexing Strategy for Optimized Joins and Query Performance
CREATE INDEX idx_customers_segment ON customers(Segment);
CREATE INDEX idx_accounts_customer ON accounts(Customer_ID);
CREATE INDEX idx_transactions_account ON transactions(Account_Number);
CREATE INDEX idx_transactions_date ON transactions(Date);
CREATE INDEX idx_transactions_category ON transactions(Category);
CREATE INDEX idx_transactions_hour ON transactions(Transaction_Hour);
CREATE INDEX idx_transactions_composite ON transactions(Account_Number, Date, Amount);
