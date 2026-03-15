import sys
sys.path.append('backend')

from config.db_mssql import get_mssql_conn

conn = get_mssql_conn()
cursor = conn.cursor()

# Check all requests
cursor.execute("""
    SELECT TOP 5 *
    FROM special_price_requests
    ORDER BY created_at DESC
""")

print("\n=== ALL SPECIAL PRICE REQUESTS ===")
columns = [desc[0] for desc in cursor.description]
print(" | ".join(columns))
print("-" * 120)

for row in cursor.fetchall():
    print(" | ".join(str(val) for val in row))

# Check items with approval levels
cursor.execute("""
    SELECT TOP 10 *
    FROM special_price_request_items
    ORDER BY id DESC
""")

print("\n\n=== REQUEST ITEMS WITH APPROVAL LEVELS ===")
columns = [desc[0] for desc in cursor.description]
print(" | ".join(columns))
print("-" * 120)

for row in cursor.fetchall():
    print(" | ".join(str(val) for val in row))

cursor.close()
conn.close()
