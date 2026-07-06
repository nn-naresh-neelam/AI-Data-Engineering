#!/usr/bin/env python3
import os
import csv
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Any

# Oracle client
try:
    import oracledb
    # Optional: provide client library path if needed
    # oracledb.init_oracle_client(lib_dir="/path/to/instantclient_19_8")
except Exception as e:
    raise SystemExit(f"Required library 'oracledb' is not available: {e}")

OUTPUT_DIR = "./Ouput/"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Environment-based DB connection
DB_USER = os.getenv("ORACLEUSERNAME")
DB_PWD = os.getenv("ORACLEPWD")
DB_DSN = os.getenv("ORACLEDSN")

if not (DB_USER and DB_PWD and DB_DSN):
    raise SystemExit("Please set ORACLEUSERNAME, ORACLEPWD, and ORACLEDSN environment variables.")

def connect_oracle():
    # Thin mode is common; adjust if you have full client
    conn = oracledb.connect(user=DB_USER, password=DB_PWD, dsn=DB_DSN, encoding="UTF-8")
    return conn

def fetch_all(cursor, query: str) -> List[Dict[str, Any]]:
    cursor.execute(query)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return [dict(zip(cols, row)) for row in rows]

def write_csv(file_path: str, rows: List[Dict[str, Any]]):
    if not rows:
        # Write header only if possible
        return
    cols = list(rows[0].keys())
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def build_email_body(section_results: Dict[str, List[Dict[str, Any]]]) -> str:
    lines = []
    lines.append("ADM Customers Reports")
    lines.append("="*80)
    for title, rows in section_results.items():
        lines.append(f"\n{title}\n")
        if not rows:
            lines.append("No data returned.")
            continue
        # Render a simple table-like section
        headers = list(rows[0].keys())
        lines.append(" | ".join(headers))
        lines.append("-" * (len(" | ".join(headers))))
        for row in rows:
            values = [str(row[h]) if row[h] is not None else "" for h in headers]
            lines.append(" | ".join(values))
    return "\n".join(lines)

