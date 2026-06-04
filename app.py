import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Set page config for a premium wide-screen experience
st.set_page_config(
    page_title="Retail Banking Intelligence Platform (RBIS)",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS to inject modern typography, glassmorphism, and curated colors
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #2D3748;
    }
    
    .stApp {
        background-color: #F7FAFC;
    }
    
    /* Executive KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, #1A365D 0%, #2A4365 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(26, 54, 93, 0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
    }
    .kpi-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Risk / Alert KPI Card */
    .kpi-card-alert {
        background: linear-gradient(135deg, #9B2C2C 0%, #C53030 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(155, 44, 44, 0.15);
        text-align: center;
    }
    
    /* Table Headers */
    .styled-table th {
        background-color: #1A365D !important;
        color: white !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1A365D;
        color: white;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] span {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to get database connection
def get_db_connection():
    db_path = "banking.db"
    if not os.path.exists(db_path):
        st.error("Database connection failed. Please ensure the pipeline runs first by executing run_pipeline.py.")
        return None
    return sqlite3.connect(db_path)

conn = get_db_connection()

if conn:
    # --- DATA CACHING & FETCHING ---
    @st.cache_data
    def load_cached_data():
        # Fetch dataframes for caching
        df_c = pd.read_sql("SELECT * FROM customers", conn)
        df_a = pd.read_sql("SELECT * FROM accounts", conn)
        df_t = pd.read_sql("SELECT * FROM transactions", conn)
        df_s = pd.read_sql("SELECT * FROM customer_segments", conn)
        
        # Merge risk score metrics directly onto transaction if available
        try:
            df_r = pd.read_sql("SELECT * FROM transaction_risk_scores", conn)
            df_t_merged = df_t.merge(df_r, on="Transaction_ID", how="left")
        except Exception:
            # Fallback if risk scores table doesn't exist yet
            df_t_merged = df_t.copy()
            df_t_merged["risk_score"] = 0.0
            df_t_merged["fraud_flag"] = 0
            df_t_merged["alert_reason"] = "Normal"
            
        return df_c, df_a, df_t_merged, df_s

    df_customers, df_accounts, df_transactions, df_segments = load_cached_data()
    
    # Pre-process columns
    df_transactions["Date"] = pd.to_datetime(df_transactions["Date"])
    min_date = df_transactions["Date"].min().to_pydatetime()
    max_date = df_transactions["Date"].max().to_pydatetime()

    # --- SIDEBAR FILTERS ---
    st.sidebar.image("https://img.icons8.com/color/96/bank.png", width=60)
    st.sidebar.title("JPMC RBIS Platform")
    st.sidebar.markdown("*Retail Banking Intelligence & Risk Analytics Suite*")
    st.sidebar.divider()
    
    # Filter: Date range
    st.sidebar.subheader("Global Time Filter")
    date_range = st.sidebar.date_input(
        "Select Transaction Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Parse date range filters
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)
        
    df_t_filtered = df_transactions[(df_transactions["Date"] >= start_date) & (df_transactions["Date"] <= end_date)]

    # Filter: Customer Segments
    st.sidebar.subheader("Portfolio Filter")
    all_segments = ["All Segments"] + list(df_segments["Calculated_Segment"].unique())
    selected_segment = st.sidebar.selectbox("Customer Segment", all_segments)
    
    if selected_segment != "All Segments":
        # Map accounts to selected customer segment
        cust_in_seg = df_segments[df_segments["Calculated_Segment"] == selected_segment]["Customer_ID"]
        acc_in_seg = df_accounts[df_accounts["Customer_ID"].isin(cust_in_seg)]["Account_Number"]
        df_t_filtered = df_t_filtered[df_t_filtered["Account_Number"].isin(acc_in_seg)]
        df_c_filtered = df_customers[df_customers["Customer_ID"].isin(cust_in_seg)]
    else:
        df_c_filtered = df_customers.copy()

    st.sidebar.divider()
    st.sidebar.info("Operational Status: ONLINE\n\nDatabase: SQLite (banking.db)\nScale Target: AWS Aurora PostgreSQL")

    # --- MAIN PAGE TABS ---
    title_col, badge_col = st.columns([8, 2])
    with title_col:
        st.title("🏦 Retail Banking Intelligence Dashboard")
        st.markdown("Global Operations and Compliance Surveillance Hub")
    with badge_col:
        st.markdown("<br><span style='background-color:#EBF8FF; color:#2B6CB0; padding:6px 12px; border-radius:15px; font-weight:bold; font-size:0.75rem; border:1.5px solid #bee3f8;'>JPMC INTERNAL ONLY</span>", unsafe_allow_html=True)
        
    tab_overview, tab_cust, tab_spend, tab_risk = st.tabs([
        "📊 Executive Overview", 
        "👥 Customer RFM Intelligence", 
        "💸 Spending & Revenue Analysis", 
        "🚨 Risk & Fraud Survelliance"
    ])

    # ==========================================
    # TAB 1: EXECUTIVE OVERVIEW
    # ==========================================
    with tab_overview:
        st.subheader("Key Portfolio Indicators")
        
        # Calculate aggregate stats
        active_customers = len(df_c_filtered)
        total_balance = df_accounts[df_accounts["Customer_ID"].isin(df_c_filtered["Customer_ID"])]["Balance"].sum()
        total_tx_vol = df_t_filtered["Amount"].sum()
        total_tx_count = len(df_t_filtered)
        
        # Count risk flags
        fraud_count = df_t_filtered[df_t_filtered["fraud_flag"] == 1]["Transaction_ID"].nunique()
        avg_risk_score = df_t_filtered[df_t_filtered["Transaction_Type"] == 'Debit']["risk_score"].mean() or 0.0
        
        # KPI Card Grid
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Active Core Customers</div>
                <div class="kpi-value">{active_customers:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Customer Deposits</div>
                <div class="kpi-value">${total_balance:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Transaction Spend Vol</div>
                <div class="kpi-value">${total_tx_vol:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            if fraud_count > 0:
                st.markdown(f"""
                <div class="kpi-card-alert">
                    <div class="kpi-title">Active Fraud Alerts</div>
                    <div class="kpi-value">{fraud_count}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Active Fraud Alerts</div>
                    <div class="kpi-value">0</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.divider()
        
        # Layout splits
        left_col, right_col = st.columns([6, 4])
        with left_col:
            st.subheader("Transaction Volume & Trends")
            # Aggregated monthly transaction values
            df_monthly_trend = df_t_filtered.groupby(["Transaction_Month", "Transaction_Type"])["Amount"].sum().reset_index()
            fig_trend = px.line(
                df_monthly_trend, 
                x="Transaction_Month", 
                y="Amount", 
                color="Transaction_Type",
                title="Monthly Credit / Debit Volume Trends",
                color_discrete_map={"Debit": "#E53E3E", "Credit": "#319795"},
                markers=True
            )
            fig_trend.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Billing Cycle (Month)",
                yaxis_title="Volume ($)"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with right_col:
            st.subheader("Customer Demographics By State")
            df_state_counts = df_c_filtered.groupby("State")["Customer_ID"].count().reset_index()
            df_state_counts.columns = ["State", "Customer Count"]
            df_state_counts = df_state_counts.sort_values("Customer Count", ascending=False)
            
            fig_bar = px.bar(
                df_state_counts, 
                x="State", 
                y="Customer Count", 
                title="Geographic Portfolio Distribution",
                color="Customer Count",
                color_continuous_scale=px.colors.sequential.Blues
            )
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

    # ==========================================
    # TAB 2: CUSTOMER RFM INTELLIGENCE
    # ==========================================
    with tab_cust:
        st.subheader("Customer Behavioral Segmentation (RFM Logic)")
        
        col_pie, col_details = st.columns([4, 6])
        
        with col_pie:
            # Segment Pie Chart
            df_seg_counts = df_segments.groupby("Calculated_Segment")["Customer_ID"].count().reset_index()
            df_seg_counts.columns = ["Segment", "Count"]
            
            fig_pie = px.pie(
                df_seg_counts, 
                values="Count", 
                names="Segment", 
                title="Segmentation Share",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_details:
            # Dynamic Filtered Customer table
            st.subheader("Portfolio Customer Directory")
            search_query = st.text_input("Search Customer Directory by Name:")
            
            # Filter customers by directory
            df_dir = df_customers.merge(df_segments, on="Customer_ID")
            if search_query:
                df_dir = df_dir[df_dir["Name"].str.contains(search_query, case=False)]
            
            # Select specific segments to view
            segment_select = st.multiselect("Filter by Segments:", list(df_segments["Calculated_Segment"].unique()))
            if segment_select:
                df_dir = df_dir[df_dir["Calculated_Segment"].isin(segment_select)]
                
            st.dataframe(
                df_dir[["Customer_ID", "Name", "Income", "Segment", "Total_Balance", "Total_Spend", "Calculated_Segment"]],
                use_container_width=True,
                height=300
            )

        st.divider()
        st.subheader("Deep-Dive Individual Customer Ledger")
        
        selected_cust_name = st.selectbox("Select Customer to Inspect:", sorted(df_customers["Name"].unique()))
        if selected_cust_name:
            cust_row = df_customers[df_customers["Name"] == selected_cust_name].iloc[0]
            cust_id = cust_row["Customer_ID"]
            
            # Get customer details
            c_seg_row = df_segments[df_segments["Customer_ID"] == cust_id].iloc[0]
            c_accounts = df_accounts[df_accounts["Customer_ID"] == cust_id]
            c_acc_numbers = c_accounts["Account_Number"].tolist()
            c_tx = df_transactions[df_transactions["Account_Number"].isin(c_acc_numbers)]
            
            # Display Details
            dcol1, dcol2, dcol3, dcol4 = st.columns(4)
            dcol1.metric("Customer ID", cust_id)
            dcol2.metric("Reported Segment", cust_row["Segment"])
            dcol3.metric("Annual Income", f"${cust_row['Income']:,}")
            dcol4.metric("Calculated Category", c_seg_row["Calculated_Segment"])
            
            # Display accounts table
            st.write("**Registered Accounts:**")
            st.dataframe(c_accounts[["Account_Number", "Account_Type", "Balance"]], use_container_width=True)
            
            # Display transaction history
            st.write(f"**Transaction Audit Trail ({len(c_tx)} Records):**")
            st.dataframe(
                c_tx[["Transaction_ID", "Account_Number", "Date", "Amount", "Transaction_Type", "Category", "Merchant_Name", "risk_score", "fraud_flag"]].sort_values("Date", ascending=False),
                use_container_width=True
            )

    # ==========================================
    # TAB 3: SPENDING & REVENUE ANALYSIS
    # ==========================================
    with tab_spend:
        st.subheader("Customer Expenditure Breakdown")
        
        scol1, scol2 = st.columns([5, 5])
        with scol1:
            # Category-wise spend
            df_cat_spend = df_t_filtered[df_t_filtered["Transaction_Type"] == 'Debit'].groupby("Category")["Amount"].sum().reset_index()
            fig_cat = px.pie(
                df_cat_spend, 
                values="Amount", 
                names="Category", 
                title="Debit Spending by Category",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with scol2:
            # Hourly distribution of spending
            df_hour_spend = df_t_filtered.groupby("Transaction_Hour")["Amount"].agg(["count", "sum"]).reset_index()
            fig_hour = px.bar(
                df_hour_spend, 
                x="Transaction_Hour", 
                y="sum", 
                title="Hourly Spending Volume Distribution",
                labels={"sum": "Total Spend Volume ($)", "Transaction_Hour": "Hour of Day (24h)"},
                color="sum",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig_hour.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_hour, use_container_width=True)
            
        st.divider()
        st.subheader("Merchant Concentration")
        
        df_merchants = df_t_filtered[df_t_filtered["Transaction_Type"] == 'Debit'].groupby(["Category", "Merchant_Name"])["Amount"].agg(["sum", "count"]).reset_index()
        df_merchants = df_merchants.sort_values("sum", ascending=False).head(15)
        
        fig_merchants = px.bar(
            df_merchants,
            y="Merchant_Name",
            x="sum",
            color="Category",
            title="Top 15 Merchant Destinations by Spending",
            orientation='h',
            labels={"sum": "Total Transacted Amount ($)", "Merchant_Name": "Merchant"}
        )
        st.plotly_chart(fig_merchants, use_container_width=True)

    # ==========================================
    # TAB 4: RISK & FRAUD SURVEILLANCE
    # ==========================================
    with tab_risk:
        st.subheader("Security & Surveillance Command Center")
        
        # Risk thresholds filters
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            risk_threshold = st.slider("Surveillance Filter: Min Transaction Risk Score", min_value=0.0, max_value=1.0, value=0.50, step=0.05)
        with rcol2:
            flagged_only = st.checkbox("Show Compliance-Flagged (Fraud Flag = 1) Only", value=True)
            
        # Filter transactions
        df_risk_tx = df_transactions[df_transactions["Transaction_Type"] == 'Debit'].copy()
        if flagged_only:
            df_risk_tx = df_risk_tx[df_risk_tx["fraud_flag"] == 1]
        df_risk_tx = df_risk_tx[df_risk_tx["risk_score"] >= risk_threshold]
        
        # KPI widgets for risk
        rcol_a, rcol_b, rcol_c = st.columns(3)
        rcol_a.metric("Flagged System Alerts", len(df_risk_tx))
        rcol_b.metric("Total Risk Exposure Amount", f"${df_risk_tx['Amount'].sum():,.2f}")
        rcol_c.metric("Highest Logged Risk Score", f"{df_risk_tx['risk_score'].max() or 0.0:.2%}")
        
        st.write(f"**Surveillance Audit Ledger ({len(df_risk_tx)} Alerts Found):**")
        
        # Display styled warning alerts table
        st.dataframe(
            df_risk_tx[["Transaction_ID", "Account_Number", "Date", "Amount", "Category", "Merchant_Name", "risk_score", "fraud_flag", "alert_reason"]].sort_values("risk_score", ascending=False),
            use_container_width=True
        )
        
        st.divider()
        st.subheader("Isolation Forest Anomaly Isolation Map")
        
        # Select sample size for rendering map to prevent lagging
        df_map_sample = df_transactions[df_transactions["Transaction_Type"] == 'Debit'].copy()
        
        # Render a scatter plot showing Amount vs Hour, color-coded by Fraud/Risk Score
        fig_scatter = px.scatter(
            df_map_sample,
            x="Transaction_Hour",
            y="Amount",
            color="risk_score",
            size="Amount",
            hover_data=["Transaction_ID", "Merchant_Name", "Category", "alert_reason"],
            color_continuous_scale=px.colors.sequential.OrRd,
            title="High-Dimensional Risk Scatter Mapping (Amount vs. Hour)",
            labels={"risk_score": "Risk Score", "Transaction_Hour": "Transaction Hour (24h)"}
        )
        fig_scatter.update_layout(plot_bgcolor="#1A202C", paper_bgcolor="rgba(0,0,0,0)")
        fig_scatter.update_traces(marker=dict(line=dict(width=0.5, color='gray')))
        st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("Ensure the database connection is initialized. Run the pipeline script first.")
