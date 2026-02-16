"""
Admin Router

This router provides admin endpoints for price management.

Endpoints:
- POST /admin/prices/upload - Upload price file (CSV or Excel) and update Item_Price table
"""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query as QueryParam
from pydantic import BaseModel

from config.db_mssql import get_mssql_conn
from services.price_upload_service import PriceUploadService, ValidationError


# Configure logging
logger = logging.getLogger(__name__)


# Initialize router
router = APIRouter(prefix="/admin", tags=["Admin"])


# Response models
class UploadResponse(BaseModel):
    """Response for price upload endpoint"""
    success: bool
    message: str
    total_rows: int
    successful_updates: int
    errors: int
    error_details: list[str]


@router.post("/prices/upload", response_model=UploadResponse)
async def upload_prices(
    file: UploadFile = File(...),
    branch_code: str = QueryParam(..., description="Branch code for price data")
):
    """
    Upload price file (CSV or Excel) and update Item_Price table.
    
    Process:
    1. Validate file format (CSV, XLSX, XLS)
    2. Validate required columns (SKU, SDM, R2, R1, W2, W1)
    3. For each row:
       - Validate SKU exists in Item_Master
       - Upsert to Item_Price table (update if exists, insert if not)
       - Set UpdatedAt timestamp
    4. Return summary with total_rows, successful_updates, errors
    
    Args:
        file: Uploaded file (CSV or Excel)
        branch_code: Branch code for price data (e.g., "00TR", "05AY")
    
    Returns:
        UploadResponse with statistics and error details
    
    Raises:
        HTTPException 400: When file format is invalid or required columns missing
        HTTPException 500: When database operation fails
    """
    logger.info(f"Received price upload request for branch: {branch_code}")
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported: .csv, .xlsx, .xls"
        )
    
    # Save uploaded file to temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        logger.info(f"Saved uploaded file to: {temp_path}")
    
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Process upload using PriceUploadService
    try:
        conn = get_mssql_conn()
        service = PriceUploadService(conn)
        
        result = service.process_upload(temp_path, branch_code)
        
        conn.close()
        
        # Build response
        success = result.errors == 0
        message = (
            f"Successfully uploaded {result.successful_updates} prices"
            if success
            else f"Uploaded {result.successful_updates} prices with {result.errors} errors"
        )
        
        logger.info(
            f"Price upload completed: success={success}, "
            f"total={result.total_rows}, successful={result.successful_updates}, "
            f"errors={result.errors}"
        )
        
        return UploadResponse(
            success=success,
            message=message,
            total_rows=result.total_rows,
            successful_updates=result.successful_updates,
            errors=result.errors,
            error_details=result.error_details
        )
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Failed to process upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Removed temporary file: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {str(e)}")
