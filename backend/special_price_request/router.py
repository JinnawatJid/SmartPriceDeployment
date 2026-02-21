# ============================================
# special_price_request_router.py
# API Router สำหรับคำขอราคาพิเศษ
# ============================================

from fastapi import APIRouter, HTTPException, Body, Query, Form
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import json
from typing import Optional
from datetime import datetime

from special_price_request.service import (
    create_request,
    get_requests,
    get_request_detail,
    approve_request,
    reject_request
)
from services.email_service import (
    send_approval_request_with_links,
    send_approval_notification,
    send_rejection_notification
)
from special_price_request.pdf_service import generate_special_price_request_pdf
from special_price_request.approval_token import (
    generate_approval_token,
    validate_token,
    mark_token_used
)
from config.email_config import PDF_STORAGE_PATH


router = APIRouter(prefix="/special-price-requests", tags=["special-price-requests"])


@router.post("", summary="สร้างคำขอราคาพิเศษใหม่")
def create_special_price_request(payload: dict = Body(...)):
    """
    สร้างคำขอราคาพิเศษใหม่
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
        
        # สร้าง approval token
        try:
            token = generate_approval_token(result["request_number"])
        except Exception as e:
            raise HTTPException(500, f"Error generating token: {str(e)}")
        
        # ส่ง Email พร้อมลิงก์
        try:
            email_result = send_approval_request_with_links(request_data, pdf_path, token)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(500, f"Error sending email: {str(e)}")
        
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
    ถ้าไฟล์ไม่มี จะสร้างใหม่อัตโนมัติ
    """
    try:
        pdf_path = PDF_STORAGE_PATH / f"{request_number}.pdf"
        
        # ถ้าไฟล์ไม่มี ให้สร้างใหม่
        if not pdf_path.exists():
            print(f"📄 PDF not found, generating new one for {request_number}")
            
            # Get request data
            request_data = get_request_detail(request_number)
            
            if not request_data:
                raise HTTPException(404, f"Request {request_number} not found")
            
            # Generate PDF
            pdf_path = generate_special_price_request_pdf(request_data)
            print(f"✅ PDF generated: {pdf_path}")
        
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


