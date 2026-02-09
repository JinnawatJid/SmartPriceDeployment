#!/usr/bin/env python
# populate_customer_cache.py
# Script to manually populate customer cache table

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobs.customer_cache_refresh import run_customer_cache_refresh

if __name__ == "__main__":
    print("=" * 60)
    print("Customer Cache Population Script")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Load all customers from D365 API")
    print("2. Calculate analytics for each customer")
    print("3. Insert/Update records in Customer table")
    print()
    print("⚠️  This may take 30-60 minutes for ~30,000 customers")
    print()
    
    response = input("Do you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)
    
    print()
    print("Starting customer cache refresh...")
    print()
    
    try:
        result = run_customer_cache_refresh()
        
        print()
        print("=" * 60)
        print("✅ COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Start Time: {result.start_time}")
        print(f"End Time: {result.end_time}")
        print(f"Duration: {result.duration_seconds:.2f} seconds ({result.duration_seconds/60:.2f} minutes)")
        print(f"Calculation Date: {result.calculation_date}")
        print()
        print(f"Customers Processed: {result.customers_processed}")
        print(f"Customers Updated: {result.customers_updated}")
        print(f"Customers Failed: {result.customers_failed}")
        print()
        if result.customers_processed > 0:
            print(f"Average Time per Customer: {result.avg_time_per_customer:.2f} seconds")
        print()
        
        if result.errors:
            print("Errors encountered:")
            for error in result.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(result.errors) > 10:
                print(f"  ... and {len(result.errors) - 10} more errors")
        
        print()
        print("You can now use the customer search API with database cache!")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"Failed to populate customer cache: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
