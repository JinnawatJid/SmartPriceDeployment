"""
Migration Script: Items_Test → Item_Master + Item_Price

This script migrates data from the old Items_Test table to the new
Item_Master and Item_Price tables with branch-based pricing.
"""

from config.db_mssql import get_mssql_conn
from datetime import datetime

def migrate_items():
    """Migrate items from Items_Test to Item_Master and Item_Price"""
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    print("="*60)
    print("Starting Items Migration")
    print("="*60)
    
    # Step 1: Get all items from Items_Test
    print("\n1. Reading items from Items_Test...")
    cursor.execute("SELECT COUNT(*) FROM Items_Test")
    total_items = cursor.fetchone()[0]
    print(f"   Found {total_items} items in Items_Test")
    
    cursor.execute("""
        SELECT 
            No, No_2, Description, Base_Unit_of_Measure,
            Inventory_Posting_Group, Variant_Mandatory_if_Exists,
            Product_Group, Product_Sub_Group,
            R1, R2, W1, W2, Package_Size, AlternateName
        FROM Items_Test
    """)
    items = cursor.fetchall()
    
    # Step 2: Migrate to Item_Master
    print("\n2. Migrating to Item_Master...")
    inserted_master = 0
    skipped_master = 0
    
    for item in items:
        sku = item[0]
        
        # Check if already exists
        cursor.execute("SELECT COUNT(*) FROM Item_Master WHERE SKU = ?", (sku,))
        if cursor.fetchone()[0] > 0:
            skipped_master += 1
            continue
        
        # Insert into Item_Master
        try:
            cursor.execute("""
                INSERT INTO Item_Master (
                    SKU, No_2, Description, Base_Unit_of_Measure,
                    Inventory_Posting_Group, Variant_Mandatory,
                    Product_Group, Product_Sub_Group, CreatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item[0],  # SKU
                item[1],  # No_2
                item[2],  # Description
                item[3],  # Base_Unit_of_Measure
                item[4],  # Inventory_Posting_Group
                item[5],  # Variant_Mandatory
                item[6],  # Product_Group
                item[7],  # Product_Sub_Group
                datetime.now()  # CreatedAt
            ))
            inserted_master += 1
        except Exception as e:
            print(f"   Error inserting {sku}: {e}")
    
    conn.commit()
    print(f"   Inserted: {inserted_master}, Skipped: {skipped_master}")
    
    # Step 3: Migrate to Item_Price (for branch 00TR)
    print("\n3. Migrating to Item_Price (Branch: 00TR)...")
    inserted_price = 0
    skipped_price = 0
    
    for item in items:
        sku = item[0]
        r1, r2, w1, w2 = item[8], item[9], item[10], item[11]
        package_size = item[12]
        alternate_name = item[13]
        
        # Skip if no price data
        if not any([r1, r2, w1, w2]):
            continue
        
        # Check if already exists
        cursor.execute("""
            SELECT COUNT(*) FROM Item_Price 
            WHERE SKU = ? AND BranchCode = ?
        """, (sku, "00TR"))
        
        if cursor.fetchone()[0] > 0:
            skipped_price += 1
            continue
        
        # Insert into Item_Price
        try:
            cursor.execute("""
                INSERT INTO Item_Price (
                    SKU, BranchCode, R1, R2, W1, W2, 
                    PackageSize, AlternateName, UpdatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sku,
                "00TR",  # Default branch
                r1 or 0,
                r2 or 0,
                w1 or 0,
                w2 or 0,
                package_size or 1,
                alternate_name,
                datetime.now()
            ))
            inserted_price += 1
        except Exception as e:
            print(f"   Error inserting price for {sku}: {e}")
    
    conn.commit()
    print(f"   Inserted: {inserted_price}, Skipped: {skipped_price}")
    
    # Step 4: Summary
    print("\n" + "="*60)
    print("Migration Summary")
    print("="*60)
    print(f"Item_Master: {inserted_master} inserted, {skipped_master} skipped")
    print(f"Item_Price:  {inserted_price} inserted, {skipped_price} skipped")
    print("="*60)
    
    conn.close()
    print("\n✅ Migration completed successfully!")


if __name__ == "__main__":
    try:
        migrate_items()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
