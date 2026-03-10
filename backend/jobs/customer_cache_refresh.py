# customer_cache_refresh.py
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import requests
import pyodbc

from config.config_external_api import (
    CUSTOMER_API_URL,
    CUSTOMER_API_HEADERS,
    INVOICE_API_URL,
    INVOICE_API_HEADERS,
)
from config.db_mssql import get_mssql_conn
from config.cache_config import (
    BATCH_SIZE,
    API_PAGE_SIZE,
    API_TIMEOUT,
)
from jobs.cache_logger import cache_logger


@dataclass
class CustomerCacheRecord:
    customer_code: str
    customer_name: str
    phone: Optional[str] = ""
    tax_no: Optional[str] = ""
    gen_bus: Optional[str] = ""
    payment_terms: Optional[str] = ""
    customer_date: Optional[str] = ""
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


def clean(x):
    if x is None:
        return ""
    if pd.isna(x):
        return ""
    return str(x).strip()


def classify_group(sku: str) -> Optional[str]:
    if not isinstance(sku, str) or len(sku) == 0:
        return None
    return sku[0].upper()


def load_all_customers_from_d365() -> List[Dict]:
    rows = []
    page = 1
    
    cache_logger.info("📥 Loading customers from D365 API...")
    
    while True:
        payload = {"page": page, "size": API_PAGE_SIZE}
        
        try:
            resp = requests.post(
                CUSTOMER_API_URL,
                json=payload,
                headers=CUSTOMER_API_HEADERS,
                timeout=API_TIMEOUT,
            )
            resp.raise_for_status()
            
            data = resp.json()
            items = data.get("data") or data
            
            if not items:
                cache_logger.info(f"  ✓ page={page}: No more data")
                break
            
            rows.extend(items)
            cache_logger.info(f"  ✓ page={page}: Loaded {len(items)} customers (total: {len(rows)})")
            
            if len(items) < API_PAGE_SIZE:
                cache_logger.info("  ✓ Completed (last page)")
                break
            
            page += 1
            
        except Exception as e:
            cache_logger.error(f"  ❌ Error on page={page}: {e}")
            break
    
    cache_logger.info(f"📊 Total customers loaded: {len(rows)}")
    return rows


def load_invoices_for_customer(customer_code: str, calculation_date: date) -> List[Dict]:
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
                INVOICE_API_URL,
                json=payload,
                headers=INVOICE_API_HEADERS,
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
            cache_logger.warning(f"  ⚠️ Failed to load invoices for {customer_code}: {e}")
            break
    
    return rows


def calculate_analytics(invoices: List[Dict], calculation_date: date) -> Dict[str, float]:
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
    
    # FIX: Convert dates and remove timezone
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
    
    # Handle missing amount column - try different column names
    amount_col = None
    for col_name in ["Line_Amount_Include_VAT", "Amount Including VAT", "Amount", "Total Amount"]:
        if col_name in inv6.columns:
            amount_col = col_name
            break
    
    if not amount_col:
        # If no amount column found, return zeros
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


def upsert_customer_batch(customers: List[CustomerCacheRecord], conn: pyodbc.Connection) -> int:
    if not customers:
        return 0
    
    cursor = conn.cursor()
    success_count = 0
    
    merge_sql = """
    MERGE INTO Customer AS target
    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) 
        AS source (customer_code, customer_name, phone, tax_no, gen_bus, payment_terms, customer_date,
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
        INSERT (customer_code, customer_name, phone, tax_no, gen_bus, payment_terms, customer_date,
                accum_6m, frequency, sales_g_cust, sales_a_cust, sales_s_cust, sales_y_cust,
                sales_c_cust, sales_e_cust, calculation_date, last_updated)
        VALUES (source.customer_code, source.customer_name, source.phone, source.tax_no, source.gen_bus,
                source.payment_terms, source.customer_date, source.accum_6m, source.frequency,
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
            cache_logger.error(f"  ❌ Failed to upsert {customer.customer_code}: {e}")
    
    conn.commit()
    cursor.close()
    
    return success_count


def run_customer_cache_refresh() -> JobExecutionResult:
    start_time = datetime.now()
    calculation_date = date.today()
    
    cache_logger.info("=" * 60)
    cache_logger.info("🚀 Starting Customer Cache Refresh Job")
    cache_logger.info(f"   Start Time: {start_time}")
    cache_logger.info(f"   Calculation Date: {calculation_date}")
    cache_logger.info("=" * 60)
    
    result = JobExecutionResult(
        start_time=start_time,
        end_time=start_time,
        calculation_date=calculation_date
    )
    
    try:
        customers_data = load_all_customers_from_d365()
        
        if not customers_data:
            cache_logger.warning("⚠️ No customers loaded from API")
            result.end_time = datetime.now()
            return result
        
        conn = get_mssql_conn()
        batch = []
        
        for idx, cust_data in enumerate(customers_data, 1):
            try:
                customer_code = clean(cust_data.get("customer_code") or cust_data.get("Customer"))
                
                if not customer_code:
                    cache_logger.warning(f"  ⚠️ Skipping customer {idx}: No customer code")
                    result.customers_failed += 1
                    continue
                
                invoices = load_invoices_for_customer(customer_code, calculation_date)
                analytics = calculate_analytics(invoices, calculation_date)
                
                customer_record = CustomerCacheRecord(
                    customer_code=customer_code,
                    customer_name=clean(cust_data.get("customer_name") or cust_data.get("Name")),
                    phone=clean(cust_data.get("phone") or cust_data.get("Tel")),
                    tax_no=clean(cust_data.get("tax_no") or cust_data.get("Tax No.")),
                    gen_bus=clean(cust_data.get("gen_bus") or cust_data.get("Gen Bus")),
                    payment_terms=clean(cust_data.get("payment_terms") or cust_data.get("Payment Terms Code")),
                    customer_date=clean(cust_data.get("customer_date") or cust_data.get("Customer Date")),
                    **analytics,
                    calculation_date=calculation_date
                )
                
                batch.append(customer_record)
                result.customers_processed += 1
                
                if len(batch) >= BATCH_SIZE:
                    success_count = upsert_customer_batch(batch, conn)
                    result.customers_updated += success_count
                    cache_logger.info(f"  ✓ Processed {result.customers_processed}/{len(customers_data)} customers")
                    batch = []
                
            except Exception as e:
                cache_logger.error(f"  ❌ Error processing customer {idx}: {e}")
                result.customers_failed += 1
                result.errors.append(f"Customer {idx}: {str(e)}")
        
        if batch:
            success_count = upsert_customer_batch(batch, conn)
            result.customers_updated += success_count
        
        conn.close()
        
    except Exception as e:
        cache_logger.error(f"❌ Critical error: {e}")
        result.errors.append(f"Critical: {str(e)}")
    
    result.end_time = datetime.now()
    
    cache_logger.info("=" * 60)
    cache_logger.info("✅ Customer Cache Refresh Job Completed")
    cache_logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
    cache_logger.info(f"   Customers Processed: {result.customers_processed}")
    cache_logger.info(f"   Customers Updated: {result.customers_updated}")
    cache_logger.info(f"   Customers Failed: {result.customers_failed}")
    cache_logger.info("=" * 60)
    
    return result
