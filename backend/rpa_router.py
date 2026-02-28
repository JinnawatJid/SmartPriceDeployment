"""
RPA Router: API endpoint for triggering RPA script to create Sales Quote in D365 BC
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import subprocess
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
    external_doc_no: str  # เลขที่ใบเสนอราคาของเรา
    your_reference: str
    items: List[RPAItem]


@router.post("/api/rpa/create-quote")
async def create_quote_via_rpa(request: RPAQuoteRequest):
    """
    Trigger RPA script to create Sales Quote in D365 BC
    """
    try:
        # Get the project root directory (parent of backend)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)
        
        # Path to RPA script (in project root)
        rpa_script_path = os.path.join(project_root, "rpa_create_quote.py")
        temp_file_path = os.path.join(project_root, "rpa_temp_data.json")
        
        # เตรียมข้อมูลสำหรับ RPA script
        rpa_data = {
            "quote_code": request.quote_code,
            "customer_no": request.customer_no,
            "sales_admin": request.sales_admin,
            "external_doc_no": request.external_doc_no,
            "your_reference": request.your_reference,
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

        # บันทึกข้อมูลลง temp file
        with open(temp_file_path, "w", encoding="utf-8") as f:
            json.dump(rpa_data, f, ensure_ascii=False, indent=2)

        # เรียก RPA script (run from project root)
        result = subprocess.run(
            ["python", rpa_script_path, request.quote_code],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            cwd=project_root,  # Run from project root
        )

        # ลบ temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if result.returncode == 0:
            return {
                "success": True,
                "message": "RPA script executed successfully",
                "output": result.stdout,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": "RPA script failed",
                    "error": result.stderr,
                    "output": result.stdout,
                },
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="RPA script timeout (exceeded 5 minutes)",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute RPA script: {str(e)}",
        )
