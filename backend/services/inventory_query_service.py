"""
Inventory Query Service

This service provides real-time inventory data from Business Central Item Ledger API
with caching to reduce API calls.

Features:
- Real-time inventory queries by SKU
- In-memory caching with 60-second TTL
- Aggregation by branch code
- Timeout handling (5 seconds via BC API Client)
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

from cachetools import TTLCache

# Import BC API Client
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.bc_item_client import BCAPIClient


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class InventoryByBranch:
    """Inventory data for a specific branch"""
    branch: str
    quantity: float


class InventoryQueryService:
    """
    Service for querying real-time inventory with caching.
    
    Uses BC Item Ledger API to fetch inventory data and aggregates by branch.
    Results are cached for 60 seconds to reduce API load.
    """
    
    def __init__(
        self,
        api_client: BCAPIClient,
        cache_ttl: int = 60,
        cache_maxsize: int = 1000
    ):
        """
        Initialize Inventory Query Service.
        
        Args:
            api_client: BC API Client instance for making API calls
            cache_ttl: Cache time-to-live in seconds (default: 60)
            cache_maxsize: Maximum number of items in cache (default: 1000)
        """
        self.api_client = api_client
        self.cache_ttl = cache_ttl
        
        # Initialize TTL cache (automatically expires entries after TTL)
        self.cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        
        logger.info(
            f"Inventory Query Service initialized with cache TTL: {cache_ttl}s, "
            f"max size: {cache_maxsize}"
        )
    
    def get_inventory(self, sku: str) -> List[InventoryByBranch]:
        """
        Get inventory for SKU grouped by branch.
        
        This method:
        1. Checks cache first, returns if hit
        2. Queries BC Ledger API with SKU filter
        3. Aggregates Quantity by Branch_Code (sum quantities for each branch)
        4. Handles empty results (returns empty list)
        5. Caches results before returning
        6. Handles timeout (5 seconds - configured in BC API Client)
        
        Args:
            sku: Item SKU to query
        
        Returns:
            List of InventoryByBranch objects with branch and quantity
            Returns empty list if no inventory found
        
        Raises:
            AuthenticationError: When API key is invalid
            ClientError: When API returns 4xx error
            ServerError: When API returns 5xx error after retries
            NetworkError: When network request fails (including timeout)
        """
        # Check cache first
        cache_key = f"inventory:{sku}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for SKU: {sku}")
            return self.cache[cache_key]
        
        logger.debug(f"Cache miss for SKU: {sku}, querying API")
        
        # Fetch from API and aggregate
        inventory_list = self._fetch_and_aggregate(sku)
        
        # Cache the results
        self.cache[cache_key] = inventory_list
        logger.debug(f"Cached inventory for SKU: {sku} ({len(inventory_list)} branches)")
        
        return inventory_list
    
    def _fetch_and_aggregate(self, sku: str) -> List[InventoryByBranch]:
        """
        Fetch inventory from BC Ledger API and aggregate by branch.
        
        Args:
            sku: Item SKU to query
        
        Returns:
            List of InventoryByBranch objects aggregated by branch
        """
        try:
            # Fetch ledger entries from API
            ledger_entries = self.api_client.fetch_inventory(sku)
            
            # Handle empty results
            if not ledger_entries:
                logger.info(f"No inventory found for SKU: {sku}")
                return []
            
            # Aggregate quantities by branch
            branch_quantities = defaultdict(float)
            for entry in ledger_entries:
                branch_code = entry.get("Branch_Code", "")
                quantity = entry.get("Quantity", 0)
                
                # Convert quantity to float if it's not already
                try:
                    quantity = float(quantity)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid quantity value for SKU {sku}, "
                        f"Branch {branch_code}: {quantity}"
                    )
                    quantity = 0
                
                branch_quantities[branch_code] += quantity
            
            # Convert to list of InventoryByBranch objects
            inventory_list = [
                InventoryByBranch(branch=branch, quantity=qty)
                for branch, qty in branch_quantities.items()
            ]
            
            logger.info(
                f"Fetched inventory for SKU: {sku} - "
                f"{len(inventory_list)} branches, "
                f"total quantity: {sum(inv.quantity for inv in inventory_list)}"
            )
            
            return inventory_list
        
        except Exception as e:
            logger.error(f"Error fetching inventory for SKU {sku}: {str(e)}")
            raise
    
    def clear_cache(self, sku: Optional[str] = None):
        """
        Clear cache for specific SKU or entire cache.
        
        Args:
            sku: SKU to clear from cache (if None, clears entire cache)
        """
        if sku:
            cache_key = f"inventory:{sku}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.info(f"Cleared cache for SKU: {sku}")
        else:
            self.cache.clear()
            logger.info("Cleared entire inventory cache")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache size and TTL info
        """
        return {
            "current_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl_seconds": self.cache_ttl
        }
