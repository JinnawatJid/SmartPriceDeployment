# credit_router.py
from fastapi import APIRouter, HTTPException
import httpx
from config.config_external_api import CREDIT_API_URL, CREDIT_API_HEADERS
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/credit-status/{customer_id}")
async def get_credit_status(customer_id: str):
    """
    ดึงข้อมูลเครดิตของลูกค้าจาก External API
    
    Args:
        customer_id: รหัสลูกค้า
    
    Returns:
        {
            "customer_id": "0100ZTR",
            "customer_name": "Mock Customer (N Scomartr)",
            "status": "N",
            "credit_limit": 500000,
            "credit_terms": {
                "ga": 60,
                "yc": 45
            },
            "updated_at": "2024-02-29T12:48:51.3992"
        }
    """
    try:
        # สร้าง URL สำหรับเรียก External API
        url = f"{CREDIT_API_URL}/api/external/credit-status/{customer_id}"
        
        logger.info(f"🔍 [CREDIT API] Calling: {url}")
        logger.info(f"🔍 [CREDIT API] Headers: {CREDIT_API_HEADERS}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers=CREDIT_API_HEADERS
            )
            
            logger.info(f"🔍 [CREDIT API] Response status: {response.status_code}")
            logger.info(f"🔍 [CREDIT API] Response body: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✅ [CREDIT API] Success! Data: {data}")
            return data
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from credit API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Credit API error: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error to credit API: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to credit API: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_credit_status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
