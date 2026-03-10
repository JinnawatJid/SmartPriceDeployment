"""
Item Master Cache Refresh Job
ดึงข้อมูล Item Master จาก D365 มาลง database
รันหลังจาก Invoice Cache และ Customer Cache เสร็จแล้ว
"""

import pyodbc
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from api.bc_item_client import BCAPIClient
from config.db_mssql import get_mssql_conn
from jobs.cache_logger import cache_logger

logger = logging.getLogger(__name__)


@dataclass
class ItemMasterRecord:
    """Item Master record structure"""
    SKU: str
    No_2: Optional[str] = None
    Description: Optional[str] = None
    Base_Unit_of_Measure: Optional[str] = None
    Product_Group: Optional[str] = None
    Product_Sub_Group: Optional[str] = None
    Variant_Mandatory: Optional[int] = None
    R1: Optional[float] = None
    R2: Optional[float] = None
    W1: Optional[float] = None
    W2: Optional[float] = None
    PackageSize: Optional[int] = None
    Product_Weight: Optional[float] = None
    AlternateName: Optional[str] = None
    Last_Updated: datetime = field(default_factory=datetime.now)


@dataclass
class ItemMasterJobResult:
    """Result of item master cache refresh job"""
    start_time: datetime
    end_time: datetime
    items_processed: int = 0
    items_inserted: int = 0
    items_updated: int = 0
    items_failed: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate job duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()


def parse_item_record(item_data: Dict) -> Optional[ItemMasterRecord]:
    """
    Parse item data from BC API response to ItemMasterRecord
    
    Args:
        item_data: Item data from BC API
    
    Returns:
        ItemMasterRecord or None if parsing fails
    """
    try:
        # Extract required fields
        sku = item_data.get("No") or item_data.get("SKU")
        if not sku:
            logger.warning(f"Item missing SKU: {item_data}")
            return None
        
        # Extract optional fields with defaults
        record = ItemMasterRecord(
            SKU=sku,
            No_2=item_data.get("No_2") or item_data.get("Alternate_Item_No"),
            Description=item_data.get("Description"),
            Base_Unit_of_Measure=item_data.get("Base_Unit_of_Measure"),
            Product_Group=item_data.get("Product_Group"),
            Product_Sub_Group=item_data.get("Product_Sub_Group"),
            Variant_Mandatory=item_data.get("Variant_Mandatory"),
            R1=item_data.get("R1") or item_data.get("Unit_Price"),
            R2=item_data.get("R2"),
            W1=item_data.get("W1"),
            W2=item_data.get("W2"),
            PackageSize=item_data.get("PackageSize") or item_data.get("Package_Size") or 1,
            Product_Weight=item_data.get("Product_Weight") or item_data.get("Weight"),
            AlternateName=item_data.get("AlternateName") or item_data.get("Alternate_Name"),
            Last_Updated=datetime.now()
        )
        
        return record
        
    except Exception as e:
        logger.error(f"Failed to parse item record: {e}", exc_info=True)
        return None


