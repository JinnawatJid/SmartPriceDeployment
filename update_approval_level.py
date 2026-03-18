import sys
sys.path.append('backend')

from config.db_mssql import get_mssql_conn

conn = get_mssql_conn()
cursor = conn.cursor()

# Update item 21 (request 22) to ZM_THEN_RM
cursor.execute("""
    UPDATE special_price_request_items
    SET approval_level = 'ZM_THEN_RM'
    WHERE id = 21
""")

conn.commit()

print("✅ Updated item 21 approval_level to ZM_THEN_RM")

# Verify
cursor.execute("""
    SELECT id, item_code, requested_price, approval_level
    FROM special_price_request_items
    WHERE id = 21
""")

row = cursor.fetchone()
print(f"Item {row[0]}: {row[1]} - Price: {row[2]} - Level: {row[3]}")

cursor.close()
conn.close()
