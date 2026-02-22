#!/usr/bin/env python3
"""
Reset request status to pending for testing
"""

from config.db_mssql import get_mssql_conn
import sys


def reset_request_status(request_number: str):
    """
    เปลี่ยนสถานะคำขอกลับเป็น pending เพื่อทดสอบ
    """
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        # ตรวจสอบว่าคำขอมีอยู่
        cursor.execute("""
            SELECT request_number, status, approved_by, approval_pdf_files
            FROM special_price_requests
            WHERE request_number = ?
        """, (request_number,))
        
        result = cursor.fetchone()
        if not result:
            print(f"❌ ไม่พบคำขอ {request_number}")
            conn.close()
            return
        
        print(f"\n📋 สถานะปัจจุบัน:")
        print(f"   Request: {result[0]}")
        print(f"   Status: {result[1]}")
        print(f"   Approved by: {result[2]}")
        print(f"   PDF files: {result[3]}")
        
        # Reset status
        cursor.execute("""
            UPDATE special_price_requests
            SET status = 'pending',
                approved_by = NULL,
                approved_at = NULL,
                approval_pdf_files = NULL,
                rejection_reason = NULL
            WHERE request_number = ?
        """, (request_number,))
        
        conn.commit()
        print(f"\n✅ Reset สถานะเป็น pending สำเร็จ")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reset_request_status.py <request_number>")
        print("Example: python reset_request_status.py SP-260222-0010")
        sys.exit(1)
    
    request_number = sys.argv[1]
    print("="*60)
    print(f"Reset Request Status: {request_number}")
    print("="*60)
    reset_request_status(request_number)
    print("\n" + "="*60)
