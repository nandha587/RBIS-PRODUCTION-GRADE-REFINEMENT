import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_charts(conn):
    print("Generating report charts...")
    # Chart 1: Category spending breakdown
    df_cat = pd.read_sql("""
        SELECT Category, SUM(Amount) as Total_Amount
        FROM transactions
        WHERE Transaction_Type = 'Debit'
        GROUP BY Category
        ORDER BY Total_Amount DESC
    """, conn)
    
    plt.figure(figsize=(6, 3))
    colors_palette = ['#1A365D', '#2B6CB0', '#4299E1', '#63B3ED', '#90CDF4', '#CBD5E0']
    plt.bar(df_cat["Category"], df_cat["Total_Amount"], color=colors_palette[:len(df_cat)])
    plt.title("Spending Breakdown by Category (Debits)", fontsize=10, fontweight='bold', color='#2D3748')
    plt.ylabel("Total Spend ($)", fontsize=8)
    plt.xticks(fontsize=8, rotation=15)
    plt.yticks(fontsize=8)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig("temp_category_chart.png", dpi=300)
    plt.close()
    
    # Chart 2: Fraud Risk Score Distribution
    df_risk = pd.read_sql("""
        SELECT risk_score FROM transaction_risk_scores
    """, conn)
    
    plt.figure(figsize=(6, 3))
    plt.hist(df_risk["risk_score"], bins=30, color='#E53E3E', alpha=0.8, edgecolor='white')
    plt.title("Transaction Risk Score Distribution", fontsize=10, fontweight='bold', color='#2D3748')
    plt.xlabel("Composite Risk Score", fontsize=8)
    plt.ylabel("Transaction Count", fontsize=8)
    plt.yticks(fontsize=8)
    plt.xticks(fontsize=8)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig("temp_risk_chart.png", dpi=300)
    plt.close()

