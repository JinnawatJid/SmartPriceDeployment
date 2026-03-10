# jobs/scheduler.py
"""
Background Job Scheduler
รัน invoice cache refresh, customer cache refresh, และ item master cache refresh
- Invoice Cache: ทุกวันเวลา 19:00 น. (7 ทุ่ม)
- Item Master Cache: ทุกวันเวลา 19:00 น. (7 ทุ่ม) - รันพร้อมกับ invoice
- Customer Cache: รันหลัง invoice เสร็จแล้ว (ไม่ตั้งเวลา)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from jobs.invoice_cache_refresh import run_invoice_cache_refresh
from jobs.customer_cache_refresh import run_customer_cache_refresh
from jobs.item_master_cache_refresh import run_item_master_cache_refresh
from jobs.cache_logger import cache_logger

logger = logging.getLogger(__name__)

# สร้าง scheduler instance
scheduler = BackgroundScheduler(
    timezone="Asia/Bangkok",  # ตั้งเวลาตาม timezone ไทย
    job_defaults={
        'coalesce': True,  # รวม job ที่พลาดไว้เป็น 1 job
        'max_instances': 1,  # รัน job ได้ครั้งละ 1 instance
        'misfire_grace_time': 3600  # ถ้าพลาดไป ยังรันได้ภายใน 1 ชั่วโมง
    }
)


def scheduled_invoice_cache_refresh():
    """
    Wrapper function สำหรับรัน invoice cache refresh job
    เมื่อ invoice เสร็จ จะเรียก customer cache refresh โดยอัตโนมัติ
    """
    try:
        cache_logger.info("=" * 80)
        cache_logger.info("🕐 Scheduled Invoice Cache Refresh Started")
        cache_logger.info(f"   Triggered at: {datetime.now()}")
        cache_logger.info("=" * 80)
        
        result = run_invoice_cache_refresh(months=6)
        
        cache_logger.info("=" * 80)
        cache_logger.info("✅ Scheduled Invoice Cache Refresh Completed")
        cache_logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
        cache_logger.info(f"   Processed: {result.invoices_processed}")
        cache_logger.info(f"   Inserted: {result.invoices_inserted}")
        cache_logger.info(f"   Failed: {result.invoices_failed}")
        cache_logger.info("=" * 80)
        
        # เรียก customer cache refresh หลัง invoice เสร็จ
        cache_logger.info("🔄 Triggering Customer Cache Refresh (after invoice completed)...")
        scheduled_customer_cache_refresh()
        
    except Exception as e:
        cache_logger.error(f"❌ Scheduled invoice job failed: {e}", exc_info=True)
        logger.error(f"Scheduled invoice cache refresh failed: {e}", exc_info=True)


def scheduled_customer_cache_refresh():
    """
    Wrapper function สำหรับรัน customer cache refresh job
    รันหลัง invoice cache refresh เสร็จแล้ว
    """
    try:
        cache_logger.info("=" * 80)
        cache_logger.info("🕐 Scheduled Customer Cache Refresh Started")
        cache_logger.info(f"   Triggered at: {datetime.now()}")
        cache_logger.info("=" * 80)
        
        result = run_customer_cache_refresh()
        
        cache_logger.info("=" * 80)
        cache_logger.info("✅ Scheduled Customer Cache Refresh Completed")
        cache_logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
        cache_logger.info(f"   Processed: {result.customers_processed}")
        cache_logger.info(f"   Updated: {result.customers_updated}")
        cache_logger.info(f"   Failed: {result.customers_failed}")
        cache_logger.info("=" * 80)
        
    except Exception as e:
        cache_logger.error(f"❌ Scheduled customer job failed: {e}", exc_info=True)
        logger.error(f"Scheduled customer cache refresh failed: {e}", exc_info=True)


def scheduled_item_master_cache_refresh():
    """
    Wrapper function สำหรับรัน item master cache refresh job
    รันหลัง customer cache refresh เสร็จแล้ว
    """
    try:
        cache_logger.info("=" * 80)
        cache_logger.info("🕐 Scheduled Item Master Cache Refresh Started")
        cache_logger.info(f"   Triggered at: {datetime.now()}")
        cache_logger.info("=" * 80)
        
        result = run_item_master_cache_refresh()
        
        cache_logger.info("=" * 80)
        cache_logger.info("✅ Scheduled Item Master Cache Refresh Completed")
        cache_logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
        cache_logger.info(f"   Processed: {result.items_processed}")
        cache_logger.info(f"   Inserted: {result.items_inserted}")
        cache_logger.info(f"   Updated: {result.items_updated}")
        cache_logger.info(f"   Failed: {result.items_failed}")
        if result.errors:
            cache_logger.info(f"   Errors: {len(result.errors)}")
        cache_logger.info("=" * 80)
        
    except Exception as e:
        cache_logger.error(f"❌ Scheduled item master job failed: {e}", exc_info=True)
        logger.error(f"Scheduled item master cache refresh failed: {e}", exc_info=True)


def start_scheduler():
    """
    เริ่มต้น scheduler และเพิ่ม jobs
    """
    try:
        # Job 1: Invoice Cache Refresh - รันเวลา 19:00 น. (7 ทุ่ม)
        scheduler.add_job(
            func=scheduled_invoice_cache_refresh,
            trigger=CronTrigger(hour=19, minute=0),
            id='invoice_cache_refresh',
            name='Invoice Cache Refresh (Daily 19:00)',
            replace_existing=True
        )
        
        # Job 2: Item Master Cache Refresh - รันเวลา 19:00 น. (7 ทุ่ม) พร้อมกับ invoice
        scheduler.add_job(
            func=scheduled_item_master_cache_refresh,
            trigger=CronTrigger(hour=19, minute=0),
            id='item_master_cache_refresh',
            name='Item Master Cache Refresh (Daily 19:00)',
            replace_existing=True
        )
        
        # Job 3: Customer Cache Refresh - รันหลัง invoice เสร็จ (ไม่ตั้งเวลา)
        # จะถูกเรียกจาก scheduled_invoice_cache_refresh เมื่อ invoice เสร็จ
        
        # เริ่มต้น scheduler
        scheduler.start()
        
        logger.info("=" * 80)
        logger.info("✅ Background Scheduler Started")
        logger.info("   Scheduled Jobs:")
        for job in scheduler.get_jobs():
            logger.info(f"   - {job.name} (ID: {job.id})")
            logger.info(f"     Next run: {job.next_run_time}")
        logger.info("=" * 80)
        
        cache_logger.info("✅ Scheduler started successfully")
        cache_logger.info(f"   Job 1: Invoice Cache - 19:00 (7 ทุ่ม) daily")
        cache_logger.info(f"   Job 2: Item Master Cache - 19:00 (7 ทุ่ม) daily (parallel with invoice)")
        cache_logger.info(f"   Job 3: Customer Cache - runs after invoice completes")
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
        cache_logger.error(f"Failed to start scheduler: {e}", exc_info=True)


def stop_scheduler():
    """
    หยุด scheduler (เรียกตอน shutdown)
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("✅ Background Scheduler Stopped")
            cache_logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}", exc_info=True)


