# ============================================
# special_price_request_router.py
# API Router สำหรับคำขอราคาพิเศษ
# ============================================

from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.responses import FileResponse
from pathlib import Path
import json
from typing import Optional

from special_price_request.service import (
    create_request,
    get_requests,
    get_request_detail,
    approve_request,
    reject_request
)
from services.email_service import (
    send_approval_request,
    send_approval_notification,
    send_rejection_notification
)
from special_price_request.pdf_service import generate_special_price_request_pdf
from config.email_config import PDF_STORAGE_PATH


router = APIRouter(prefix="/special-price-requests", tags=["special-price-requests"])


@router.post("", summary="สร้างคำขอราคาพิเศษใหม่")
def create_special_price_request(payload: dict = Body(...)):
    """
    สร้างคำขอราคาพิเศษใหม่
    
    Request Body:
    {
        "quote_no": "BSQT-2501/0001",
        "customer_code": "C001",
        "customer_name": "บริษัท ABC",
        "requester_name": "สมชาย ใจดี",
        "requester_phone": "081-234-5678",
        "request_reason": "ลูกค้าเป็น VIP",
        "original_total": 15000.00,
        "requested_total": 12000.00,
        "approver_email": "manager@company.com",
        "branch": "สาขากรุงเทพ",
        "valid_from": "2025-02-01",
        "valid_to": "2025-03-31",
        "items": [
            {
                "item_code": "A010010100101",
                "item_name": "อลูมิเนียม",
                "quantity": 100,
                "unit": "เมตร",
                "w1_price": 150.00,
                "requested_price": 120.00
            }
        ]
    }
    """
    try:
        # Validate required fields
        required_fields = [
            "quote_no", "requester_name",
            "request_reason", "original_total", "requested_total",
            "approver_email", "items"
        ]
        
        for field in required_fields:
            if field not in payload or not payload[field]:
                raise HTTPException(400, f"Missing required field: {field}")
        
        # Validate items
        if not isinstance(payload["items"], list) or len(payload["items"]) == 0:
            raise HTTPException(400, "Items must be a non-empty array")
        
        # สร้างคำขอ
        result = create_request(payload)
        
        # ดึงข้อมูลคำขอที่สร้างเสร็จ
        request_data = get_request_detail(result["request_number"])
        
        # สร้าง PDF
        pdf_path = generate_special_price_request_pdf(request_data)
        
        # ส่ง Email
        email_result = send_approval_request(request_data, pdf_path)
        
        if not email_result["success"]:
            # ถ้าส่ง Email ไม่สำเร็จ แต่ยังคงสร้างคำขอไว้
            return {
                "request_number": result["request_number"],
                "status": result["status"],
                "email_sent": False,
                "email_error": email_result.get("error"),
                "message": "สร้างคำขอสำเร็จ แต่ส่ง Email ไม่สำเร็จ"
            }
        
        return {
            "request_number": result["request_number"],
            "status": result["status"],
            "email_sent": True,
            "message": "ส่งคำขอราคาพิเศษสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error creating request: {str(e)}")


