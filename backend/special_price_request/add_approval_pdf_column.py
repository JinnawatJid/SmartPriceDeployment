#!/usr/bin/env python3
"""
Add approval_pdf_files column to special_price_requests table
"""

from config.db_sqlite import get_conn

def add_approval_pdf_column():
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Check if column already exists
        cur.execute("PRAGMA table_info(special_price_requests)")
        columns = [row[1] for row in cur.fetchall()]
        
        if 'approval_pdf_files' in columns:
            print("✅ Column 'approval_pdf_files' already exists")
            return
        
        # Add column
        cur.execute("""
            ALTER TABLE special_price_requests 
            ADD COLUMN approval_pdf_files TEXT
        """)
        
        conn.commit()
        print("✅ Added column 'approval_pdf_files' to special_price_requests table")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_approval_pdf_column()