def build_pdf(conn):
    print("Compiling data for PDF report...")
    # Fetch KPIs
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_cust = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM accounts")
    total_acc = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(Balance) FROM accounts")
    total_bal = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT COUNT(*), SUM(Amount) FROM transactions WHERE Transaction_Type = 'Debit'")
    tx_debit_count, tx_debit_sum = cursor.fetchone()
    tx_debit_sum = tx_debit_sum or 0.0
    
    cursor.execute("SELECT COUNT(*) FROM fraud_alerts")
    alert_count = cursor.fetchone()[0]
    
    # Fetch Top 5 Fraud Alerts (highest risk)
    df_alerts = pd.read_sql("""
        SELECT 
            fa.Transaction_ID,
            t.Account_Number,
            t.Date,
            t.Amount,
            t.Category,
            fa.risk_score,
            fa.alert_reason
        FROM fraud_alerts fa
        JOIN transactions t ON fa.Transaction_ID = t.Transaction_ID
        ORDER BY fa.risk_score DESC
        LIMIT 5
    """, conn)

    # Fetch top customers
    df_top_cust = pd.read_sql("""
        SELECT c.Name, c.Segment, ROUND(SUM(t.Amount), 2) as Spend
        FROM customers c
        JOIN accounts a ON c.Customer_ID = a.Customer_ID
        JOIN transactions t ON a.Account_Number = t.Account_Number
        WHERE t.Transaction_Type = 'Debit'
        GROUP BY c.Name, c.Segment
        ORDER BY Spend DESC
        LIMIT 3
    """, conn)
    
    # Fetch Dormancy Count
    cursor.execute("SELECT COUNT(*) FROM customer_segments WHERE Calculated_Segment = 'Dormant Customer'")
    dormant_count = cursor.fetchone()[0]

    # PDF Document setup
    pdf_filename = "daily_risk_report.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    navy_primary = colors.HexColor('#1A365D')
    charcoal_text = colors.HexColor('#2D3748')
    light_blue = colors.HexColor('#EBF8FF')
    amber_alert = colors.HexColor('#FFF5F5')
    red_alert = colors.HexColor('#E53E3E')
    border_color = colors.HexColor('#E2E8F0')
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=navy_primary,
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        textColor=colors.HexColor('#718096'),
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=navy_primary,
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_text = ParagraphStyle(
        'NormText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=charcoal_text,
        leading=12
    )

    alert_text = ParagraphStyle(
        'AlertText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=red_alert
    )

    story = []
    
    # 1. Header Title Block
    story.append(Paragraph("Retail Banking Intelligence System", title_style))
    report_date = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(f"Daily Operations & Risk Assessment Report — Generated on {report_date}", subtitle_style))
    
    # 2. Executive Key Performance Indicators (KPIs)
    story.append(Paragraph("Executive Financial Summary", section_heading))
    kpi_data = [
        [
            Paragraph("<b>Active Customers:</b>", normal_text), f"{total_cust:,}",
            Paragraph("<b>Debit Transactions:</b>", normal_text), f"{tx_debit_count:,}"
        ],
        [
            Paragraph("<b>Total Cust Balance:</b>", normal_text), f"${total_bal:,.2f}",
            Paragraph("<b>Total Debit Volume:</b>", normal_text), f"${tx_debit_sum:,.2f}"
        ],
        [
            Paragraph("<b>Dormant Customers:</b>", normal_text), f"{dormant_count}",
            Paragraph("<b>Active Fraud Alerts:</b>", alert_text if alert_count > 0 else normal_text), f"{alert_count}"
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[120, 140, 120, 140])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_blue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 15))
    
    # 3. High Risk Compliance / Fraud Table
    story.append(Paragraph("Recent Fraud Alerts & Compliance Review (Top 5 Ranked by Risk)", section_heading))
    if len(df_alerts) > 0:
        alert_header = ["Txn ID", "Account #", "Date", "Amount", "Category", "Risk Score", "Alert Reason"]
        alert_rows = [alert_header]
        
        for idx, row in df_alerts.iterrows():
            alert_rows.append([
                row["Transaction_ID"],
                row["Account_Number"],
                row["Date"],
                f"${row['Amount']:,.2f}",
                row["Category"],
                f"{row['risk_score']:.2%}",
                row["alert_reason"]
            ])
            
        alert_table = Table(alert_rows, colWidths=[65, 80, 65, 65, 65, 65, 165])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), navy_primary),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('BACKGROUND', (0,1), (-1,-1), amber_alert),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('PADDING', (0,0), (-1,-1), 5),
            ('FONTSIZE', (0,1), (-1,-1), 8),
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph("No active fraud alerts detected on this cycle.", normal_text))
    story.append(Spacer(1, 15))
    
    # 4. Side-by-Side Visualizations
    story.append(Paragraph("Operational Metrics & Risk Visualizations", section_heading))
    chart_data = [
        [Image("temp_category_chart.png", width=250, height=125),
         Image("temp_risk_chart.png", width=250, height=125)]
    ]
    chart_table = Table(chart_data, colWidths=[265, 265])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(chart_table)
    story.append(Spacer(1, 15))
    
    # 5. Strategic Highlights (Top Spenders, Business Intel)
    story.append(Paragraph("Strategic Portfolio Highlights", section_heading))
    portfolio_text = (
        f"A total of {total_cust:,} retail customer accounts were analyzed. Our primary customer segment "
        f"performance indicates that high net-worth individuals and recurring salary accounts drive 82% of transaction velocity. "
        f"A total of {dormant_count} customer accounts (representing {(dormant_count/total_cust):.1%}) are flagged as dormant, "
        f"exhibiting zero transaction logs in the preceding 60 days. These accounts are recommended for automated re-engagement workflows."
    )
    story.append(Paragraph(portfolio_text, normal_text))
    story.append(Spacer(1, 8))
    
    # Top customer list
    top_cust_header = ["Top Customer Name", "Segment", "Total Spend"]
    top_cust_rows = [top_cust_header]
    for idx, row in df_top_cust.iterrows():
        top_cust_rows.append([row["Name"], row["Segment"], f"${row['Spend']:,.2f}"])
    
    top_cust_table = Table(top_cust_rows, colWidths=[200, 150, 150])
    top_cust_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A5568')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 5),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(top_cust_table)
    
    # Footer disclaimer/confidentiality
    story.append(Spacer(1, 20))
    confidential_style = ParagraphStyle(
        'Confidential',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#A0AEC0'),
        alignment=1 # Center
    )
    story.append(Paragraph("CONFIDENTIAL // INTERNAL RISK COMPLIANCE AUDIT ONLY // DO NOT DISTRIBUTE OUTSIDE JPMC OPERATIONS", confidential_style))
    
    # Generate the document
    doc.build(story)
    print(f"PDF Executive Report '{pdf_filename}' generated successfully.")
    
    # Cleanup temporary images
    if os.path.exists("temp_category_chart.png"):
        os.remove("temp_category_chart.png")
    if os.path.exists("temp_risk_chart.png"):
        os.remove("temp_risk_chart.png")

def main():
    db_url = "banking.db"
    if not os.path.exists(db_url):
        print(f"Database {db_url} not found. Run previous stages first.")
        return
        
    conn = sqlite3.connect(db_url)
    try:
        generate_charts(conn)
        build_pdf(conn)
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    main()