def send_email(subject: str, body: str, to_emails: List[str]):
    # Optional: use env vars for SMTP config
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = os.getenv("SMTP_PORT", "25")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PWD = os.getenv("SMTP_PWD")

    if not SMTP_HOST:
        print("SMTP_HOST not set; skipping email sending. Email body prepared.")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USER or "noreply@example.com"
    msg['To'] = ", ".join(to_emails)
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as server:
            server.ehlo()
            server.starttls() if hasattr(server, 'starttls') else None
            if SMTP_USER and SMTP_PWD:
                server.login(SMTP_USER, SMTP_PWD)
            server.send_message(msg)
        print(f"Email sent to {to_emails} with subject: {subject}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    conn = connect_oracle()
    cur = conn.cursor()

    # 1) DFUN0001 Identify High-Value "Loyal" Customers
    sql_dfun0001 = """
    WITH customer_spending AS (
      SELECT o.CUSTOMER_ID,
             COUNT(*) AS order_count,
             SUM(oi.UNIT_PRICE * oi.QUANTITY) AS total_spent
      FROM ADM_ORDERS o
      JOIN ADM_ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
      GROUP BY o.CUSTOMER_ID
    ),
    average_spend AS (
      SELECT AVG(total_spent) AS avg_spent FROM customer_spending
    )
    SELECT c.CUSTOMER_ID, c.FULL_NAME, c.EMAIL_ADDRESS, cs.order_count, cs.total_spent, asg.avg_spent
    FROM customer_spending cs
    JOIN ADM_CUSTOMERS c ON cs.CUSTOMER_ID = c.CUSTOMER_ID
    CROSS JOIN average_spend asg
    WHERE cs.order_count >= 5 AND cs.total_spent > asg.avg_spent
    """
    result1 = fetch_all(cur, sql_dfun0001)
    write_csv(os.path.join(OUTPUT_DIR, "DFUN0001_high_value_loyal_customers.csv"), result1)

    # 2) DFUN0002 Top-Selling Product per Category
    # Assumes 'category' and 'total_sales' are accessible via the product_orders view.
    sql_dfun0002 = """
    WITH t AS (
      SELECT category, product_id, product_name, total_sales
      FROM product_orders
    )
    SELECT category, product_id, product_name, total_sales
    FROM (
      SELECT t.*,
             ROW_NUMBER() OVER (PARTITION BY category ORDER BY total_sales DESC) AS rn
      FROM t
    ) s
    WHERE rn = 1
    """
    result2 = fetch_all(cur, sql_dfun0002)
    write_csv(os.path.join(OUTPUT_DIR, "DFUN0002_top_selling_per_category.csv"), result2)

    # 3) DFUN0003 Detect Dormant Accounts (Zero Purchases)
    sql_dfun0003 = """
    WITH last_order AS (
      SELECT o.CUSTOMER_ID,
             MAX(o.ORDER_TMS) AS last_order_tms
      FROM ADM_ORDERS o
      GROUP BY o.CUSTOMER_ID
    )
    SELECT c.CUSTOMER_ID, c.FULL_NAME, c.EMAIL_ADDRESS
    FROM ADM_CUSTOMERS c
    LEFT JOIN last_order lo ON c.CUSTOMER_ID = lo.CUSTOMER_ID
    WHERE lo.last_order_tms IS NULL
       OR lo.last_order_tms < ADD_MONTHS(SYSDATE, -12)
    """
    result3 = fetch_all(cur, sql_dfun0003)
    write_csv(os.path.join(OUTPUT_DIR, "DFUN0003_dormant_accounts.csv"), result3)

    # 4) DFUN0004 Pinpoint Consecutive Sales Surges
    sql_dfun0004 = """
    WITH daily AS (
      SELECT o.CUSTOMER_ID,
             TRUNC(o.ORDER_TMS) AS order_date,
             SUM(oi.UNIT_PRICE * oi.QUANTITY) AS day_total
      FROM ADM_ORDERS o
      JOIN ADM_ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
      GROUP BY o.CUSTOMER_ID, TRUNC(o.ORDER_TMS)
    )
    SELECT d1.CUSTOMER_ID, d1.order_date
    FROM daily d1
    JOIN daily d2 ON d2.CUSTOMER_ID = d1.CUSTOMER_ID AND d2.order_date = d1.order_date + 1
    JOIN daily d3 ON d3.CUSTOMER_ID = d1.CUSTOMER_ID AND d3.order_date = d1.order_date + 2
    WHERE d1.day_total > 1000 AND d2.day_total > 1000 AND d3.day_total > 1000
    """
    # The query returns customer_id and a start date of the 3-day window
    result4 = fetch_all(cur, sql_dfun0004)
    write_csv(os.path.join(OUTPUT_DIR, "DFUN0004_consecutive_sales_surges.csv"), result4)

    # 5) DFUN0005 Moving Averages over Time (3-order rolling average)
    sql_dfun0005 = """
    WITH daily AS (
      SELECT o.CUSTOMER_ID,
             TRUNC(o.ORDER_TMS) AS order_date,
             SUM(oi.UNIT_PRICE * oi.QUANTITY) AS day_total
      FROM ADM_ORDERS o
      JOIN ADM_ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
      GROUP BY o.CUSTOMER_ID, TRUNC(o.ORDER_TMS)
    )
    SELECT customer_id, order_date, day_total,
           AVG(day_total) OVER (
             PARTITION BY customer_id
             ORDER BY order_date
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
           ) AS moving_avg_3
    FROM daily
    ORDER BY customer_id, order_date
    """
    result5 = fetch_all(cur, sql_dfun0005)
    write_csv(os.path.join(OUTPUT_DIR, "DFUN0005_moving_averages.csv"), result5)

    # Consolidated functional email body
    section_results = {
        "1. Identify High-Value Loyal Customers": result1,
        "2. Top-Selling Product per Category": result2,
        "3. Dormant Accounts (Zero Purchases)": result3,
        "4. Consecutive Sales Surges (>=1000 on 3 consecutive days)": result4,
        "5. 3-Order Moving Averages by Customer": result5,
    }
    email_body = build_email_body(section_results)

    # Optional: Send functional email (subject as per NFUN0001)
    recipients = [os.getenv("RECIPIENT_EMAIL", "naresh_neelam@outlook.com")]
    send_email("ADM Customers Reports", email_body, recipients)

    # Technical email scaffold (optional)
    # You can build a separate technical body if needed and send to another address
    technical_subject = "ADM CUSTOMER DATA – REPORTING BRD"
    technical_body = "Technical mapping of BRD to Schema completed. See attached outputs in ./Ouput/."
    technical_recipients = [os.getenv("TECHNICAL_RECIPIENT_EMAIL", "tech@example.com")]
    # Uncomment to enable, if SMTP is configured
    # send_email(technical_subject, technical_body, technical_recipients)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()