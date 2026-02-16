"""
Check Variant_Mandatory values in Item_Master table
"""
import sys
sys.path.append('backend')

from config.db_mssql import get_mssql_conn

conn = get_mssql_conn()
cursor = conn.cursor()

print("=== DISTINCT Variant_Mandatory VALUES ===")
cursor.execute("""
    SELECT DISTINCT Variant_Mandatory, COUNT(*) as count
    FROM Item_Master
    WHERE SKU LIKE 'G%'
    GROUP BY Variant_Mandatory
    ORDER BY Variant_Mandatory
""")
rows = cursor.fetchall()
for row in rows:
    print(f"Variant_Mandatory: {row[0]} (type: {type(row[0])}) - Count: {row[1]}")

print("\n=== SAMPLE GLASS SKUs WITH Variant_Mandatory ===")
cursor.execute("""
    SELECT TOP 10 SKU, Variant_Mandatory
    FROM Item_Master
    WHERE SKU LIKE 'G%'
    ORDER BY SKU
""")
rows = cursor.fetchall()
for row in rows:
    print(f"SKU: {row[0]}, Variant_Mandatory: {row[1]} (type: {type(row[1])})")

conn.close()
