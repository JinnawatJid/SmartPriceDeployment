"""
Migration: Add approver information columns to special_price_requests table

This migration adds columns to track the actual person who approved each request:
- actual_approver_id: รหัสพนักงานที่อนุมัติจริง (e.g., "12345")
- actual_approver_name: ชื่อพนักงานที่อนุมัติจริง (e.g., "สมชาย ใจดี")
- actual_approver_role: Role ของผู้อนุมัติ (e.g., "ZM", "RM", "SDM")

This solves the problem where we know the role that approved (e.g., ZM_03TS)
but don't know who the actual person was.
"""

from config.db_mssql import get_mssql_conn

def run_migration():
    """Add approver information columns"""
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting migration: Add approver information columns...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'special_price_requests' 
            AND COLUMN_NAME = 'actual_approver_id'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ Columns already exist. Skipping migration.")
            return
        
        # Add new columns
        print("📝 Adding actual_approver_id column...")
        cursor.execute("""
            ALTER TABLE special_price_requests
            ADD actual_approver_id VARCHAR(50) NULL
        """)
        
        print("📝 Adding actual_approver_name column...")
        cursor.execute("""
            ALTER TABLE special_price_requests
            ADD actual_approver_name NVARCHAR(255) NULL
        """)
        
        print("📝 Adding actual_approver_role column...")
        cursor.execute("""
            ALTER TABLE special_price_requests
            ADD actual_approver_role VARCHAR(20) NULL
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
