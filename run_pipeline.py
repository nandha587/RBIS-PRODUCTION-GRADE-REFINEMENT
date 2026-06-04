import subprocess
import os
import sys
import sqlite3
import pandas as pd
import time

def log_header(message):
    print("\n" + "="*70)
    print(f">>> {message.upper()}")
    print("="*70)

def run_script(script_name):
    print(f"Executing: python {script_name}...")
    start_time = time.time()
    # Execute the python script in the current environment
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(result.stdout)
        print(f"[OK] {script_name} completed in {duration:.2f} seconds.")
    else:
        print(f"[ERROR] Error executing {script_name}:")
        print(result.stderr)
        sys.exit(result.returncode)

def execute_sql_analytics(db_path="banking.db", sql_file="analytics_queries.sql"):
    log_header("Executing Advanced SQL Analytics Queries")
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} does not exist.")
        sys.exit(1)
    if not os.path.exists(sql_file):
        print(f"Error: SQL query file {sql_file} does not exist.")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    
    with open(sql_file, "r") as f:
        sql_content = f.read()
        
    # Split queries by double-dash comments containing QUERY
    # We will split queries by double semicolons or parse based on the comments
    queries_raw = sql_content.split(";")
    
    query_count = 1
    for query in queries_raw:
        query_stripped = query.strip()
        if not query_stripped:
            continue
            
        # Extract query description from comments
        lines = query_stripped.split("\n")
        comments = [l.replace("--", "").strip() for l in lines if l.strip().startswith("--")]
        query_clean = "\n".join([l for l in lines if not l.strip().startswith("--")])
        
        if not query_clean.strip():
            continue
            
        query_title = f"Query {query_count}"
        for comment in comments:
            if "QUERY" in comment:
                query_title = comment
                break
                
        print(f"\n[RUN] Running: {query_title}")
        print("-" * 50)
        
        try:
            df_res = pd.read_sql(query_clean, conn)
            # Display results (limit rows to 10 for terminal printing, but run full)
            if len(df_res) > 0:
                print(df_res.head(10).to_string(index=False))
                if len(df_res) > 10:
                    print(f"... and {len(df_res) - 10} more rows.")
            else:
                print("Empty Result Set")
        except Exception as e:
            print(f"Execution Error: {e}")
            
        query_count += 1
        
    conn.close()
    print("\n[OK] SQL Analytics complete.")

def main():
    overall_start = time.time()
    print("="*80)
    print("          RETAIL BANKING INTELLIGENCE SYSTEM PIPELINE RUNNER")
    print("="*80)
    
    # Step 1: Data Generation
    log_header("Step 1: Synthetic Data Generation")
    run_script("generate_data.py")
    
    # Step 2: ETL Pipeline & Database Ingestion
    log_header("Step 2: Clean, Feature Engineer & Ingest Data (ETL)")
    run_script("etl_pipeline.py")
    
    # Step 3: SQL Analytics Queries execution
    execute_sql_analytics()
    
    # Step 4: Run Machine Learning Segmentation and Fraud Risk Engines
    log_header("Step 4: Customer RFM Segmentation & Isolation Forest Fraud Engine")
    run_script("analytics_risk_engine.py")
    
    # Step 5: Generate Daily Operations PDF Report
    log_header("Step 5: Daily Risk & Performance Report Compilation")
    run_script("automation_reporter.py")
    
    overall_duration = time.time() - overall_start
    print("\n" + "="*80)
    print(f"PIPELINE RUN COMPLETED SUCCESSFULLY in {overall_duration:.2f} seconds!")
    print(f"Generated Database: {os.path.abspath('banking.db')}")
    print(f"Generated Executive PDF Report: {os.path.abspath('daily_risk_report.pdf')}")
    print("Launch the Web Portal with: streamlit run app.py")
    print("="*80)

if __name__ == "__main__":
    main()
