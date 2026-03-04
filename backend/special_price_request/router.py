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
from special_price_request.pdf_service import generate_special_price_request_pdf

# PDF Storage Path
PDF_STORAGE_PATH = Path(__file__).parent.parent / "data" / "special_price_pdfs"

router = APIRouter(prefix="/special-price-requests", tags=["special-price-requests"])


@router.post("", summary="สร้างคำขอราคาพิเศษใหม่")
async def create_special_price_request(payload: dict = Body(...)):
    """
    สร้างคำขอราคาพิเศษใหม่
    """
    try:
        # Validate required fields
        required_fields = [
            "quote_no", "requester_name",
            "request_reason", "original_total", "requested_total",
            "approver_employee_id", "items"
        ]
        
        for field in required_fields:
            if field not in payload or not payload[field]:
                raise HTTPException(400, f"Missing required field: {field}")
        
        # Validate items
        if not isinstance(payload["items"], list) or len(payload["items"]) == 0:
            raise HTTPException(400, "Items must be a non-empty array")
        
        # สร้างคำขอ
        result = create_request(payload)
        request_number = result["request_number"]
        
        # ส่งผลลัพธ์กลับทันที
        return {
            "request_number": request_number,
            "status": result["status"],
            "message": "สร้างคำขอสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error creating request: {str(e)}")


