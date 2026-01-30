#!/usr/bin/env python3
"""
Email Reply Checker - Background Service
ตรวจสอบ email ทุก 1 นาที (ปรับได้ตามต้องการ)
"""

import time
import schedule
import sys
from special_price_request.email_reply_checker import check_email_replies

# ⭐ ปรับระยะเวลาตรวจสอบได้ที่นี่ (หน่วยเป็นนาที)
CHECK_INTERVAL_MINUTES = 1  # เปลี่ยนเป็น 1, 2, 5, 10 ตามต้องการ


def job():
    """Run email checker"""
    try:
        check_email_replies()
    except Exception as e:
        print(f"❌ Error in email checker: {e}")


if __name__ == "__main__":
    # รับ interval จาก command line argument (ถ้ามี)
    interval = CHECK_INTERVAL_MINUTES
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"⚠️  Invalid interval, using default: {CHECK_INTERVAL_MINUTES} minutes")
    
    print("🚀 Starting Email Reply Checker Service...")
    print(f"⏰ Checking emails every {interval} minute(s)")
    print("Press Ctrl+C to stop\n")
    
    # Run immediately on start
    job()
    
    # Schedule to run every N minutes
    schedule.every(interval).minutes.do(job)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Email checker stopped")
