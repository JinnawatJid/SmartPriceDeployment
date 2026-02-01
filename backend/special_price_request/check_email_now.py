#!/usr/bin/env python3
"""
ตรวจสอบอีเมลทันที (สำหรับทดสอบ)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from special_price_request.email_reply_checker import check_email_replies

if __name__ == "__main__":
    print("🔍 Checking emails now...")
    check_email_replies()
    print("✅ Done!")
