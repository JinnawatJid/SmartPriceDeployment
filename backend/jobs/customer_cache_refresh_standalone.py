"""
Customer Cache Refresh Job - Standalone Version for Airflow
ดึงข้อมูล Customer และ Analytics จาก D365 มาลง database

This is a standalone version that doesn't require external imports.
All dependencies are included in this file.

Configuration:
--------------
The script uses hardcoded default values from production environment:
- CUSTOMER_API_URL: http://192.192.0.37:8280/customer/1.0.0
- CUSTOMER_API_KEY: (production key included)
- INVOICE_API_URL: http://192.192.0.37:8280/invoice-sp681/1.0.0
- INVOICE_API_KEY: (production key included)
- MSSQL_SERVER: 192.192.0.220,50681
- MSSQL_DATABASE: SP681
- MSSQL_USERNAME: sp681_user
- MSSQL_PASSWORD: (production password included)

You can override these defaults using environment variables.

Usage:
------
1. Direct execution:
   python customer_cache_refresh_standalone.py

2. In Airflow DAG:
   from customer_cache_refresh_standalone import run_customer_cache_refresh
   
   def task_function():
       result = run_customer_cache_refresh()
       if result.errors:
           raise Exception(f"Job failed with {len(result.errors)} errors")
       return result

Requirements:
-------------
- pyodbc
- requests
- pandas

Install with:
    pip install pyodbc requests pandas
"""

import os
import time
import logging
import pyodbc
import requests
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from logging.handlers import TimedRotatingFileHandler


# =========================
# LOGGING SETUP
# =========================

LOG_FILE = "logs/customer_cache_refresh.log"
LOG_LEVEL = "INFO"
LOG_BACKUP_COUNT = 30


def setup_logger():
    """Setup logger with file and console handlers"""
    logger = logging.getLogger('customer_cache')
    logger.setLevel(getattr(logging, LOG_LEVEL))
    logger.handlers.clear()
    
    # Create logs directory if not exists
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # File handler with daily rotation
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()


# =========================
# CONFIGURATION
# =========================

# Database Configuration
MSSQL_CONFIG = {
    "server": os.getenv("MSSQL_SERVER", "192.192.0.220,50681"),
    "database": os.getenv("MSSQL_DATABASE", "SP681"),
    "username": os.getenv("MSSQL_USERNAME", "sp681_user"),
    "password": os.getenv("MSSQL_PASSWORD", "Tng#kmitl2"),
    "driver": os.getenv("MSSQL_DRIVER", "{ODBC Driver 17 for SQL Server}"),
}

# API Configuration - Customer API
DEFAULT_CUSTOMER_API_URL = "http://192.192.0.37:8280/customer-silver/1.0.0"
DEFAULT_CUSTOMER_API_KEY = "eyJ4NXQjUzI1NiI6Ik16QXpNVEZqT0RRMU1ETmpPVFUxWkRBNE5HUTVNRGt6WXpFM01XSTRNbVJsWkdVM1l6WmpZams0WkdSa00yUmhNbUl3TWpBeFl6SmxNR0pqTmpkbU53PT0iLCJraWQiOiJnYXRld2F5X2NlcnRpZmljYXRlX2FsaWFzIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ==.eyJzdWIiOiJhZG1pbkBjYXJib24uc3VwZXIiLCJhcHBsaWNhdGlvbiI6eyJpZCI6MzQsInV1aWQiOiIzNTU5OGQ4NS1jM2VlLTQ3ODktOGViMC03MGM5YzEwNGJiMmYifSwiaXNzIjoiaHR0cHM6XC9cL2xvY2FsaG9zdDo5NDQzXC9vYXV0aDJcL3Rva2VuIiwia2V5dHlwZSI6IlBST0RVQ1RJT04iLCJ0b2tlbl90eXBlIjoiYXBpS2V5IiwiaWF0IjoxNzc0MjMyOTYyLCJqdGkiOiJkNTlhYTdiZC1hODNkLTQyMzItYTY3Mi0yMzQ2ODZhNWUwMDUifQ==.am4fKoaQhW-n1NMg2Rr29MyO4NjbOw3R1_M7RGQnOtgWt-ZMuC3pKXuVWgYCGVYngh2OiAXeVwFQ9GC4rToy_zdq0bXQ3kjey1_QSYi6H-PLl2DYRpxhaYRLqQF8DlIAHtFAGAa_PWTgqh2y2DoI_MUc6UwEcHOnYV59_y1BXWaeghyRa_Ziyaq-0HWwGoKZCJPuTlitXrdGMOara6noi2rGLn5bmI_xI9g-KGIEf47dWDLfubv-zfZPWZlnsAAjxSNSeOXrGkehvnOTJm-CuO84PGa6ID867arQb775mMtAEu4ci3K7Yj_1kUi67lz3rDLZSjHR9M_9pe3Bthqukg=="

