"""
RPA Router: API endpoint for triggering RPA script to create Sales Quote in D365 BC
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os

router = APIRouter()


class RPAItem(BaseModel):
    sku: str
    description: str
    quantity: str
    unit_price: Optional[str] = None
    price_per_sqft: Optional[str] = None
    price_per_sheet: Optional[str] = None


class RPAQuoteRequest(BaseModel):
    quote_code: str  # e.g., "TRQT"
    customer_no: str
    sales_admin: str
    your_reference: str  # เลขที่ใบเสนอราคาของเรา
    remote_chrome_address: Optional[str] = "127.0.0.1:9222"  # ⭐ รองรับ remote Chrome
    items: List[RPAItem]


@router.post("/api/rpa/create-quote")
async def create_quote_via_rpa(request: RPAQuoteRequest):
    """
    Trigger RPA script to create Sales Quote in D365 BC
    """
    import logging
    import sys
    logger = logging.getLogger(__name__)
    
    try:
        print("\n" + "="*60)
        print("RPA REQUEST RECEIVED")
        print(f"Quote Code: {request.quote_code}")
        print(f"Customer: {request.customer_no}")
        print(f"Chrome Address: {request.remote_chrome_address}")
        print(f"Items Count: {len(request.items)}")
        print("="*60 + "\n")
        
        logger.info("="*60)
        logger.info("RPA Request Received")
        logger.info(f"Quote Code: {request.quote_code}")
        logger.info(f"Customer: {request.customer_no}")
        logger.info(f"Chrome Address: {request.remote_chrome_address}")
        logger.info(f"Items Count: {len(request.items)}")
        logger.info("="*60)
        
        # เตรียมข้อมูลสำหรับ RPA
        rpa_data = {
            "quote_code": request.quote_code,
            "customer_no": request.customer_no,
            "sales_admin": request.sales_admin,
            "your_reference": request.your_reference,
            "remote_chrome_address": request.remote_chrome_address,
            "items": [
                {
                    "item_code": item.sku,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "price_per_sqft": item.price_per_sqft,
                    "price_per_sheet": item.price_per_sheet,
                }
                for item in request.items
            ],
        }

        # ⭐ Import และเรียกใช้ RPA function โดยตรง
        # Import จาก backend.rpa_create_quote เพราะไฟล์อยู่ใน backend/ แล้ว
        try:
            print("Importing RPA module...")
            logger.info("Importing RPA module...")
            
            # Import RPA module from same directory (backend/)
            import rpa_create_quote
            
            print("RPA module imported successfully")
            logger.info("RPA module imported successfully")
            
            # เรียกใช้ function create_sales_quote โดยตรง
            print("Executing RPA function...")
            logger.info("Executing RPA function...")
            
            rpa_create_quote.create_sales_quote(request.quote_code, rpa_data)
            
            print("RPA function completed successfully")
            logger.info("RPA function completed successfully")
            
            return {
                "success": True,
                "message": "RPA executed successfully",
                "output": "Sales Quote created in D365 BC"
            }
            
        except Exception as rpa_error:
            error_msg = str(rpa_error)
            print(f"[ERROR] RPA execution failed: {error_msg}")
            logger.error(f"RPA execution failed: {error_msg}", exc_info=True)
            
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": "RPA execution failed",
                    "error": error_msg,
                    "output": ""
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Failed to execute RPA: {error_msg}")
        logger.error(f"Failed to execute RPA: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute RPA script: {error_msg}",
        )