def trigger_manual_refresh():
    """
    รัน jobs ทันทีแบบ manual (สำหรับ API endpoint)
    - Invoice และ Item Master รันพร้อมกัน
    - Customer รันหลัง invoice เสร็จ
    """
    try:
        cache_logger.info("🔧 Manual refresh triggered")
        
        # 1. รัน invoice cache refresh และ item master cache refresh พร้อมกัน
        cache_logger.info("Step 1: Running invoice cache refresh and item master cache refresh (parallel)...")
        invoice_result = run_invoice_cache_refresh(months=6)
        item_result = run_item_master_cache_refresh()
        cache_logger.info(f"Invoice refresh completed: {invoice_result.invoices_processed} invoices")
        cache_logger.info(f"Item master refresh completed: {item_result.items_processed} items")
        
        # 2. รัน customer cache refresh หลัง invoice เสร็จ
        cache_logger.info("Step 2: Running customer cache refresh (after invoice completed)...")
        customer_result = run_customer_cache_refresh()
        cache_logger.info(f"Customer refresh completed: {customer_result.customers_processed} customers")
        
        return {
            "invoice": invoice_result,
            "customer": customer_result,
            "item_master": item_result
        }
    except Exception as e:
        cache_logger.error(f"Manual refresh failed: {e}", exc_info=True)
        raise


# ฟังก์ชันสำหรับดูสถานะ scheduler
def get_scheduler_status():
    """
    ดูสถานะของ scheduler และ jobs ที่กำลังรัน
    """
    if not scheduler.running:
        return {
            "status": "stopped",
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running",
        "timezone": "Asia/Bangkok",
        "jobs": jobs
    }
