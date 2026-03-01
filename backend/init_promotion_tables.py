"""
สคริปต์สำหรับสร้างตาราง Promotion_Header และ Promotion_Items
รันคำสั่ง: python backend/init_promotion_tables.py
"""

import sqlite3
import os

DB_PATH = "backend/config/data/Quetung.db"
SQL_FILE = "backend/sql/create_promotion_tables.sql"

def init_promotion_tables():
    """สร้างตาราง Promotion ในฐานข้อมูล"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ ไม่พบไฟล์ฐานข้อมูล: {DB_PATH}")
        return
    
    if not os.path.exists(SQL_FILE):
        print(f"❌ ไม่พบไฟล์ SQL: {SQL_FILE}")
        return
    
    try:
        # อ่าน SQL script
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # เชื่อมต่อฐานข้อมูล
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # รัน SQL script
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ สร้างตาราง Promotion สำเร็จ!")
        
        # ตรวจสอบตาราง
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Promotion%'")
        tables = cursor.fetchall()
        
        print("\n📋 ตารางที่สร้าง:")
        for table in tables:
            print(f"  - {table[0]}")
            
            # นับจำนวนแถว
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"    จำนวนแถว: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🚀 เริ่มสร้างตาราง Promotion")
    print("="*60)
    init_promotion_tables()
    print("="*60)
