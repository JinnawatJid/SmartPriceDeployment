#!/usr/bin/env python3
"""
สคริปต์สำหรับสร้างตาราง approval_tokens
"""

from pathlib import Path
from config.db_sqlite import get_conn


def init_approval_tokens_table():
    """สร้างตาราง approval_tokens"""
    
    sql_file = Path(__file__).parent / "create_approval_tokens_table.sql"
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Execute SQL
        cur.executescript(sql)
        conn.commit()
        print("✅ สร้างตาราง approval_tokens สำเร็จ")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        conn.rollback()
        
    finally:
        conn.close()


if __name__ == "__main__":
    init_approval_tokens_table()
