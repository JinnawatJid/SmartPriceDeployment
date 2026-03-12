"""
Airflow DAG: D365 Cache Refresh Pipeline
ดึงข้อมูลจาก D365 มา update ใน database

Pipeline:
1. Invoice Cache Refresh (รันก่อน)
2. Customer Cache Refresh (ใช้ข้อมูล Invoice)
3. Item Master Cache Refresh (รันพร้อมกัน)

Schedule: รันทุกวัน 01:00 AM
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Import standalone job functions
from jobs.invoice_cache_refresh_standalone import run_invoice_cache_refresh
from jobs.customer_cache_refresh_standalone import run_customer_cache_refresh
from jobs.item_master_cache_refresh_standalone import run_item_master_cache_refresh

# ============================================
# Default DAG settings
# ============================================
default_args = {
    "owner": "supplysense",
    "depends_on_past": False,
    "start_date": datetime(2026, 3, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ============================================
# DAG
# ============================================
with DAG(
    dag_id="d365_cache_refresh_pipeline",
    description="Refresh Invoice, Customer, and Item Master cache from D365",
    default_args=default_args,
    schedule_interval="0 1 * * *",  # รันทุกวัน 01:00
    catchup=False,
    tags=["cache", "d365", "pipeline"],
) as dag:

    # ============================================
    # Task 1: Invoice Cache Refresh
    # ============================================
    def run_invoice_job():
        """ดึงข้อมูล Invoice ย้อนหลัง 6 เดือน"""
        result = run_invoice_cache_refresh(months=6)
        
        # Log summary
        print("=" * 80)
        print("INVOICE CACHE RESULT:")
        print("=" * 80)
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Processed: {result.invoices_processed}")
        print(f"Inserted: {result.invoices_inserted}")
        print(f"Failed: {result.invoices_failed}")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")
            raise Exception(f"Invoice job finished with {len(result.errors)} errors")
        
        print("✅ Invoice cache refresh completed successfully")
        return {
            "invoices_processed": result.invoices_processed,
            "invoices_inserted": result.invoices_inserted,
        }

    refresh_invoice = PythonOperator(
        task_id="refresh_invoice_cache",
        python_callable=run_invoice_job,
        doc_md="""
        ### Invoice Cache Refresh
        
        ดึงข้อมูล Invoice จาก D365 ย้อนหลัง 6 เดือน
        
        **ข้อมูลที่ดึง:**
        - Document No
        - Customer Code
        - Posting Date
        - SKU
        - Quantity
        - Amount
        
        **ตาราง:** Invoice
        """
    )

    # ============================================
    # Task 2: Customer Cache Refresh
    # ============================================
    def run_customer_job():
        """ดึงข้อมูล Customer และคำนวณ Analytics"""
        result = run_customer_cache_refresh()
        
        # Log summary
        print("=" * 80)
        print("CUSTOMER CACHE RESULT:")
        print("=" * 80)
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Processed: {result.customers_processed}")
        print(f"Updated: {result.customers_updated}")
        print(f"Failed: {result.customers_failed}")
        print(f"Avg time per customer: {result.avg_time_per_customer:.2f} seconds")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")
            raise Exception(f"Customer job finished with {len(result.errors)} errors")
        
        print("✅ Customer cache refresh completed successfully")
        return {
            "customers_processed": result.customers_processed,
            "customers_updated": result.customers_updated,
        }

    refresh_customer = PythonOperator(
        task_id="refresh_customer_cache",
        python_callable=run_customer_job,
        doc_md="""
        ### Customer Cache Refresh
        
        ดึงข้อมูล Customer จาก D365 และคำนวณ Analytics
        
        **ข้อมูลที่ดึง:**
        - Customer Code
        - Customer Name
        - Phone, Tax No
        - Payment Terms
        
        **Analytics ที่คำนวณ:**
        - accum_6m (ยอดซื้อ 6 เดือน)
        - frequency (ความถี่การซื้อ)
        - sales_g_cust, sales_a_cust, etc. (ยอดขายแยกตามหมวด)
        
        **ตาราง:** Customer
        
        **หมายเหตุ:** ต้องรัน Invoice Cache ก่อน
        """
    )

    # ============================================
    # Task 3: Item Master Cache Refresh
    # ============================================
    def run_item_master_job():
        """ดึงข้อมูล Item Master"""
        result = run_item_master_cache_refresh()
        
        # Log summary
        print("=" * 80)
        print("ITEM MASTER CACHE RESULT:")
        print("=" * 80)
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Processed: {result.items_processed}")
        print(f"Inserted: {result.items_inserted}")
        print(f"Updated: {result.items_updated}")
        print(f"Failed: {result.items_failed}")
        
        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for error in result.errors[:5]:
                print(f"  - {error}")
            raise Exception(f"Item Master job finished with {len(result.errors)} errors")
        
        print("✅ Item Master cache refresh completed successfully")
        return {
            "items_processed": result.items_processed,
            "items_inserted": result.items_inserted,
            "items_updated": result.items_updated,
        }

    refresh_item_master = PythonOperator(
        task_id="refresh_item_master_cache",
        python_callable=run_item_master_job,
        doc_md="""
        ### Item Master Cache Refresh
        
        ดึงข้อมูล Item Master จาก D365
        
        **ข้อมูลที่ดึง:**
        - SKU
        - Description
        - Base Unit of Measure
        - Product Group
        - Prices (R1, R2, W1, W2)
        - Package Size
        - Product Weight
        
        **ตาราง:** Item_Master
        """
    )

    # ============================================
    # Task Dependencies
    # ============================================
    # Invoice ต้องรันก่อน Customer (เพราะ Customer ใช้ข้อมูล Invoice)
    # Item Master สามารถรันพร้อมกับ Customer ได้
    refresh_invoice >> refresh_customer
    refresh_invoice >> refresh_item_master