@router.get("/approve/{token}", summary="อนุมัติคำขอผ่าน URL")
def approve_via_link(token: str):
    """
    อนุมัติคำขอราคาพิเศษผ่าน URL link
    """
    try:
        # ตรวจสอบ token
        request_number = validate_token(token)
        
        if not request_number:
            return HTMLResponse(content="""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }
                        .error { color: #dc3545; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <div class="error">❌ ลิงก์ไม่ถูกต้องหรือหมดอายุแล้ว</div>
                    <p>กรุณาติดต่อผู้ส่งคำขอเพื่อขอลิงก์ใหม่</p>
                </body>
                </html>
            """, status_code=400)
        
        # ดึงข้อมูลคำขอ
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        # ตรวจสอบสถานะ
        if request_data["status"] != "pending":
            status_text = "อนุมัติแล้ว" if request_data["status"] == "approved" else "ปฏิเสธแล้ว"
            return HTMLResponse(content=f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }}
                        .warning {{ color: #ffc107; font-size: 24px; }}
                    </style>
                </head>
                <body>
                    <div class="warning">⚠️ คำขอนี้ถูก{status_text}</div>
                    <p>เลขที่คำขอ: {request_number}</p>
                </body>
                </html>
            """)
        
        # อนุมัติคำขอ
        approver_email = request_data.get("approver_email", "Unknown")
        success = approve_request(request_number, approver_email)
        
        if not success:
            raise HTTPException(500, "Failed to approve request")
        
        # ทำเครื่องหมายว่า token ถูกใช้แล้ว
        mark_token_used(token)
        
        # ส่ง Email แจ้งผล
        send_approval_notification(request_data)
        
        return HTMLResponse(content=f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #28a745; font-size: 32px; margin-bottom: 20px; }}
                    .info {{ font-size: 18px; color: #495057; }}
                </style>
            </head>
            <body>
                <div class="success">✅ อนุมัติคำขอสำเร็จ</div>
                <div class="info">
                    <p>เลขที่คำขอ: <strong>{request_number}</strong></p>
                    <p>ผู้อนุมัติ: <strong>{approver_email}</strong></p>
                    <p>วันที่อนุมัติ: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                </div>
                <p style="margin-top: 30px; color: #6c757d;">คุณสามารถปิดหน้าต่างนี้ได้</p>
            </body>
            </html>
        """)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error approving request: {str(e)}")


@router.get("/reject/{token}", summary="หน้าฟอร์มปฏิเสธคำขอ")
def reject_form(token: str):
    """
    แสดงฟอร์มสำหรับปฏิเสธคำขอ
    """
    try:
        # ตรวจสอบ token
        request_number = validate_token(token)
        
        if not request_number:
            return HTMLResponse(content="""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }
                        .error { color: #dc3545; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <div class="error">❌ ลิงก์ไม่ถูกต้องหรือหมดอายุแล้ว</div>
                    <p>กรุณาติดต่อผู้ส่งคำขอเพื่อขอลิงก์ใหม่</p>
                </body>
                </html>
            """, status_code=400)
        
        # ดึงข้อมูลคำขอ
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        # ตรวจสอบสถานะ
        if request_data["status"] != "pending":
            status_text = "อนุมัติแล้ว" if request_data["status"] == "approved" else "ปฏิเสธแล้ว"
            return HTMLResponse(content=f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }}
                        .warning {{ color: #ffc107; font-size: 24px; }}
                    </style>
                </head>
                <body>
                    <div class="warning">⚠️ คำขอนี้ถูก{status_text}</div>
                    <p>เลขที่คำขอ: {request_number}</p>
                </body>
                </html>
            """)
        
        # แสดงฟอร์ม
        return HTMLResponse(content=f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Sarabun', Arial, sans-serif;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        background-color: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h2 {{
                        color: #dc3545;
                        text-align: center;
                    }}
                    .info {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    label {{
                        display: block;
                        margin-bottom: 10px;
                        font-weight: bold;
                        color: #495057;
                    }}
                    textarea {{
                        width: 100%;
                        padding: 10px;
                        border: 1px solid #ced4da;
                        border-radius: 5px;
                        font-family: 'Sarabun', Arial, sans-serif;
                        font-size: 16px;
                        resize: vertical;
                        box-sizing: border-box;
                    }}
                    button {{
                        width: 100%;
                        padding: 12px;
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        margin-top: 20px;
                    }}
                    button:hover {{
                        background-color: #c82333;
                    }}
                    button:disabled {{
                        background-color: #6c757d;
                        cursor: not-allowed;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>❌ ปฏิเสธคำขอราคาพิเศษ</h2>
                    
                    <div class="info">
                        <p><strong>เลขที่คำขอ:</strong> {request_number}</p>
                        <p><strong>ลูกค้า:</strong> {request_data.get('customer_name', 'N/A')}</p>
                        <p><strong>ผู้ขอ:</strong> {request_data['requester_name']}</p>
                    </div>
                    
                    <form id="rejectForm">
                        <label for="reason">เหตุผลในการปฏิเสธ: <span style="color: red;">*</span></label>
                        <textarea 
                            id="reason" 
                            name="reason" 
                            rows="5" 
                            required 
                            placeholder="กรุณาระบุเหตุผลในการปฏิเสธคำขอนี้..."
                        ></textarea>
                        
                        <button type="submit" id="submitBtn">ยืนยันการปฏิเสธ</button>
                    </form>
                </div>
                
                <script>
                    document.getElementById('rejectForm').addEventListener('submit', async (e) => {{
                        e.preventDefault();
                        
                        const reason = document.getElementById('reason').value.trim();
                        const submitBtn = document.getElementById('submitBtn');
                        
                        if (!reason) {{
                            alert('กรุณาระบุเหตุผล');
                            return;
                        }}
                        
                        submitBtn.disabled = true;
                        submitBtn.textContent = 'กำลังดำเนินการ...';
                        
                        try {{
                            const response = await fetch('/api/special-price-requests/reject/{token}', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                }},
                                body: 'reason=' + encodeURIComponent(reason)
                            }});
                            
                            if (response.ok) {{
                                const html = await response.text();
                                document.body.innerHTML = html;
                            }} else {{
                                alert('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง');
                                submitBtn.disabled = false;
                                submitBtn.textContent = 'ยืนยันการปฏิเสธ';
                            }}
                        }} catch (error) {{
                            alert('เกิดข้อผิดพลาด: ' + error.message);
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'ยืนยันการปฏิเสธ';
                        }}
                    }});
                </script>
            </body>
            </html>
        """)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error showing reject form: {str(e)}")


@router.post("/reject/{token}", summary="ปฏิเสธคำขอผ่าน URL")
def reject_via_link(token: str, reason: str = Form(...)):
    """
    ปฏิเสธคำขอราคาพิเศษผ่าน URL link
    """
    try:
        # ตรวจสอบ token
        request_number = validate_token(token)
        
        if not request_number:
            return HTMLResponse(content="""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }
                        .error { color: #dc3545; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <div class="error">❌ ลิงก์ไม่ถูกต้องหรือหมดอายุแล้ว</div>
                    <p>กรุณาติดต่อผู้ส่งคำขอเพื่อขอลิงก์ใหม่</p>
                </body>
                </html>
            """, status_code=400)
        
        # ดึงข้อมูลคำขอ
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        # ปฏิเสธคำขอ
        success = reject_request(request_number, reason)
        
        if not success:
            raise HTTPException(500, "Failed to reject request")
        
        # ทำเครื่องหมายว่า token ถูกใช้แล้ว
        mark_token_used(token)
        
        # ส่ง Email แจ้งผล
        send_rejection_notification(request_data)
        
        return HTMLResponse(content=f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #dc3545; font-size: 32px; margin-bottom: 20px; }}
                    .info {{ font-size: 18px; color: #495057; text-align: left; max-width: 600px; margin: 0 auto; }}
                </style>
            </head>
            <body>
                <div class="success">❌ ปฏิเสธคำขอสำเร็จ</div>
                <div class="info">
                    <p><strong>เลขที่คำขอ:</strong> {request_number}</p>
                    <p><strong>เหตุผล:</strong> {reason}</p>
                    <p><strong>วันที่ปฏิเสธ:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <p style="margin-top: 30px; color: #6c757d;">คุณสามารถปิดหน้าต่างนี้ได้</p>
            </body>
            </html>
        """)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error rejecting request: {str(e)}")


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
