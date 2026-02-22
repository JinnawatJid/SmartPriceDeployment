# ============================================
# email_service.py
# Service สำหรับส่ง Email
# ============================================

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional, List
from config.email_config import EMAIL_CONFIG
from config.config_external_api import BASE_URL


def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachments: Optional[List[Path]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> dict:
    """
    ส่ง Email พื้นฐาน
    
    Args:
        to_email: Email ผู้รับ
        subject: หัวข้อ Email
        body: เนื้อหา Email (HTML)
        attachments: ไฟล์แนบ (List of Path objects)
        cc: CC Email addresses
        bcc: BCC Email addresses
    
    Returns:
        dict: {
            "success": bool,
            "message_id": str,
            "error": str (ถ้ามี)
        }
    """
    max_retries = EMAIL_CONFIG["max_retries"]
    retry_delay = EMAIL_CONFIG["retry_delay"]
    
    for attempt in range(max_retries):
        try:
            # สร้าง Email Message
            msg = MIMEMultipart()
            msg["From"] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            if bcc:
                msg["Bcc"] = ", ".join(bcc)
            
            # เพิ่ม Body
            msg.attach(MIMEText(body, "html", "utf-8"))
            
            # เพิ่มไฟล์แนบ
            if attachments:
                for file_path in attachments:
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=file_path.name)
                            part["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
                            msg.attach(part)
            
            # ส่ง Email
            with smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]) as server:
                if EMAIL_CONFIG["smtp_use_tls"]:
                    server.starttls()
                
                server.login(EMAIL_CONFIG["smtp_user"], EMAIL_CONFIG["smtp_password"])
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(EMAIL_CONFIG["from_email"], recipients, msg.as_string())
            
            # สำเร็จ
            message_id = msg.get("Message-ID", "")
            return {
                "success": True,
                "message_id": message_id,
                "error": None
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return {
                    "success": False,
                    "message_id": None,
                    "error": str(e)
                }
    
    return {
        "success": False,
        "message_id": None,
        "error": "Max retries exceeded"
    }



def send_approval_request(request_data: dict, pdf_path: Path) -> dict:
    """
    ส่ง Email ขออนุมัติราคาพิเศษพร้อมแนบ PDF (แบบเก่า - ตอบกลับอีเมล)
    
    Args:
        request_data: ข้อมูลคำขอ
        pdf_path: Path ของไฟล์ PDF
    
    Returns:
        dict: ผลการส่ง Email
    """
    subject = f"[Approval Required] Special Price Request {request_data['request_number']}"
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Sarabun', Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .info-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #495057; }}
            .value {{ color: #212529; }}
            .price-highlight {{ font-size: 18px; font-weight: bold; color: #dc3545; }}
            .instructions {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
            .warning {{ color: #856404; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0; color: #007bff;">คำขอราคาพิเศษรอการพิจารณา</h2>
            </div>
            
            <div class="info-row">
                <span class="label">เลขที่คำขอ:</span>
                <span class="value">{request_data['request_number']}</span>
            </div>
            
            <div class="info-row">
                <span class="label">ผู้ขอ:</span>
                <span class="value">{request_data['requester_name']}</span>
            </div>
            
            <div class="info-row">
                <span class="label">ลูกค้า:</span>
                <span class="value">{request_data.get('customer_name', 'N/A')}</span>
            </div>
            
            <div class="info-row">
                <span class="label">เลขที่ใบเสนอราคา:</span>
                <span class="value">{request_data['quote_no']}</span>
            </div>
            
            <hr style="margin: 20px 0;">
            
    
            <hr style="margin: 20px 0;">
            
            <div class="info-row">
                <span class="label">เหตุผลที่ขอ:</span>
                <div style="margin-top: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                    {request_data['request_reason']}
                </div>
            </div>
            
            <div class="instructions">
                <p><strong>วิธีการอนุมัติ/ปฏิเสธ:</strong></p>
                <p>กรุณา <strong>Reply Email นี้</strong> ด้วยคำว่า:</p>
                <ul>
                    <li><strong>APPROVE</strong> เพื่ออนุมัติ</li>
                    <li><strong>REJECT: &lt;เหตุผล&gt;</strong> เพื่อปฏิเสธ (ระบุเหตุผลหลัง REJECT:)</li>
                </ul>
                <p class="warning">*** กรุณาอย่าแก้ไข Subject ของ Email ***</p>
            </div>
            
            <p style="margin-top: 20px;">รายละเอียดเพิ่มเติมในไฟล์แนบ</p>
            
            <hr style="margin: 20px 0;">
            
            <p style="color: #6c757d; font-size: 12px;">
                Email นี้ถูกส่งอัตโนมัติจากระบบใบเสนอราคา<br>
                กรุณาอย่าตอบกลับ Email นี้โดยตรง ให้ใช้วิธีการด้านบนเท่านั้น
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(
        to_email=request_data['approver_email'],
        subject=subject,
        body=body,
        attachments=[pdf_path] if pdf_path.exists() else None
    )


def send_approval_request_with_links(request_data: dict, pdf_path: Path, token: str) -> dict:
    """
    ส่ง Email ขออนุมัติราคาพิเศษพร้อมลิงก์ Approve/Reject
    
    Args:
        request_data: ข้อมูลคำขอ
        pdf_path: Path ของไฟล์ PDF
        token: Token สำหรับการอนุมัติ
    
    Returns:
        dict: ผลการส่ง Email
    """
    # สร้าง URL สำหรับ approve และ reject
    approve_url = f"{BASE_URL}/api/special-price-requests/approve/{token}"
    reject_url = f"{BASE_URL}/api/special-price-requests/reject/{token}"
    
    subject = f"[Approval Required] Special Price Request {request_data['request_number']}"
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Sarabun', Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; }}
            .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .info-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #495057; }}
            .value {{ color: #212529; }}
            .price-highlight {{ font-size: 18px; font-weight: bold; color: #dc3545; }}
            .button-container {{ 
                text-align: center; 
                margin: 30px 0;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }}
            .btn {{ 
                display: inline-block;
                padding: 15px 50px;
                margin: 10px 15px;
                text-decoration: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                color: white !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            }}
            .btn-approve {{ 
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            }}
            .btn-reject {{ 
                background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
            }}
            .note {{ 
                background-color: #e7f3ff; 
                padding: 15px; 
                border-radius: 5px; 
                margin-top: 20px; 
                border-left: 4px solid #007bff; 
            }}
            .footer {{ 
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                color: #6c757d; 
                font-size: 12px; 
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0; color: #007bff;">🔔 คำขอราคาพิเศษรอการพิจารณา</h2>
            </div>
            
            <div class="info-row">
                <span class="label">เลขที่คำขอ:</span>
                <span class="value">{request_data['request_number']}</span>
            </div>
            
            <div class="info-row">
                <span class="label">ผู้ขอ:</span>
                <span class="value">{request_data['requester_name']}</span>
            </div>
            
            <div class="info-row">
                <span class="label">ลูกค้า:</span>
                <span class="value">{request_data.get('customer_name', 'N/A')}</span>
            </div>
            
            <div class="info-row">
                <span class="label">เลขที่ใบเสนอราคา:</span>
                <span class="value">{request_data['quote_no']}</span>
            </div>
            
            <hr style="margin: 20px 0;">
            
            <div class="info-row">
                <span class="label">ราคาเดิม:</span>
                <span class="value">{request_data['original_total']:,.2f} บาท</span>
            </div>
            
            <div class="info-row">
                <span class="label">ราคาที่ขอ:</span>
                <span class="price-highlight">{request_data['requested_total']:,.2f} บาท</span>
            </div>
            
            <div class="info-row">
                <span class="label">ส่วนลด:</span>
                <span class="price-highlight">{request_data['discount_percentage']:.2f}%</span>
            </div>
            
            <hr style="margin: 20px 0;">
            
            <div class="info-row">
                <span class="label">เหตุผลที่ขอ:</span>
                <div style="margin-top: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                    {request_data['request_reason']}
                </div>
            </div>
            
            <div class="note">
                <p style="margin: 0 0 10px 0;"><strong>📌 วิธีการพิจารณา:</strong></p>
                <ul style="margin: 5px 0;">
                    <li>คลิกปุ่ม "อนุมัติ" ด้านล่างเพื่ออนุมัติคำขอ (สามารถแนบไฟล์เพิ่มเติมได้)</li>
                    <li>คลิกปุ่ม "ปฏิเสธ" ด้านล่างเพื่อกรอกเหตุผลและปฏิเสธคำขอ</li>
                    <li>ลิงก์นี้จะหมดอายุใน 72 ชั่วโมง</li>
                    <li>รายละเอียดเพิ่มเติมในไฟล์แนบ</li>
                </ul>
            </div>
            
            <div class="button-container">
                <p style="margin: 0 0 15px 0; font-size: 16px; color: #495057;">
                    <strong>กรุณาเลือกการดำเนินการ:</strong>
                </p>
                <a href="{approve_url}" class="btn btn-approve">✅ อนุมัติคำขอ</a>
                <a href="{reject_url}" class="btn btn-reject">❌ ปฏิเสธคำขอ</a>
            </div>
            
            <div class="footer">
                <p style="margin: 5px 0;">Email นี้ถูกส่งอัตโนมัติจากระบบใบเสนอราคา</p>
                <p style="margin: 5px 0;">หากปุ่มไม่ทำงาน กรุณาคัดลอกลิงก์ด้านล่างไปวางในเบราว์เซอร์</p>
                <p style="margin: 10px 0; font-size: 11px; word-break: break-all;">
                    อนุมัติ: {approve_url}<br>
                    ปฏิเสธ: {reject_url}
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(
        to_email=request_data['approver_email'],
        subject=subject,
        body=body,
        attachments=[pdf_path] if pdf_path.exists() else None
    )


def send_approval_notification(request_data: dict) -> dict:
    """
    แจ้งผลการอนุมัติกลับไปหาผู้ขอ
    (ปิดการใช้งานชั่วคราวเพราะไม่มี requester_email)
    
    Args:
        request_data: ข้อมูลคำขอ
    
    Returns:
        dict: ผลการส่ง Email
    """
    # ⚠️ ปิดการใช้งานเพราะไม่มี requester_email
    return {
        "success": False,
        "message_id": None,
        "error": "Requester email not available"
    }


def send_rejection_notification(request_data: dict) -> dict:
    """
    แจ้งผลการปฏิเสธกลับไปหาผู้ขอ
    (ปิดการใช้งานชั่วคราวเพราะไม่มี requester_email)
    
    Args:
        request_data: ข้อมูลคำขอ
    
    Returns:
        dict: ผลการส่ง Email
    """
    # ⚠️ ปิดการใช้งานเพราะไม่มี requester_email
    return {
        "success": False,
        "message_id": None,
        "error": "Requester email not available"
    }
