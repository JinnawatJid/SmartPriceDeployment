#!/usr/bin/env python3
"""
ตรวจสอบอีเมลทันที (สำหรับทดสอบ)
"""

from special_price_request.email_reply_checker import check_email_replies

if __name__ == "__main__":
    print("🔍 Checking emails now...")
    check_email_replies()
    print("✅ Done!")