def upsert_item_batch(items: List[ItemMasterRecord], conn: pyodbc.Connection) -> tuple[int, int]:
    """
    Upsert items into Item_Master table (insert or update)
    
    Args:
        items: List of ItemMasterRecord to upsert
        conn: Database connection
    
    Returns:
        Tuple of (inserted_count, updated_count)
    """
    if not items:
        return 0, 0
    
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    
    try:
        for item in items:
            # Check if item exists
            cursor.execute(
                "SELECT COUNT(*) FROM Item_Master WHERE SKU = ?",
                (item.SKU,)
            )
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Update existing item
                cursor.execute("""
                    UPDATE Item_Master
                    SET 
                        No_2 = ?,
                        Description = ?,
                        Base_Unit_of_Measure = ?,
                        Product_Group = ?,
                        Product_Sub_Group = ?,
                        Variant_Mandatory = ?,
                        R1 = ?,
                        R2 = ?,
                        W1 = ?,
                        W2 = ?,
                        PackageSize = ?,
                        Product_Weight = ?,
                        AlternateName = ?,
                        Last_Updated = ?
                    WHERE SKU = ?
                """, (
                    item.No_2,
                    item.Description,
                    item.Base_Unit_of_Measure,
                    item.Product_Group,
                    item.Product_Sub_Group,
                    item.Variant_Mandatory,
                    item.R1,
                    item.R2,
                    item.W1,
                    item.W2,
                    item.PackageSize,
                    item.Product_Weight,
                    item.AlternateName,
                    item.Last_Updated,
                    item.SKU
                ))
                updated += 1
            else:
                # Insert new item
                cursor.execute("""
                    INSERT INTO Item_Master (
                        SKU, No_2, Description, Base_Unit_of_Measure,
                        Product_Group, Product_Sub_Group, Variant_Mandatory,
                        R1, R2, W1, W2, PackageSize, Product_Weight,
                        AlternateName, Last_Updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.SKU,
                    item.No_2,
                    item.Description,
                    item.Base_Unit_of_Measure,
                    item.Product_Group,
                    item.Product_Sub_Group,
                    item.Variant_Mandatory,
                    item.R1,
                    item.R2,
                    item.W1,
                    item.W2,
                    item.PackageSize,
                    item.Product_Weight,
                    item.AlternateName,
                    item.Last_Updated
                ))
                inserted += 1
        
        conn.commit()
        logger.info(f"Upserted items: {inserted} inserted, {updated} updated")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to upsert items: {e}", exc_info=True)
        raise
    finally:
        cursor.close()
    
    return inserted, updated


def run_item_master_cache_refresh() -> ItemMasterJobResult:
    """
    Main job function: ดึงข้อมูล Item Master จาก D365 มาลง database
    
    Returns:
        ItemMasterJobResult with job execution details
    """
    start_time = datetime.now()
    result = ItemMasterJobResult(start_time=start_time, end_time=start_time)
    
    try:
        cache_logger.info("=" * 80)
        cache_logger.info("🕐 Item Master Cache Refresh Started")
        cache_logger.info(f"   Triggered at: {start_time}")
        cache_logger.info("=" * 80)
        
        # Initialize BC API client
        try:
            bc_client = BCAPIClient()
        except ValueError as e:
            error_msg = f"Failed to initialize BC API client: {e}"
            logger.error(error_msg)
            cache_logger.error(error_msg)
            result.errors.append(error_msg)
            result.end_time = datetime.now()
            return result
        
        # Fetch items from BC API
        cache_logger.info("📥 Fetching items from D365...")
        try:
            items_data = bc_client.fetch_items(page=1, size=100)
            cache_logger.info(f"   Fetched {len(items_data)} items from D365")
        except Exception as e:
            error_msg = f"Failed to fetch items from BC API: {e}"
            logger.error(error_msg, exc_info=True)
            cache_logger.error(error_msg)
            result.errors.append(error_msg)
            result.end_time = datetime.now()
            return result
        
        # Parse items
        cache_logger.info("🔄 Parsing items...")
        parsed_items = []
        for item_data in items_data:
            parsed_item = parse_item_record(item_data)
            if parsed_item:
                parsed_items.append(parsed_item)
                result.items_processed += 1
            else:
                result.items_failed += 1
        
        cache_logger.info(f"   Parsed {result.items_processed} items, {result.items_failed} failed")
        
        # Upsert items to database
        if parsed_items:
            cache_logger.info("💾 Upserting items to database...")
            try:
                conn = get_mssql_conn()
                inserted, updated = upsert_item_batch(parsed_items, conn)
                conn.close()
                
                result.items_inserted = inserted
                result.items_updated = updated
                cache_logger.info(f"   Inserted: {inserted}, Updated: {updated}")
                
            except Exception as e:
                error_msg = f"Failed to upsert items to database: {e}"
                logger.error(error_msg, exc_info=True)
                cache_logger.error(error_msg)
                result.errors.append(error_msg)
        
        result.end_time = datetime.now()
        
        cache_logger.info("=" * 80)
        cache_logger.info("✅ Item Master Cache Refresh Completed")
        cache_logger.info(f"   Duration: {result.duration_seconds:.2f} seconds")
        cache_logger.info(f"   Processed: {result.items_processed}")
        cache_logger.info(f"   Inserted: {result.items_inserted}")
        cache_logger.info(f"   Updated: {result.items_updated}")
        cache_logger.info(f"   Failed: {result.items_failed}")
        if result.errors:
            cache_logger.info(f"   Errors: {len(result.errors)}")
            for error in result.errors:
                cache_logger.error(f"     - {error}")
        cache_logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in item master cache refresh: {e}", exc_info=True)
        cache_logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        result.errors.append(str(e))
        result.end_time = datetime.now()
        return result
