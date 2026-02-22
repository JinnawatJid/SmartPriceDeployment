#!/usr/bin/env python3
"""
ตรวจสอบไฟล์ PDF ที่บันทึกในฐานข้อมูล
"""

from config.db_mssql import get_mssql_conn
import json


def check_pdf_files():
    """
    แสดงรายการคำขอที่มีไฟล์ PDF แนบ
    """
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT request_number, status, approved_by, approval_pdf_files
            FROM special_price_requests
            WHERE approval_pdf_files IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ ไม่พบคำขอที่มีไฟล์ PDF แนบ")
            return
        
        print(f"\n📋 พบ {len(results)} คำขอที่มีไฟล์ PDF แนบ:\n")
        
        for row in results:
            request_number = row[0]
            status = row[1]
            approved_by = row[2]
            pdf_files_json = row[3]
            
            print(f"{'='*60}")
            print(f"Request: {request_number}")
            print(f"Status: {status}")
            print(f"Approved by: {approved_by}")
            
            if pdf_files_json:
                try:
                    pdf_files = json.loads(pdf_files_json)
                    print(f"PDF Files ({len(pdf_files)}):")
                    for i, file_path in enumerate(pdf_files, 1):
                        print(f"  {i}. {file_path}")
                except Exception as e:
                    print(f"  ❌ Error parsing JSON: {e}")
                    print(f"  Raw: {pdf_files_json}")
            else:
                print("PDF Files: None")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("ตรวจสอบไฟล์ PDF ในฐานข้อมูล")
    print("="*60)
    check_pdf_files()