@router.get("", summary="ดึงรายการคำขอราคาพิเศษ")
def list_special_price_requests(
    status: Optional[str] = Query(None, description="pending, approved, rejected, all"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    ดึงรายการคำขอราคาพิเศษทั้งหมด
    """
    try:
        result = get_requests(status=status, limit=limit, offset=offset)
        return result
    except Exception as e:
        raise HTTPException(500, f"Error fetching requests: {str(e)}")


@router.get("/{request_number}", summary="ดึงรายละเอียดคำขอ")
def get_special_price_request_detail(request_number: str):
    """
    ดึงรายละเอียดคำขอราคาพิเศษ
    """
    try:
        result = get_request_detail(request_number)
        
        if not result:
            raise HTTPException(404, f"Request {request_number} not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching request detail: {str(e)}")


@router.get("/{request_number}/pdf", summary="ดาวน์โหลด PDF")
def download_special_price_request_pdf(request_number: str):
    """
    ดาวน์โหลด PDF ของคำขอราคาพิเศษ
    """
    try:
        pdf_path = PDF_STORAGE_PATH / f"{request_number}.pdf"
        
        if not pdf_path.exists():
            raise HTTPException(404, "PDF file not found")
        
        return FileResponse(
            path=pdf_path,
            filename=f"{request_number}.pdf",
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error downloading PDF: {str(e)}")


@router.post("/{request_number}/approve", summary="อนุมัติคำขอ")
def approve_special_price_request(
    request_number: str,
    payload: dict = Body(...)
):
    """
    อนุมัติคำขอราคาพิเศษ
    
    Request Body:
    {
        "approved_by": "ผู้จัดการสมหญิง"
    }
    """
    try:
        approved_by = payload.get("approved_by", "")
        
        if not approved_by:
            raise HTTPException(400, "approved_by is required")
        
        success = approve_request(request_number, approved_by)
        
        if not success:
            raise HTTPException(404, f"Request {request_number} not found or already processed")
        
        # ดึงข้อมูลคำขอ
        request_data = get_request_detail(request_number)
        
        # ส่ง Email แจ้งผล
        send_approval_notification(request_data)
        
        return {
            "request_number": request_number,
            "status": "approved",
            "message": "อนุมัติคำขอสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error approving request: {str(e)}")


@router.post("/{request_number}/reject", summary="ปฏิเสธคำขอ")
def reject_special_price_request(
    request_number: str,
    payload: dict = Body(...)
):
    """
    ปฏิเสธคำขอราคาพิเศษ
    
    Request Body:
    {
        "rejection_reason": "ราคาต่ำเกินไป"
    }
    """
    try:
        rejection_reason = payload.get("rejection_reason", "")
        
        if not rejection_reason:
            raise HTTPException(400, "rejection_reason is required")
        
        success = reject_request(request_number, rejection_reason)
        
        if not success:
            raise HTTPException(404, f"Request {request_number} not found or already processed")
        
        # ดึงข้อมูลคำขอ
        request_data = get_request_detail(request_number)
        
        # ส่ง Email แจ้งผล
        send_rejection_notification(request_data)
        
        return {
            "request_number": request_number,
            "status": "rejected",
            "message": "ปฏิเสธคำขอสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error rejecting request: {str(e)}")



@router.get("/{request_number}/approval-pdfs", summary="ดาวน์โหลด PDF ที่ผู้อนุมัติแนบมา")
def download_approval_pdfs(request_number: str):
    """
    ดาวน์โหลดรายการ PDF ที่ผู้อนุมัติแนบมากับ email
    
    Returns:
    {
        "request_number": "SP-250130-0001",
        "pdf_files": [
            {
                "filename": "SP-250130-0001_approved_20250130_143022.pdf",
                "download_url": "/api/special-price-requests/SP-250130-0001/approval-pdfs/0"
            }
        ]
    }
    """
    try:
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, f"Request {request_number} not found")
        
        # ดึงรายการไฟล์ PDF
        pdf_files_json = request_data.get("approval_pdf_files")
        
        if not pdf_files_json:
            return {
                "request_number": request_number,
                "pdf_files": []
            }
        
        pdf_files = json.loads(pdf_files_json)
        
        # สร้าง response
        result = []
        for idx, file_path in enumerate(pdf_files):
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                result.append({
                    "filename": file_path_obj.name,
                    "download_url": f"/api/special-price-requests/{request_number}/approval-pdfs/{idx}"
                })
        
        return {
            "request_number": request_number,
            "pdf_files": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching approval PDFs: {str(e)}")


@router.get("/{request_number}/approval-pdfs/{file_index}", summary="ดาวน์โหลดไฟล์ PDF ที่ผู้อนุมัติแนบมา")
def download_approval_pdf_file(request_number: str, file_index: int):
    """
    ดาวน์โหลดไฟล์ PDF ที่ผู้อนุมัติแนบมา (ตาม index)
    """
    try:
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, f"Request {request_number} not found")
        
        # ดึงรายการไฟล์ PDF
        pdf_files_json = request_data.get("approval_pdf_files")
        
        if not pdf_files_json:
            raise HTTPException(404, "No approval PDFs found")
        
        pdf_files = json.loads(pdf_files_json)
        
        if file_index < 0 or file_index >= len(pdf_files):
            raise HTTPException(404, "Invalid file index")
        
        file_path = Path(pdf_files[file_index])
        
        if not file_path.exists():
            raise HTTPException(404, "PDF file not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error downloading approval PDF: {str(e)}")
