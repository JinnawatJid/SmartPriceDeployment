"""
Airflow DAG: Item Master Cache Refresh

ดึงข้อมูล Item Master จาก D365 มา update ใน Item_Master table
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# import job function ของคุณ
from jobs.item_master_cache_refresh import run_item_master_cache_refresh


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
    dag_id="item_master_cache_refresh",
    description="Refresh Item Master cache from D365",
    default_args=default_args,
    schedule_interval="0 1 * * *",  # รันทุกวัน 01:00
    catchup=False,
    tags=["cache", "d365"],
) as dag:


    def run_item_master_job():
        result = run_item_master_cache_refresh()

        # log summary
        print("Item Master Cache Result:")
        print(f"Processed: {result.items_processed}")
        print(f"Inserted: {result.items_inserted}")
        print(f"Updated: {result.items_updated}")
        print(f"Failed: {result.items_failed}")

        if result.errors:
            raise Exception(f"Job finished with errors: {result.errors}")


    refresh_item_master = PythonOperator(
        task_id="refresh_item_master_cache",
        python_callable=run_item_master_job
    )


    refresh_item_master