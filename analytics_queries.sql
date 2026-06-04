-- Retail Banking Intelligence System (RBIS) Analytics Queries

-- ==========================================
-- QUERY 1: Monthly Spending Per Customer
-- Calculates the total debit spending for each customer by month.
-- Real-world relevance: Used for monthly budgeting and credit capacity checks.
-- ==========================================
WITH CustomerMonthlySpend AS (
    SELECT 
        c.Customer_ID,
        c.Name,
        t.Transaction_Month,
        SUM(t.Amount) AS Total_Spend,
        COUNT(t.Transaction_ID) AS Transaction_Count
    FROM customers c
    JOIN accounts a ON c.Customer_ID = a.Customer_ID
    JOIN transactions t ON a.Account_Number = t.Account_Number
    WHERE t.Transaction_Type = 'Debit'
    GROUP BY c.Customer_ID, c.Name, t.Transaction_Month
)
SELECT 
    Customer_ID,
    Name,
    Transaction_Month,
    ROUND(Total_Spend, 2) AS Total_Spend,
    Transaction_Count
FROM CustomerMonthlySpend
ORDER BY Customer_ID, Transaction_Month;


-- ==========================================
-- QUERY 2: Top 10 High-Value Customers (DENSE_RANK)
-- Ranks customers by their total debit spend using the DENSE_RANK() window function.
-- Real-world relevance: Targeting for premium banking products (wealth management).
-- ==========================================
WITH CustomerTotalSpend AS (
    SELECT 
        c.Customer_ID,
        c.Name,
        c.Segment,
        c.Income,
        SUM(t.Amount) AS Total_Debit_Spend
    FROM customers c
    JOIN accounts a ON c.Customer_ID = a.Customer_ID
    JOIN transactions t ON a.Account_Number = t.Account_Number
    WHERE t.Transaction_Type = 'Debit'
    GROUP BY c.Customer_ID, c.Name, c.Segment, c.Income
),
RankedCustomers AS (
    SELECT 
        Customer_ID,
        Name,
        Segment,
        Income,
        ROUND(Total_Debit_Spend, 2) AS Total_Debit_Spend,
        DENSE_RANK() OVER (ORDER BY Total_Debit_Spend DESC) as Spend_Rank
    FROM CustomerTotalSpend
)
SELECT 
    Spend_Rank,
    Customer_ID,
    Name,
    Segment,
    Income,
    Total_Debit_Spend
FROM RankedCustomers
WHERE Spend_Rank <= 10
ORDER BY Spend_Rank;


-- ==========================================
-- QUERY 3: Category-Wise Spending Breakdown
-- Breaks down debit transactions by category and calculates the percentage contribution.
-- Real-world relevance: Customer behavior profiling and merchant partnership offers.
-- ==========================================
WITH TotalDebitSpending AS (
    SELECT SUM(Amount) AS Grand_Total FROM transactions WHERE Transaction_Type = 'Debit'
),
CategorySpending AS (
    SELECT 
        Category,
        SUM(Amount) AS Category_Total,
        COUNT(Transaction_ID) AS Category_Tx_Count
    FROM transactions
    WHERE Transaction_Type = 'Debit'
    GROUP BY Category
)
SELECT 
    cs.Category,
    ROUND(cs.Category_Total, 2) AS Category_Total,
    cs.Category_Tx_Count,
    ROUND((cs.Category_Total / tds.Grand_Total) * 100, 2) AS Spend_Percentage
FROM CategorySpending cs
CROSS JOIN TotalDebitSpending tds
ORDER BY Category_Total DESC;


-- ==========================================
-- QUERY 4: Dormant Customers (60+ Days Inactivity)
-- Finds customers whose accounts have had zero transactions in the last 60 days.
-- Assumes the database benchmark date is the latest transaction date.
-- Real-world relevance: Customer churn prevention campaigns.
-- ==========================================
WITH LatestSystemDate AS (
    SELECT MAX(Date) AS Last_Tx_Date FROM transactions
),
CustomerLastActivity AS (
    SELECT 
        c.Customer_ID,
        c.Name,
        c.Segment,
        MAX(t.Date) AS Last_Active_Date
    FROM customers c
    LEFT JOIN accounts a ON c.Customer_ID = a.Customer_ID
    LEFT JOIN transactions t ON a.Account_Number = t.Account_Number
    GROUP BY c.Customer_ID, c.Name, c.Segment
)
SELECT 
    cla.Customer_ID,
    cla.Name,
    cla.Segment,
    cla.Last_Active_Date,
    CAST((JULIANDAY(lsd.Last_Tx_Date) - JULIANDAY(cla.Last_Active_Date)) AS INTEGER) AS Days_Of_Inactivity
FROM CustomerLastActivity cla
CROSS JOIN LatestSystemDate lsd
WHERE Days_Of_Inactivity >= 60 OR cla.Last_Active_Date IS NULL
ORDER BY Days_Of_Inactivity DESC;


-- ==========================================
-- QUERY 5: Peak Transaction Hours
-- Identifies peak transaction hours to analyze system load and server capacity.
-- Real-world relevance: IT infrastructure scaling and maintenance window planning.
-- ==========================================
SELECT 
    Transaction_Hour,
    COUNT(Transaction_ID) AS Transaction_Count,
    ROUND(SUM(Amount), 2) AS Total_Volume,
    ROUND(AVG(Amount), 2) AS Average_Tx_Size
FROM transactions
GROUP BY Transaction_Hour
ORDER BY Transaction_Count DESC;


-- ==========================================
-- QUERY 6: Risk-Heavy Accounts
-- Identifies accounts with high transaction frequencies (velocity) or multiple high-value transactions.
-- Real-world relevance: Anti-Money Laundering (AML) and high-risk compliance flagging.
-- ==========================================
SELECT 
    a.Account_Number,
    c.Customer_ID,
    c.Name,
    c.Segment,
    COUNT(CASE WHEN t.is_high_value = 1 THEN 1 END) AS High_Value_Tx_Count,
    ROUND(SUM(CASE WHEN t.is_high_value = 1 THEN t.Amount ELSE 0 END), 2) AS High_Value_Spend,
    ROUND(a.Balance, 2) AS Current_Balance
FROM accounts a
JOIN customers c ON a.Customer_ID = c.Customer_ID
JOIN transactions t ON a.Account_Number = t.Account_Number
GROUP BY a.Account_Number, c.Customer_ID, c.Name, c.Segment
HAVING High_Value_Tx_Count > 0
ORDER BY High_Value_Tx_Count DESC, High_Value_Spend DESC;
