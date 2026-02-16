import pyodbc

try:
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-HBJR1VH;DATABASE=SmartPrice;Trusted_Connection=yes;', timeout=5)
    cur = conn.cursor()

    # 1. ตรวจสอบค่า Variant_Mandatory ทั้งหมดในกระจก
    print("=" * 60)
    print("📊 Variant_Mandatory distribution in glass items (SKU LIKE 'G%'):")
    print("=" * 60)
    
    cur.execute("""
        SELECT DISTINCT Variant_Mandatory, COUNT(*) as cnt 
        FROM Item_Master 
        WHERE SKU LIKE 'G%' 
        GROUP BY Variant_Mandatory 
        ORDER BY Variant_Mandatory
    """)

    total = 0
    for row in cur.fetchall():
        value = row[0] if row[0] is not None else "NULL"
        count = row[1]
        total += count
        print(f"  Variant_Mandatory = {value}: {count} items")
    
    print(f"\n  Total glass items: {total}")
    
    # 2. แสดงตัวอย่างกระจกที่ Variant_Mandatory = 2
    print("\n" + "=" * 60)
    print("🔍 Sample glass items with Variant_Mandatory = 2:")
    print("=" * 60)
    
    cur.execute("""
        SELECT TOP 10 SKU, Description, Variant_Mandatory
        FROM Item_Master 
        WHERE SKU LIKE 'G%' AND Variant_Mandatory = 2
        ORDER BY SKU
    """)
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]} | {row[1]} | Variant={row[2]}")
    else:
        print("  ❌ No glass items found with Variant_Mandatory = 2")
    
    # 3. แสดงตัวอย่างกระจกที่ Variant_Mandatory = 1
    print("\n" + "=" * 60)
    print("🔍 Sample glass items with Variant_Mandatory = 1:")
    print("=" * 60)
    
    cur.execute("""
        SELECT TOP 5 SKU, Description, Variant_Mandatory
        FROM Item_Master 
        WHERE SKU LIKE 'G%' AND Variant_Mandatory = 1
        ORDER BY SKU
    """)
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]} | {row[1]} | Variant={row[2]}")
    else:
        print("  ❌ No glass items found with Variant_Mandatory = 1")

    conn.close()
    print("\n✅ Database check completed")

except Exception as e:
    print(f"❌ Error connecting to database: {e}")
    print("\nPlease make sure:")
    print("  1. SQL Server is running")
    print("  2. Database 'SmartPrice' exists")
    print("  3. You have access permissions")
