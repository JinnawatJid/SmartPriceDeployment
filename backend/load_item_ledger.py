"""
Script to load Item Ledger Entries from API Gateway
and insert into SP683_ItemLedgerEntries table
"""

import requests
import os
from dotenv import load_dotenv
from config.db_mssql import get_mssql_conn
from datetime import datetime

# Load environment variables
load_dotenv()

def load_item_ledger_entries():
    """Load Item Ledger Entries from API Gateway and insert into database"""
    
    print("=" * 80)
    print("📦 Loading Item Ledger Entries from API Gateway")
    print("=" * 80)
    
    # Get API credentials from .env
    api_url = os.getenv('ITEMLEDGER_API_URL')
    api_key = os.getenv('ITEMLEDGER_API_KEY')
    
    if not api_url or not api_key:
        print("❌ Error: ITEMLEDGER_API_URL or ITEMLEDGER_API_KEY not found in .env")
        return
    
    print(f"\n🔗 API URL: {api_url}")
    
    # Request with API key
    try:
        print("\n📡 Fetching data from API Gateway...")
        response = requests.get(
            api_url,
            headers={
                'Accept': 'application/json',
                'apikey': api_key  # Use 'apikey' header like other APIs
            },
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict) and 'value' in data:
            entries = data['value']
        elif isinstance(data, list):
            entries = data
        else:
            print(f"❌ Unexpected response format: {type(data)}")
            return
        
        print(f"✅ Fetched {len(entries)} entries from API")
        
        if len(entries) == 0:
            print("⚠️ No data returned from API")
            return
        
        # Show sample entry
        print("\n📋 Sample entry:")
        sample = entries[0]
        for key in list(sample.keys())[:5]:
            print(f"  {key}: {sample[key]}")
        
        # Connect to database
        print("\n💾 Connecting to database...")
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # Clear existing data
        print("🗑️ Clearing existing data...")
        cursor.execute("DELETE FROM SP683_ItemLedgerEntries")
        conn.commit()
        
        # Insert data
        print(f"📥 Inserting {len(entries)} entries...")
        
        insert_sql = """
            INSERT INTO SP683_ItemLedgerEntries (
                Entry_No, Item_No, Description, Item_Brand, Item_Group,
                Entry_Type, Posting_Date, Document_No, Document_Type,
                Department_Code, Branch_Code, Location_Code, Bin_Code,
                Variant_Code, Quantity, SystemModifiedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        success_count = 0
        error_count = 0
        
        for entry in entries:
            try:
                # Parse date fields
                posting_date = None
                if entry.get('Posting_Date'):
                    try:
                        posting_date = datetime.fromisoformat(entry['Posting_Date'].replace('Z', '+00:00')).date()
                    except:
                        pass
                
                system_modified_at = None
                if entry.get('SystemModifiedAt'):
                    try:
                        system_modified_at = datetime.fromisoformat(entry['SystemModifiedAt'].replace('Z', '+00:00'))
                    except:
                        pass
                
                cursor.execute(insert_sql, (
                    entry.get('Entry_No'),
                    entry.get('Item_No'),
                    entry.get('Description'),
                    entry.get('Item_Brand'),
                    entry.get('Item_Group'),
                    entry.get('Entry_Type'),
                    posting_date,
                    entry.get('Document_No'),
                    entry.get('Document_Type'),
                    entry.get('Department_Code'),
                    entry.get('Branch_Code'),
                    entry.get('Location_Code'),
                    entry.get('Bin_Code'),
                    entry.get('Variant_Code'),
                    entry.get('Quantity'),
                    system_modified_at
                ))
                success_count += 1
                
                if success_count % 1000 == 0:
                    print(f"  ✓ Inserted {success_count} entries...")
                    conn.commit()
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Show first 5 errors only
                    print(f"  ❌ Error inserting entry {entry.get('Entry_No')}: {e}")
        
        conn.commit()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"✅ Successfully inserted: {success_count} entries")
        if error_count > 0:
            print(f"❌ Errors: {error_count} entries")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM SP683_ItemLedgerEntries")
        total = cursor.fetchone()[0]
        print(f"💾 Total entries in database: {total}")
        
        # Show branch distribution
        cursor.execute("""
            SELECT Branch_Code, COUNT(*) as cnt
            FROM SP683_ItemLedgerEntries
            WHERE Branch_Code IS NOT NULL
            GROUP BY Branch_Code
            ORDER BY cnt DESC
        """)
        
        print("\n📍 Branch Distribution:")
        for row in cursor.fetchall():
            branch = row[0]
            count = row[1]
            print(f"  {branch}: {count} entries")
        
        # Show item count per branch
        cursor.execute("""
            SELECT Branch_Code, COUNT(DISTINCT Item_No) as item_count
            FROM SP683_ItemLedgerEntries
            WHERE Branch_Code IS NOT NULL
            GROUP BY Branch_Code
            ORDER BY item_count DESC
        """)
        
        print("\n📦 Unique Items per Branch:")
        for row in cursor.fetchall():
            branch = row[0]
            count = row[1]
            print(f"  {branch}: {count} unique items")
        
        conn.close()
        print("\n✅ Data load completed!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_item_ledger_entries()