# API Configuration - Invoice API
DEFAULT_INVOICE_API_URL = "http://192.192.0.37:8280/invoice-sp681/1.0.0"
DEFAULT_INVOICE_API_KEY = "eyJ4NXQjUzI1NiI6Ik16QXpNVEZqT0RRMU1ETmpPVFUxWkRBNE5HUTVNRGt6WXpFM01XSTRNbVJsWkdVM1l6WmpZams0WkdSa00yUmhNbUl3TWpBeFl6SmxNR0pqTmpkbU53PT0iLCJraWQiOiJnYXRld2F5X2NlcnRpZmljYXRlX2FsaWFzIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYifQ==.eyJzdWIiOiJkZXZVc2VyQGNhcmJvbi5zdXBlciIsImFwcGxpY2F0aW9uIjp7ImlkIjo2OSwidXVpZCI6ImNlODcxN2I0LTUwOTQtNDBlMy1hNzdjLWY2M2UyNWQwNWNjNSJ9LCJpc3MiOiJodHRwczpcL1wvbG9jYWxob3N0Ojk0NDNcL29hdXRoMlwvdG9rZW4iLCJrZXl0eXBlIjoiUFJPRFVDVElPTiIsInRva2VuX3R5cGUiOiJhcGlLZXkiLCJpYXQiOjE3NjkxNzcyMDIsImp0aSI6IjYyZjhlNWEzLWUxYjktNDYwMS1iMDk0LWIwYjNhM2I2YTU1YyJ9.gNjVXzh-q9ITNMybUmrdL8Vuvptxvm3zLUKX5DXqK98qzhfSmP2dwWGteviBQLGOOlmYws0zoqf0DLzlswcT08gYhQIzXNPHTMek47w127DWHdp97lcBFNEGDBlRVxuzRq_Y9_gkwugNI7vDhu41SE7nj0tEy15-iDmGH8RNrUZEp_tML8nCjTpBs0jPcar7dIbJxyP94O63pjdSN2GXW6TTMOCRlKUsMO5EiAjJKCzHFgvFabmFZNrk12jvmLXyh7QnqXCQF1o3UNmKS7--GS3qie2mpHWyaQxP1Qa6kNWdPbHlzIp27eA208Az6XAlq2s6iaXLdcvAfZKPWcbRGQ=="

# Job Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
API_PAGE_SIZE = int(os.getenv("API_PAGE_SIZE", "500"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))