@router.get("", summary="ดึงรายการคำขอราคาพิเศษ")
def list_special_price_requests(
    status: Optional[str] = Query(None, description="pending, approved, rejected, all"),
    approver_employee_id: Optional[str] = Query(None, description="รหัสพนักงานผู้อนุมัติ"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    ดึงรายการคำขอราคาพิเศษทั้งหมด
    ถ้าระบุ approver_employee_id จะแสดงเฉพาะคำขอที่ส่งมาหาพนักงานคนนั้น
    """
    try:
        result = get_requests(
            status=status, 
            approver_employee_id=approver_employee_id,
            limit=limit, 
            offset=offset
        )
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
        
        return {
            "request_number": request_number,
            "status": "approved",
            "message": "อนุมัติคำขอสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error approving request: {str(e)}")





@router.post("/{request_number}/upload-approval-files", summary="อัปโหลดไฟล์สำหรับการอนุมัติ")
async def upload_approval_files(request_number: str, files: List[UploadFile] = File(...)):
    """
    อัปโหลดไฟล์ PDF/เอกสารสำหรับการอนุมัติ
    """
    import json
    
    print(f"\n{'='*60}")
    print(f"📤 UPLOAD FILES REQUEST")
    print(f"Request Number: {request_number}")
    print(f"Files Count: {len(files)}")
    print(f"PDF Storage Path: {PDF_STORAGE_PATH}")
    print(f"{'='*60}\n")
    
    try:
        # ตรวจสอบว่าคำขอมีอยู่จริง
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        if request_data["status"] != "pending":
            raise HTTPException(400, "Request is not pending")
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        PDF_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        print(f"✅ PDF Storage Path exists: {PDF_STORAGE_PATH.exists()}")
        
        uploaded_files = []
        
        # บันทึกไฟล์ที่อัปโหลด
        for file in files:
            if file.filename:
                # สร้างชื่อไฟล์ที่ไม่ซ้ำ
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = f"{request_number}_{timestamp}_{file.filename}"
                file_path = PDF_STORAGE_PATH / safe_filename
                
                print(f"📝 Processing file: {file.filename}")
                print(f"   Safe filename: {safe_filename}")
                print(f"   Full path: {file_path}")
                
                # บันทึกไฟล์
                content = await file.read()
                print(f"   File size: {len(content)} bytes")
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # ตรวจสอบว่าไฟล์ถูกบันทึกจริง
                if file_path.exists():
                    print(f"   ✅ File saved successfully")
                    uploaded_files.append(safe_filename)
                else:
                    print(f"   ❌ File NOT saved!")
        
        print(f"\n📦 Total files uploaded: {len(uploaded_files)}")
        print(f"Files: {uploaded_files}")
        
        # อัปเดต database
        from config.db_mssql import get_mssql_conn
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # ดึงไฟล์เดิม (ถ้ามี)
        cursor.execute("""
            SELECT attached_documents FROM special_price_requests
            WHERE request_number = ?
        """, (request_number,))
        result = cursor.fetchone()
        
        existing_files = []
        if result and result[0]:
            try:
                existing_files = json.loads(result[0])
                print(f"📋 Existing files: {existing_files}")
            except:
                existing_files = []
        
        # รวมไฟล์เดิมกับไฟล์ใหม่
        all_files = existing_files + uploaded_files
        print(f"📋 All files (after merge): {all_files}")
        
        # อัปเดต database
        cursor.execute("""
            UPDATE special_price_requests
            SET attached_documents = ?,
                updated_at = ?
            WHERE request_number = ?
        """, (json.dumps(all_files), datetime.now().isoformat(timespec="seconds"), request_number))
        
        rows_affected = cursor.rowcount
        print(f"💾 Database UPDATE rows affected: {rows_affected}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Upload completed successfully\n")
        
        return {
            "success": True,
            "files_uploaded": len(uploaded_files),
            "files": uploaded_files,
            "total_files": len(all_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR in upload_approval_files:")
        traceback.print_exc()
        raise HTTPException(500, f"Error uploading files: {str(e)}")











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
    ดึงรายการไฟล์ที่แนบมากับคำขอ (ทั้งที่อัปโหลดผ่าน web และที่แนบมาโดยผู้อนุมัติ)
    """
    try:
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, f"Request {request_number} not found")
        
        import json
        all_files = []
        
        # ⭐ 1. ดึงไฟล์จาก attached_documents (ไฟล์ที่อัปโหลดผ่าน web)
        if request_data.get("attached_documents"):
            try:
                attached = json.loads(request_data["attached_documents"])
                all_files.extend(attached)
                print(f"📎 Found {len(attached)} files in attached_documents")
            except Exception as e:
                print(f"⚠️ Error parsing attached_documents: {e}")
        
        # ⭐ 2. ดึงไฟล์จาก approval_pdf_files (ไฟล์ที่ผู้อนุมัติแนบมา)
        if request_data.get("approval_pdf_files"):
            try:
                approval_files = json.loads(request_data["approval_pdf_files"])
                all_files.extend(approval_files)
                print(f"📧 Found {len(approval_files)} files in approval_pdf_files")
            except Exception as e:
                print(f"⚠️ Error parsing approval_pdf_files: {e}")
        
        print(f"📦 Total files: {len(all_files)}")
        print(f"Files: {all_files}")
        
        # สร้าง URL สำหรับดาวน์โหลด
        files_info = []
        for filename in all_files:
            files_info.append({
                "filename": filename,
                "download_url": f"/api/special-price-requests/{request_number}/download-approval-file?filename={filename}"
            })
        
        return {
            "request_number": request_number,
            "pdf_files": files_info,
            "total": len(files_info)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Error in download_approval_pdfs:")
        traceback.print_exc()
        raise HTTPException(500, f"Error fetching files: {str(e)}")


@router.get("/{request_number}/download-approval-file", summary="ดาวน์โหลดไฟล์ที่แนบมา")
def download_approval_file(request_number: str, filename: str = Query(...)):
    """
    ดาวน์โหลดไฟล์ที่แนบมากับคำขอ (ทั้งที่อัปโหลดผ่าน web และที่แนบมาโดยผู้อนุมัติ)
    """
    try:
        request_data = get_request_detail(request_number)
        
        if not request_data:
            raise HTTPException(404, "Request not found")
        
        # ตรวจสอบว่าไฟล์อยู่ในรายการที่แนบมา
        import json
        all_files = []
        
        # รวมไฟล์จาก attached_documents
        if request_data.get("attached_documents"):
            try:
                all_files.extend(json.loads(request_data["attached_documents"]))
            except:
                pass
        
        # รวมไฟล์จาก approval_pdf_files
        if request_data.get("approval_pdf_files"):
            try:
                all_files.extend(json.loads(request_data["approval_pdf_files"]))
            except:
                pass
        
        if filename not in all_files:
            raise HTTPException(404, f"File '{filename}' not found in request attachments")
        
        file_path = PDF_STORAGE_PATH / filename
        
        if not file_path.exists():
            raise HTTPException(404, f"File '{filename}' not found on server at {file_path}")
        
        # ตรวจสอบ file extension เพื่อกำหนด media type
        file_ext = filename.split('.')[-1].lower()
        media_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        }
        media_type = media_types.get(file_ext, 'application/octet-stream')
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Error in download_approval_file:")
        traceback.print_exc()
        raise HTTPException(500, f"Error downloading file: {str(e)}")



