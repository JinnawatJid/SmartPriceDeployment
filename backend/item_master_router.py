"""
Item Master Query API Router

This router provides endpoints for querying Item Master data with prices and inventory.

Endpoints:
- GET /items/{sku} - Get full item details by SKU or No_2
- GET /items - List items with filtering and pagination
"""

import logging
from typing import Optional, List
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel

from config.db_mssql import get_mssql_conn
from api.bc_item_client import BCAPIClient
from services.inventory_query_service import InventoryQueryService, InventoryByBranch


# Configure logging
logger = logging.getLogger(__name__)


# Initialize router
router = APIRouter(prefix="/items", tags=["Item Master"])


# Response models
class PriceData(BaseModel):
    """Price data for an item"""
    sdm: Optional[float] = None
    r2: Optional[float] = None
    r1: Optional[float] = None
    w2: Optional[float] = None
    w1: Optional[float] = None
    updated_at: Optional[str] = None


class InventoryData(BaseModel):
    """Inventory data for a branch"""
    branch: str
    quantity: float


class ItemDetail(BaseModel):
    """Full item details with master data, prices, and inventory"""
    sku: str
    sku2: str  # no_2
    name: str  # description
    unit: str  # base_unit_of_measure
    category: str  # inventory_posting_group
    product_group: str
    product_sub_group: str
    re: float  # unit cost
    prices: Optional[PriceData] = None
    inventory: List[InventoryData] = []


class ItemSummary(BaseModel):
    """Item summary for list view (no inventory)"""
    sku: str
    sku2: str
    name: str
    category: str
    product_group: str
    product_sub_group: str
    prices: Optional[PriceData] = None


class ItemListResponse(BaseModel):
    """Response for item list endpoint"""
    items: List[ItemSummary]
    total: int
    limit: int
    offset: int


# Initialize services (lazy initialization)
_api_client = None
_inventory_service = None


def get_api_client() -> BCAPIClient:
    """Get or create BC API Client instance"""
    global _api_client
    if _api_client is None:
        _api_client = BCAPIClient()
    return _api_client


def get_inventory_service() -> InventoryQueryService:
    """Get or create Inventory Query Service instance"""
    global _inventory_service
    if _inventory_service is None:
        api_client = get_api_client()
        _inventory_service = InventoryQueryService(api_client)
    return _inventory_service



@router.get("/{sku}", response_model=ItemDetail)
def get_item_detail(
    sku: str,
    branch_code: str = QueryParam(..., description="Branch code to filter prices and inventory")
):
    """
    Get full item details including master data, prices, and inventory.
    
    Supports querying by either SKU or No_2 field.
    
    Args:
        sku: Item SKU or No_2 to query
    
    Returns:
        ItemDetail object with all fields
    
    Raises:
        HTTPException 404: When SKU not found in Item_Master
    """
    logger.info(f"Fetching item detail for SKU: {sku}")
    
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        # Query Item_Master by SKU or No_2, left join with Item_Price filtered by branch
        query = """
            SELECT 
                im.SKU,
                im.No_2,
                im.Description,
                im.Base_Unit_of_Measure,
                im.Inventory_Posting_Group,
                im.Product_Group,
                im.Product_Sub_Group,
                im.RE,
                ip.SDM,
                ip.R2,
                ip.R1,
                ip.W2,
                ip.W1,
                ip.UpdatedAt
            FROM Item_Master im
            LEFT JOIN Item_Price ip ON im.SKU = ip.SKU AND ip.BranchCode = ?
            WHERE im.SKU = ? OR im.No_2 = ?
        """
        
        cursor.execute(query, (branch_code, sku, sku))
        row = cursor.fetchone()
        
        # Check if item exists
        if not row:
            logger.warning(f"Item not found: {sku}")
            raise HTTPException(status_code=404, detail=f"Item not found: {sku}")
        
        # Parse item master data
        item_sku = row[0] or ""
        no_2 = row[1] or ""
        description = row[2] or ""
        base_unit = row[3] or ""
        category = row[4] or ""
        product_group = row[5] or ""
        product_sub_group = row[6] or ""
        re = float(row[7]) if row[7] is not None else 0.0
        
        # Parse price data (may be null if no price record)
        prices = None
        if row[8] is not None:  # SDM field
            prices = PriceData(
                sdm=float(row[8]) if row[8] is not None else None,
                r2=float(row[9]) if row[9] is not None else None,
                r1=float(row[10]) if row[10] is not None else None,
                w2=float(row[11]) if row[11] is not None else None,
                w1=float(row[12]) if row[12] is not None else None,
                updated_at=row[13].isoformat() if row[13] is not None else None
            )
        
        # Fetch real-time inventory filtered by branch
        inventory_service = get_inventory_service()
        try:
            inventory_list = inventory_service.get_inventory(item_sku)
            # Filter inventory by requested branch only
            inventory_data = [
                InventoryData(branch=inv.branch, quantity=inv.quantity)
                for inv in inventory_list
                if inv.branch == branch_code
            ]
        except Exception as e:
            logger.error(f"Failed to fetch inventory for SKU {item_sku}: {str(e)}")
            # Return empty inventory on error (graceful degradation)
            inventory_data = []
        
        # Build response
        item_detail = ItemDetail(
            sku=item_sku,
            sku2=no_2,
            name=description,
            unit=base_unit,
            category=category,
            product_group=product_group,
            product_sub_group=product_sub_group,
            re=re,
            prices=prices,
            inventory=inventory_data
        )
        
        logger.info(f"Successfully fetched item detail for SKU: {sku}")
        return item_detail
    
    finally:
        cursor.close()
        conn.close()



