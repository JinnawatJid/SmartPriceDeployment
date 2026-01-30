# ============================================
# pdf_service.py
# Service สำหรับสร้าง PDF
# ============================================

from pathlib import Path
from datetime import datetime
from weasyprint import HTML, CSS
from config.email_config import PDF_STORAGE_PATH


def generate_special_price_request_pdf(request_data: dict) -> Path:
    """
    สร้าง PDF สำหรับคำขอราคาพิเศษ
    
    Args:
        request_data: ข้อมูลคำขอพร้อมรายการสินค้า
    
    Returns:
        Path: Path ของไฟล์ PDF ที่สร้าง
    """
    # สร้าง HTML Template
    html_content = _generate_html_template(request_data)
    
    # สร้างชื่อไฟล์
    filename = f"{request_data['request_number']}.pdf"
    pdf_path = PDF_STORAGE_PATH / filename
    
    # สร้าง PDF
    HTML(string=html_content).write_pdf(pdf_path)
    
    return pdf_path


def _generate_html_template(data: dict) -> str:
    """
    สร้าง HTML Template สำหรับ PDF (แบบย่อ)
    """
    # สร้างตารางรายการสินค้า
    items_html = ""
    for idx, item in enumerate(data.get("items", []), 1):
        is_below_w1 = item.get("is_below_w1", False)
        warning_icon = "⚠️" if is_below_w1 else ""
        
        items_html += f"""
        <tr>
            <td class="center">{idx}</td>
            <td>{item['item_code']}</td>
            <td>{item['item_name']}</td>
            <td class="center">{item['quantity']:,.2f}</td>
            <td class="center">{item.get('unit', '')}</td>
            <td class="right">{item['requested_price']:,.2f}</td>
            <td class="center">{warning_icon}</td>
        </tr>
        """
    
    # สร้าง HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 15mm;
            }}
            
            @font-face {{
                font-family: "Sarabun";
                src: url("Sarabun-Regular.ttf");
            }}
            
            body {{
                font-family: "Sarabun", Arial, sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #333;
                padding-bottom: 15px;
            }}
            
            .header h1 {{
                font-size: 20px;
                margin: 0;
                color: #000;
            }}
            
            .info-section {{
                margin-bottom: 25px;
            }}
            
            .info-row {{
                display: flex;
                margin: 8px 0;
            }}
            
            .info-label {{
                width: 180px;
                font-weight: bold;
            }}
            
            .info-value {{
                flex: 1;
            }}
            
            .reason-section {{
                background-color: #f8f9fa;
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin: 20px 0;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            
            th {{
                background-color: #333;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 12px;
                border: 1px solid #333;
            }}
            
            td {{
                padding: 8px;
                border: 1px solid #dee2e6;
                font-size: 12px;
            }}
            
            .center {{
                text-align: center;
            }}
            
            .right {{
                text-align: right;
            }}
            
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
            }}
            
            .signature-section {{
                display: flex;
                justify-content: space-between;
                margin-top: 50px;
            }}
            
            .signature-box {{
                width: 45%;
                text-align: center;
            }}
            
            .signature-line {{
                border-top: 1px solid #000;
                margin-top: 60px;
                padding-top: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>แบบฟอร์มขออนุมัติราคาพิเศษ</h1>
        </div>
        
        <div class="info-section">
            <div class="info-row">
                <div class="info-label">เลขที่คำขอ:</div>
                <div class="info-value">{data['request_number']}</div>
            </div>
            <div class="info-row">
                <div class="info-label">วันที่ขอ:</div>
                <div class="info-value">{data.get('created_at', '')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">ผู้ขอ:</div>
                <div class="info-value">{data['requester_name']}</div>
            </div>
            <div class="info-row">
                <div class="info-label">เบอร์โทร:</div>
                <div class="info-value">{data.get('requester_phone', '-')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">ลูกค้า:</div>
                <div class="info-value">{data.get('customer_name', 'N/A')}</div>
            </div>
            <div class="info-row">
                <div class="info-label">เลขที่ใบเสนอราคา:</div>
                <div class="info-value">{data['quote_no']}</div>
            </div>
        </div>
        
        <div class="reason-section">
            <p style="margin: 0 0 10px 0; font-weight: bold;">เหตุผลที่ขอราคาพิเศษ:</p>
            <p style="margin: 0;">{data['request_reason']}</p>
        </div>
        
        <h3 style="margin-top: 30px;">รายการสินค้าที่ขอราคาพิเศษ</h3>
        <table>
            <thead>
                <tr>
                    <th class="center" style="width: 40px;">ลำดับ</th>
                    <th style="width: 120px;">รหัสสินค้า</th>
                    <th>ชื่อสินค้า</th>
                    <th class="center" style="width: 70px;">จำนวน</th>
                    <th class="center" style="width: 60px;">หน่วย</th>
                    <th class="right" style="width: 100px;">ราคาที่ขอ</th>
                    <th class="center" style="width: 60px;">หมายเหตุ</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div class="signature-section">
            <div class="signature-box">
                <div class="signature-line">
                    <p style="margin: 5px 0;">ผู้ขอ</p>
                    <p style="margin: 5px 0; font-size: 11px;">วันที่: ........................</p>
                </div>
            </div>
            <div class="signature-box">
                <div class="signature-line">
                    <p style="margin: 5px 0;">ผู้อนุมัติ</p>
                    <p style="margin: 5px 0; font-size: 11px;">วันที่: ........................</p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p style="font-size: 10px; color: #6c757d; margin: 0;">เอกสารนี้สร้างโดยระบบอัตโนมัติ | {data['request_number']}</p>
        </div>
    </body>
    </html>
    """
    
    return html
