# ============================================
# special_price_request_router.py
# API Router สำหรับคำขอราคาพิเศษ
# ============================================

from fastapi import APIRouter, HTTPException, Body, Query, Form, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import json
from typing import Optional, List
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
async def create_special_price_request(payload: dict = Body(...)):
    """
    สร้างคำขอราคาพิเศษใหม่
    """
    from fastapi import BackgroundTasks
    
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
        
        # สร้างคำขอ (เร็ว)
        result = create_request(payload)
        request_number = result["request_number"]
        
        # ส่งคำขอกลับทันที แล้วทำ PDF และ Email ใน background
        import threading
        
        def send_approval_email_background():
            """ทำงานใน background thread"""
            try:
                # ดึงข้อมูลคำขอ
                request_data = get_request_detail(request_number)
                
                # สร้าง PDF
                pdf_path = generate_special_price_request_pdf(request_data)
                print(f"✅ PDF generated: {pdf_path}")
                
                # สร้าง approval token
                token = generate_approval_token(request_number)
                print(f"✅ Token generated: {token[:20]}...")
                
                # ส่ง Email
                email_result = send_approval_request_with_links(request_data, pdf_path, token)
                
                if email_result["success"]:
                    print(f"✅ Email sent successfully for {request_number}")
                else:
                    print(f"❌ Email failed for {request_number}: {email_result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Background task error for {request_number}: {e}")
                import traceback
                traceback.print_exc()
        
        # เริ่ม background thread
        thread = threading.Thread(target=send_approval_email_background, daemon=True)
        thread.start()
        
        # ส่งผลลัพธ์กลับทันที
        return {
            "request_number": request_number,
            "status": result["status"],
            "email_sent": "processing",
            "message": "สร้างคำขอสำเร็จ กำลังส่ง Email..."
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
    อนุมัติคำขอราคาพิเศษผ่าน URL link - อนุมัติทันที
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
        
        # ⭐ อนุมัติทันที
        success = approve_request(request_number, "Approved via link")
        
        # Mark token as used
        mark_token_used(token)
        
        if success:
            return HTMLResponse(content=f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }}
                        .success {{ color: #28a745; font-size: 32px; margin-bottom: 20px; }}
                        .info {{ color: #495057; font-size: 18px; }}
                    </style>
                </head>
                <body>
                    <div class="success">✅ อนุมัติสำเร็จ</div>
                    <p class="info">เลขที่คำขอ: {request_number}</p>
                    <p class="info">คำขอราคาพิเศษได้รับการอนุมัติแล้ว</p>
                </body>
                </html>
            """)
        else:
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
                    <div class="error">❌ เกิดข้อผิดพลาดในการอนุมัติ</div>
                    <p>กรุณาลองใหม่อีกครั้ง</p>
                </body>
                </html>
            """, status_code=500)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error approving request: {str(e)}")


@router.post("/upload-approval-files/{request_number}", summary="อัปโหลดไฟล์สำหรับการอนุมัติ")
async def upload_approval_files(request_number: str, files: List[UploadFile] = File(...)):
    """
    อัปโหลดไฟล์ PDF สำหรับการอนุมัติ (ก่อนกดอนุมัติ)
    """
    from pathlib import Path
    from config.email_config import PDF_STORAGE_PATH
    
    try:
        # ตรวจสอบว่าคำขอมีอยู่จริง
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        if request_data["status"] != "pending":
            raise HTTPException(400, "Request is not pending")
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        PDF_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        
        # บันทึกไฟล์ที่อัปโหลด
        for file in files:
            if file.filename and file.filename.lower().endswith('.pdf'):
                # สร้างชื่อไฟล์ที่ไม่ซ้ำ
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{request_number}_approved_{timestamp}_{file.filename}"
                file_path = PDF_STORAGE_PATH / safe_filename
                
                # บันทึกไฟล์
                content = await file.read()
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # ⭐ เก็บแค่ชื่อไฟล์ (relative path) แทน absolute path
                uploaded_files.append(safe_filename)
                print(f"📎 Saved uploaded file: {safe_filename}")
        
        return {
            "success": True,
            "files_uploaded": len(uploaded_files),
            "files": uploaded_files  # ⭐ ส่งชื่อไฟล์กลับไปแทน Path object
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error uploading files: {str(e)}")


@router.post("/approve/{token}", summary="ประมวลผลการอนุมัติพร้อมไฟล์แนบ")
async def process_approval(token: str):
    """
    ประมวลผลการอนุมัติพร้อมรับไฟล์แนบ
    """
    from pathlib import Path
    from config.email_config import PDF_STORAGE_PATH
    
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
                </body>
                </html>
            """, status_code=400)
        
        # ดึงข้อมูลคำขอ
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        # บันทึกไฟล์ที่อัปโหลด
        pdf_files = []
        
        # ค้นหาไฟล์ที่แนบมาจาก email (ถ้ามี)
        if PDF_STORAGE_PATH.exists():
            pattern = f"{request_number}_approved_*.pdf"
            # ⭐ เก็บแค่ชื่อไฟล์ (relative path) แทน absolute path
            email_pdfs = [f.name for f in PDF_STORAGE_PATH.glob(pattern)]
            pdf_files.extend(email_pdfs)
            if email_pdfs:
                print(f"📧 Found {len(email_pdfs)} email-attached PDFs")
        
        # อนุมัติคำขอ
        approver_email = request_data.get("approver_email", "Unknown")
        success = approve_request(request_number, approver_email, pdf_files if pdf_files else None)
        
        if not success:
            raise HTTPException(500, "Failed to approve request")
        
        # ทำเครื่องหมายว่า token ถูกใช้แล้ว
        mark_token_used(token)
        
        # ส่ง Email แจ้งผล
        send_approval_notification(request_data)
        
        # แสดงรายการไฟล์ที่แนบ
        attachment_html = ""
        if pdf_files:
            attachment_html = f"""
                <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                    <p style="margin: 0 0 10px 0; font-weight: bold;">📎 ไฟล์ที่แนบ ({len(pdf_files)} ไฟล์):</p>
                    <ul style="margin: 0; padding-left: 20px; text-align: left;">
                        {''.join([f'<li>{f}</li>' for f in pdf_files])}
                    </ul>
                </div>
            """
        
        return HTMLResponse(content=f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Sarabun', Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #28a745; font-size: 32px; margin-bottom: 20px; }}
                    .info {{ font-size: 18px; color: #495057; max-width: 600px; margin: 0 auto; }}
                </style>
            </head>
            <body>
                <div class="success">✅ อนุมัติคำขอสำเร็จ</div>
                <div class="info">
                    <p>เลขที่คำขอ: <strong>{request_number}</strong></p>
                    <p>ผู้อนุมัติ: <strong>{approver_email}</strong></p>
                    <p>วันที่อนุมัติ: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
                    {attachment_html}
                </div>
                <p style="margin-top: 30px; color: #6c757d;">คุณสามารถปิดหน้าต่างนี้ได้</p>
            </body>
            </html>
        """)
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error processing approval: {str(e)}")


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
        rejected_by = request_data.get("approver_email", "Unknown")
        success = reject_request(request_number, rejected_by, reason)
        
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
        "rejected_by": "ผู้จัดการสมหญิง",
        "rejection_reason": "ราคาต่ำเกินไป"
    }
    """
    try:
        rejected_by = payload.get("rejected_by", "")
        rejection_reason = payload.get("rejection_reason", "")
        
        if not rejected_by:
            raise HTTPException(400, "rejected_by is required")
        
        if not rejection_reason:
            raise HTTPException(400, "rejection_reason is required")
        
        success = reject_request(request_number, rejected_by, rejection_reason)
        
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
        for idx, filename in enumerate(pdf_files):
            # ⭐ สร้าง full path จากชื่อไฟล์
            file_path = PDF_STORAGE_PATH / filename
            if file_path.exists():
                result.append({
                    "filename": filename,
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
        
        # ⭐ สร้าง full path จากชื่อไฟล์
        filename = pdf_files[file_index]
        file_path = PDF_STORAGE_PATH / filename
        
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