@router.get("", response_model=ItemListResponse)
def list_items(
    branch_code: str = QueryParam(..., description="Branch code to filter prices"),
    category: Optional[str] = QueryParam(None, description="Filter by Inventory_Posting_Group"),
    product_group: Optional[str] = QueryParam(None, description="Filter by Product_Group"),
    search: Optional[str] = QueryParam(None, description="Search in SKU, No_2, Description"),
    limit: int = QueryParam(50, ge=1, le=1000, description="Number of items to return"),
    offset: int = QueryParam(0, ge=0, description="Number of items to skip")
):
    """
    List items with filtering and pagination.
    
    Supports filtering by:
    - category (Inventory_Posting_Group)
    - product_group (Product_Group)
    - search (SKU, No_2, Description using LIKE)
    
    Results are ordered by SKU ascending.
    
    Args:
        category: Filter by Inventory_Posting_Group
        product_group: Filter by Product_Group
        search: Search term for SKU, No_2, Description
        limit: Number of items to return (default: 50, max: 1000)
        offset: Number of items to skip (default: 0)
    
    Returns:
        ItemListResponse with items array and total count
    """
    logger.info(
        f"Listing items: category={category}, product_group={product_group}, "
        f"search={search}, limit={limit}, offset={offset}"
    )
    
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        # Build WHERE clause dynamically
        where_clauses = []
        params = []
        
        if category:
            where_clauses.append("im.Inventory_Posting_Group = ?")
            params.append(category)
        
        if product_group:
            where_clauses.append("im.Product_Group = ?")
            params.append(product_group)
        
        if search:
            # Search in SKU, No_2, and Description using LIKE
            where_clauses.append(
                "(im.SKU LIKE ? OR im.No_2 LIKE ? OR im.Description LIKE ?)"
            )
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        # Query total count
        count_query = f"""
            SELECT COUNT(*)
            FROM Item_Master im
            {where_clause}
        """
        
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Query items with pagination (filter prices by branch)
        items_query = f"""
            SELECT 
                im.SKU,
                im.No_2,
                im.Description,
                im.Inventory_Posting_Group,
                im.Product_Group,
                im.Product_Sub_Group,
                ip.SDM,
                ip.R2,
                ip.R1,
                ip.W2,
                ip.W1,
                ip.UpdatedAt
            FROM Item_Master im
            LEFT JOIN Item_Price ip ON im.SKU = ip.SKU AND ip.BranchCode = ?
            {where_clause}
            ORDER BY im.SKU ASC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """
        
        # Add branch_code and pagination parameters
        query_params = [branch_code] + params + [offset, limit]
        
        cursor.execute(items_query, query_params)
        rows = cursor.fetchall()
        
        # Build item summaries
        items = []
        for row in rows:
            item_sku = row[0] or ""
            no_2 = row[1] or ""
            description = row[2] or ""
            category_val = row[3] or ""
            product_group_val = row[4] or ""
            product_sub_group = row[5] or ""
            
            # Parse price data (may be null)
            prices = None
            if row[6] is not None:  # SDM field
                prices = PriceData(
                    sdm=float(row[6]) if row[6] is not None else None,
                    r2=float(row[7]) if row[7] is not None else None,
                    r1=float(row[8]) if row[8] is not None else None,
                    w2=float(row[9]) if row[9] is not None else None,
                    w1=float(row[10]) if row[10] is not None else None,
                    updated_at=row[11].isoformat() if row[11] is not None else None
                )
            
            item_summary = ItemSummary(
                sku=item_sku,
                sku2=no_2,
                name=description,
                category=category_val,
                product_group=product_group_val,
                product_sub_group=product_sub_group,
                prices=prices
            )
            items.append(item_summary)
        
        logger.info(
            f"Successfully fetched {len(items)} items (total: {total_count})"
        )
        
        return ItemListResponse(
            items=items,
            total=total_count,
            limit=limit,
            offset=offset
        )
    
    finally:
        cursor.close()
        conn.close()