def get_mssql_conn():
    """Create and return MSSQL database connection"""
    conn_str = (
        f"DRIVER={MSSQL_CONFIG['driver']};"
        f"SERVER={MSSQL_CONFIG['server']};"
        f"DATABASE={MSSQL_CONFIG['database']};"
        f"UID={MSSQL_CONFIG['username']};"
        f"PWD={MSSQL_CONFIG['password']};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


# =========================
# DATA MODELS
# =========================

@dataclass
class CustomerCacheRecord:
    customer_code: str
    customer_name: str
    phone: Optional[str] = ""
    tax_no: Optional[str] = ""
    gen_bus: Optional[str] = ""
    payment_terms: Optional[str] = ""
    customer_date: Optional[str] = ""
    blocked: Optional[str] = ""
    accum_6m: float = 0.0
    frequency: int = 0
    sales_g_cust: float = 0.0
    sales_a_cust: float = 0.0
    sales_s_cust: float = 0.0
    sales_y_cust: float = 0.0
    sales_c_cust: float = 0.0
    sales_e_cust: float = 0.0
    calculation_date: Optional[date] = None


@dataclass
class JobExecutionResult:
    start_time: datetime
    end_time: datetime
    calculation_date: date
    customers_processed: int = 0
    customers_updated: int = 0
    customers_failed: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def avg_time_per_customer(self) -> float:
        if self.customers_processed == 0:
            return 0.0
        return self.duration_seconds / self.customers_processed


# =========================
# HELPER FUNCTIONS
# =========================

def clean(x):
    """Clean and normalize string values"""
    if x is None:
        return ""
    if pd.isna(x):
        return ""
    return str(x).strip()


def classify_group(sku: str) -> Optional[str]:
    """Classify product group from SKU"""
    if not isinstance(sku, str) or len(sku) == 0:
        return None
    return sku[0].upper()


# =========================
# API FUNCTIONS
# =========================

def load_all_customers_from_d365() -> List[Dict]:
    """Load all customers from D365 API"""
    customer_api_url = os.getenv("CUSTOMER_API_URL", "").strip() or DEFAULT_CUSTOMER_API_URL
    customer_api_key = os.getenv("CUSTOMER_API_KEY", "").strip() or DEFAULT_CUSTOMER_API_KEY
    
    headers = {
        "apikey": customer_api_key,
        "Content-Type": "application/json",
    }
    
    rows = []
    page = 1
    
    logger.info("📥 Loading customers from D365 API...")
    logger.info(f"   API URL: {customer_api_url}")
    logger.info(f"   API Key: {customer_api_key[:50]}..." if len(customer_api_key) > 50 else f"   API Key: {customer_api_key}")
    
    while True:
        payload = {"page": page, "size": API_PAGE_SIZE}
        
        try:
            resp = requests.post(
                customer_api_url,
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT,
            )
            resp.raise_for_status()
            
            data = resp.json()
            items = data.get("data") or data
            
            if not items:
                logger.info(f"  ✓ page={page}: No more data")
                break
            
            rows.extend(items)
            logger.info(f"  ✓ page={page}: Loaded {len(items)} customers (total: {len(rows)})")
            
            if len(items) < API_PAGE_SIZE:
                logger.info("  ✓ Completed (last page)")
                break
            
            page += 1
            
        except Exception as e:
            logger.error(f"  ❌ Error on page={page}: {e}")
            logger.error(f"     Response Status: {resp.status_code if 'resp' in locals() else 'N/A'}")
            logger.error(f"     Response Body: {resp.text if 'resp' in locals() else 'N/A'}")
            break
    
    logger.info(f"📊 Total customers loaded: {len(rows)}")
    return rows


def load_invoices_for_customer(customer_code: str, calculation_date: date) -> List[Dict]:
    """Load invoices for specific customer"""
    invoice_api_url = os.getenv("INVOICE_API_URL", "").strip() or DEFAULT_INVOICE_API_URL
    invoice_api_key = os.getenv("INVOICE_API_KEY", "").strip() or DEFAULT_INVOICE_API_KEY
    
    headers = {
        "apikey": invoice_api_key,
        "Content-Type": "application/json",
    }
    
    rows = []
    page = 1
    max_page = 10
    
    date_to = calculation_date.isoformat()
    date_from = (calculation_date - timedelta(days=180)).isoformat()
    
    while True:
        payload = {
            "page": page,
            "size": API_PAGE_SIZE,
            "customer_code": {"$eq": customer_code},
            "Posting Date": {"$gte": date_from, "$lte": date_to},
        }
        
        try:
            resp = requests.post(
                invoice_api_url,
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT,
            )
            resp.raise_for_status()
            
            data = resp.json()
            items = data.get("data") or []
            
            if not items:
                break
            
            rows.extend(items)
            
            if len(items) < API_PAGE_SIZE:
                break
            
            page += 1
            if page > max_page:
                break
                
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to load invoices for {customer_code}: {e}")
            break
    
    return rows


def calculate_analytics(invoices: List[Dict], calculation_date: date) -> Dict[str, float]:
    """Calculate customer analytics from invoices"""
    if not invoices:
        return {
            "accum_6m": 0.0,
            "frequency": 0,
            "sales_g_cust": 0.0,
            "sales_a_cust": 0.0,
            "sales_s_cust": 0.0,
            "sales_y_cust": 0.0,
            "sales_c_cust": 0.0,
            "sales_e_cust": 0.0,
        }
    
    inv = pd.DataFrame(invoices)
    
    if "sku" in inv.columns and "No." not in inv.columns:
        inv["No."] = inv["sku"]
    
    # Convert dates and remove timezone
    inv["Posting Date"] = pd.to_datetime(inv["Posting Date"], errors="coerce", utc=True).dt.tz_localize(None)
    
    # Filter by date range
    cutoff = calculation_date - timedelta(days=180)
    cutoff_timestamp = pd.Timestamp(cutoff)
    inv6 = inv[inv["Posting Date"] >= cutoff_timestamp]
    
    if inv6.empty:
        return {
            "accum_6m": 0.0,
            "frequency": 0,
            "sales_g_cust": 0.0,
            "sales_a_cust": 0.0,
            "sales_s_cust": 0.0,
            "sales_y_cust": 0.0,
            "sales_c_cust": 0.0,
            "sales_e_cust": 0.0,
        }
    
    # Handle missing amount column
    amount_col = None
    for col_name in ["Line_Amount_Include_VAT", "Amount Including VAT", "Amount", "Total Amount"]:
        if col_name in inv6.columns:
            amount_col = col_name
            break
    
    if not amount_col:
        return {
            "accum_6m": 0.0,
            "frequency": int(inv6["Document No."].nunique()) if "Document No." in inv6.columns else 0,
            "sales_g_cust": 0.0,
            "sales_a_cust": 0.0,
            "sales_s_cust": 0.0,
            "sales_y_cust": 0.0,
            "sales_c_cust": 0.0,
            "sales_e_cust": 0.0,
        }
    
    accum_6m = float(inv6[amount_col].fillna(0).sum())
    frequency = int(inv6["Document No."].nunique()) if "Document No." in inv6.columns else 0
    
    inv6["group"] = inv6["No."].apply(classify_group) if "No." in inv6.columns else "U"
    grp = inv6.groupby("group")[amount_col].sum().to_dict()
    
    return {
        "accum_6m": accum_6m,
        "frequency": frequency,
        "sales_g_cust": float(grp.get("G", 0)),
        "sales_a_cust": float(grp.get("A", 0)),
        "sales_s_cust": float(grp.get("S", 0)),
        "sales_y_cust": float(grp.get("Y", 0)),
        "sales_c_cust": float(grp.get("C", 0)),
        "sales_e_cust": float(grp.get("E", 0)),
    }


# =========================
# DATABASE FUNCTIONS
# =========================

def upsert_customer_batch(customers: List[CustomerCacheRecord], conn: pyodbc.Connection) -> int:
    """Upsert customer batch to database"""
    if not customers:
        return 0
    
    cursor = conn.cursor()
    success_count = 0
    
    merge_sql = """
    MERGE INTO Customer AS target
    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) 
        AS source (customer_code, customer_name, phone, tax_no, gen_bus, payment_terms, customer_date, blocked,
                   accum_6m, frequency, sales_g_cust, sales_a_cust, sales_s_cust, sales_y_cust,
                   sales_c_cust, sales_e_cust, calculation_date, last_updated)
    ON target.customer_code = source.customer_code
    WHEN MATCHED THEN
        UPDATE SET
            customer_name = source.customer_name,
            phone = source.phone,
            tax_no = source.tax_no,
            gen_bus = source.gen_bus,
            payment_terms = source.payment_terms,
            customer_date = source.customer_date,
            blocked = source.blocked,
            accum_6m = source.accum_6m,
            frequency = source.frequency,
            sales_g_cust = source.sales_g_cust,
            sales_a_cust = source.sales_a_cust,
            sales_s_cust = source.sales_s_cust,
            sales_y_cust = source.sales_y_cust,
            sales_c_cust = source.sales_c_cust,
            sales_e_cust = source.sales_e_cust,
            calculation_date = source.calculation_date,
            last_updated = source.last_updated
    WHEN NOT MATCHED THEN
        INSERT (customer_code, customer_name, phone, tax_no, gen_bus, payment_terms, customer_date, blocked,
                accum_6m, frequency, sales_g_cust, sales_a_cust, sales_s_cust, sales_y_cust,
                sales_c_cust, sales_e_cust, calculation_date, last_updated)
        VALUES (source.customer_code, source.customer_name, source.phone, source.tax_no, source.gen_bus,
                source.payment_terms, source.customer_date, source.blocked, source.accum_6m, source.frequency,
                source.sales_g_cust, source.sales_a_cust, source.sales_s_cust, source.sales_y_cust,
                source.sales_c_cust, source.sales_e_cust, source.calculation_date, source.last_updated);
    """
    
    for customer in customers:
        try:
            cursor.execute(merge_sql, (
                customer.customer_code,
                customer.customer_name,
                customer.phone or None,
                customer.tax_no or None,
                customer.gen_bus or None,
                customer.payment_terms or None,
                customer.customer_date or None,
                customer.blocked or None,
                customer.accum_6m,
                customer.frequency,
                customer.sales_g_cust,
                customer.sales_a_cust,
                customer.sales_s_cust,
                customer.sales_y_cust,
                customer.sales_c_cust,
                customer.sales_e_cust,
                customer.calculation_date,
                datetime.now()
            ))
            success_count += 1
        except Exception as e:
            logger.error(f"  ❌ Failed to upsert {customer.customer_code}: {e}")
    
    conn.commit()
    cursor.close()
    
    return success_count


# =========================
# MAIN JOB FUNCTION
# =========================

def run_customer_cache_refresh() -> JobExecutionResult:
    """
    Main job function: ดึงข้อมูล Customer และ Analytics จาก D365 มาลง database
    
    Returns:
        JobExecutionResult with job execution details
    """
    start_time = datetime.now()
    calculation_date = date.today()
    
    logger.info("=" * 80)
    logger.info("🚀 Starting Customer Cache Refresh Job")
    logger.info(f"   Start Time: {start_time}")
    logger.info(f"   Calculation Date: {calculation_date}")
    logger.info("=" * 80)
    
    result = JobExecutionResult(
        start_time=start_time,
        end_time=start_time,
        calculation_date=calculation_date
    )
    
    try:
        customers_data = load_all_customers_from_d365()
        
        if not customers_data:
            logger.warning("⚠️ No customers loaded from API")
            result.end_time = datetime.now()
            return result
        
        conn = get_mssql_conn()
        batch = []
        
        for idx, cust_data in enumerate(customers_data, 1):
            try:
                customer_code = clean(cust_data.get("Customer_No"))
                
                if not customer_code:
                    logger.warning(f"  ⚠️ Skipping customer {idx}: No customer code")
                    result.customers_failed += 1
                    continue
                
                invoices = load_invoices_for_customer(customer_code, calculation_date)
                analytics = calculate_analytics(invoices, calculation_date)
                
                customer_record = CustomerCacheRecord(
                    customer_code=customer_code,
                    customer_name=clean(cust_data.get("Name")),
                    phone=clean(cust_data.get("Phone_No")),
                    tax_no=clean(cust_data.get("VAT_Registration_No")),
                    gen_bus=clean(cust_data.get("Gen_Bus_Posting_Group")),
                    payment_terms=clean(cust_data.get("Payment_Terms_Code")),
                    customer_date=clean(cust_data.get("Customer_Date")),
                    blocked=clean(cust_data.get("Blocked")),
                    **analytics,
                    calculation_date=calculation_date
                )
                
                batch.append(customer_record)
                result.customers_processed += 1
                
                if len(batch) >= BATCH_SIZE:
                    success_count = upsert_customer_batch(batch, conn)
                    result.customers_updated += success_count
                    logger.info(f"  ✓ Processed {result.customers_processed}/{len(customers_data)} customers")
                    batch = []
                
            except Exception as e:
                logger.error(f"  ❌ Error processing customer {idx}: {e}")
                result.customers_failed += 1
                result.errors.append(f"Customer {idx}: {str(e)}")
        
        if batch:
            success_count = upsert_customer_batch(batch, conn)
            result.customers_updated += success_count
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        result.errors.append(f"Critical: {str(e)}")
    
    result.end_time = datetime.now()
    
    logger.info("=" * 80)
    logger.info("✅ Customer Cache Refresh Job Completed")
    logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
    logger.info(f"   Customers Processed: {result.customers_processed}")
    logger.info(f"   Customers Updated: {result.customers_updated}")
    logger.info(f"   Customers Failed: {result.customers_failed}")
    if result.errors:
        logger.info(f"   Errors: {len(result.errors)}")
    logger.info("=" * 80)
    
    return result


# =========================
# CLI ENTRY POINT
# =========================

if __name__ == "__main__":
    """Run the job when executed as a script"""
    print("Starting Customer Cache Refresh Job...")
    result = run_customer_cache_refresh()
    
    # Print summary
    print("\n" + "=" * 80)
    print("JOB SUMMARY")
    print("=" * 80)
    print(f"Duration: {result.duration_seconds:.2f} seconds")
    print(f"Customers Processed: {result.customers_processed}")
    print(f"Customers Updated: {result.customers_updated}")
    print(f"Customers Failed: {result.customers_failed}")
    
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(result.errors) > 10:
            print(f"  ... and {len(result.errors) - 10} more errors")
        exit(1)
    else:
        print("\n✅ Job completed successfully!")
        exit(0)
