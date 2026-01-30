# ============================================
# special_price_request_service.py
# Service สำหรับจัดการคำขอราคาพิเศษ
# ============================================

from datetime import datetime
from typing import List, Optional, Dict, Any
from config.db_sqlite import get_conn


def generate_request_number() -> str:
    """
    สร้างเลขที่คำขอรูปแบบ SP-YYMMDD-XXXX
    เช่น SP-250130-0001
    """
    now = datetime.now()
    yy = str(now.year)[-2:]
    mm = f"{now.month:02d}"
    dd = f"{now.day:02d}"
    
    prefix = f"SP-{yy}{mm}{dd}"
    
    conn = get_conn()
    cur = conn.cursor()
    
    # นับจำนวนคำขอในวันนี้
    cur.execute("""
        SELECT COUNT(*) as count
        FROM special_price_requests
        WHERE request_number LIKE ?
    """, (f"{prefix}%",))
    
    result = cur.fetchone()
    count = result["count"] if result else 0
    conn.close()
    
    seq = f"{count + 1:04d}"
    return f"{prefix}-{seq}"


def calculate_discount_percentage(original_total: float, requested_total: float) -> float:
    """
    คำนวณ % ส่วนลด
    """
    if original_total <= 0:
        return 0.0
    
    discount = ((original_total - requested_total) / original_total) * 100
    return round(discount, 2)


def create_request(data: dict) -> dict:
    """
    สร้างคำขอราคาพิเศษใหม่
    
    Args:
        data: {
            "quote_no": str,
            "customer_code": str,
            "customer_name": str,
            "requester_name": str,
            "requester_phone": str,
            "request_reason": str,
            "original_total": float,
            "requested_total": float,
            "approver_email": str,
            "branch": str,
            "valid_from": str,
            "valid_to": str,
            "items": [
                {
                    "item_code": str,
                    "item_name": str,
                    "quantity": float,
                    "unit": str,
                    "w1_price": float,
                    "requested_price": float
                }
            ]
        }
    
    Returns:
        dict: {
            "request_number": str,
            "status": str,
            "created_at": str
        }
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # สร้างเลขที่คำขอ
    request_number = generate_request_number()
    
    # คำนวณ % ส่วนลด
    discount_pct = calculate_discount_percentage(
        data["original_total"],
        data["requested_total"]
    )
    
    now = datetime.now().isoformat(timespec="seconds")
    
    # Insert header
    cur.execute("""
        INSERT INTO special_price_requests (
            request_number, quote_no, customer_code, customer_name,
            requester_name, requester_phone, request_reason,
            original_total, requested_total, discount_percentage,
            status, approver_email, branch, valid_from, valid_to,
            email_sent_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request_number,
        data["quote_no"],
        data.get("customer_code", ""),
        data.get("customer_name", ""),
        data["requester_name"],
        data.get("requester_phone", ""),
        data["request_reason"],
        data["original_total"],
        data["requested_total"],
        discount_pct,
        "pending",
        data["approver_email"],
        data.get("branch", ""),
        data.get("valid_from", ""),
        data.get("valid_to", ""),
        now,
        now,
        now
    ))
    
    request_id = cur.lastrowid
    
    # Insert items
    for item in data.get("items", []):
        original_amount = item["w1_price"] * item["quantity"]
        requested_amount = item["requested_price"] * item["quantity"]
        is_below_w1 = item["requested_price"] < item["w1_price"]
        
        cur.execute("""
            INSERT INTO special_price_request_items (
                request_id, item_code, item_name, quantity, unit,
                w1_price, requested_price, original_amount, requested_amount,
                is_below_w1, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id,
            item["item_code"],
            item["item_name"],
            item["quantity"],
            item.get("unit", ""),
            item["w1_price"],
            item["requested_price"],
            original_amount,
            requested_amount,
            is_below_w1,
            now
        ))
    
    # อัปเดต Quote_Header
    cur.execute("""
        UPDATE Quote_Header
        SET Status = 'pending_approval',
            special_price_request_id = ?,
            special_price_status = 'pending',
            LastUpdate = ?
        WHERE QuoteNo = ?
    """, (request_id, now, data["quote_no"]))
    
    conn.commit()
    conn.close()
    
    return {
        "request_number": request_number,
        "status": "pending",
        "created_at": now
    }



def get_requests(status: Optional[str] = None, limit: int = 20, offset: int = 0) -> dict:
    """
    ดึงรายการคำขอราคาพิเศษ
    
    Args:
        status: "pending", "approved", "rejected", None (all)
        limit: จำนวนรายการต่อหน้า
        offset: เริ่มต้นที่รายการที่
    
    Returns:
        dict: {
            "items": [...],
            "total": int,
            "limit": int,
            "offset": int
        }
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if status and status != "all":
        where_clause = "WHERE status = ?"
        params.append(status)
    
    # Count total
    count_sql = f"SELECT COUNT(*) as total FROM special_price_requests {where_clause}"
    cur.execute(count_sql, params)
    total = cur.fetchone()["total"]
    
    # Get items
    sql = f"""
        SELECT 
            request_number, quote_no, customer_code, customer_name,
            requester_name, original_total, requested_total,
            discount_percentage, status, approver_email, approved_by, approved_at,
            created_at, updated_at
        FROM special_price_requests
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    
    cur.execute(sql, params + [limit, offset])
    rows = cur.fetchall()
    
    items = [dict(row) for row in rows]
    conn.close()
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }


def get_request_detail(request_number: str) -> Optional[dict]:
    """
    ดึงรายละเอียดคำขอราคาพิเศษ
    
    Args:
        request_number: เลขที่คำขอ
    
    Returns:
        dict หรือ None ถ้าไม่พบ
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # Get header
    cur.execute("""
        SELECT *
        FROM special_price_requests
        WHERE request_number = ?
    """, (request_number,))
    
    header = cur.fetchone()
    if not header:
        conn.close()
        return None
    
    header_dict = dict(header)
    
    # Get items
    cur.execute("""
        SELECT *
        FROM special_price_request_items
        WHERE request_id = ?
        ORDER BY id
    """, (header_dict["id"],))
    
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    header_dict["items"] = items
    return header_dict


def approve_request(request_number: str, approved_by: str, pdf_files: list = None) -> bool:
    """
    อนุมัติคำขอราคาพิเศษ
    
    Args:
        request_number: เลขที่คำขอ
        approved_by: ชื่อผู้อนุมัติ
        pdf_files: รายการไฟล์ PDF ที่แนบมา (optional)
    
    Returns:
        bool: สำเร็จหรือไม่
    """
    conn = get_conn()
    cur = conn.cursor()
    
    now = datetime.now().isoformat(timespec="seconds")
    
    # แปลง pdf_files เป็น JSON string
    import json
    pdf_files_json = json.dumps(pdf_files) if pdf_files else None
    
    # อัปเดตสถานะคำขอ
    cur.execute("""
        UPDATE special_price_requests
        SET status = 'approved',
            approved_by = ?,
            approved_at = ?,
            approval_pdf_files = ?,
            updated_at = ?
        WHERE request_number = ? AND status = 'pending'
    """, (approved_by, now, pdf_files_json, now, request_number))
    
    if cur.rowcount == 0:
        conn.close()
        return False
    
    # ดึง quote_no
    cur.execute("""
        SELECT quote_no
        FROM special_price_requests
        WHERE request_number = ?
    """, (request_number,))
    
    result = cur.fetchone()
    if not result:
        conn.close()
        return False
    
    quote_no = result["quote_no"]
    
    # อัปเดต Quote_Header
    cur.execute("""
        UPDATE Quote_Header
        SET Status = 'open',
            special_price_status = 'approved',
            LastUpdate = ?
        WHERE QuoteNo = ?
    """, (now, quote_no))
    
    print(f"✅ Updated Quote_Header: {quote_no}, rows affected: {cur.rowcount}")
    
    conn.commit()
    conn.close()
    
    return True


def reject_request(request_number: str, rejection_reason: str) -> bool:
    """
    ปฏิเสธคำขอราคาพิเศษ
    
    Args:
        request_number: เลขที่คำขอ
        rejection_reason: เหตุผลที่ปฏิเสธ
    
    Returns:
        bool: สำเร็จหรือไม่
    """
    conn = get_conn()
    cur = conn.cursor()
    
    now = datetime.now().isoformat(timespec="seconds")
    
    # อัปเดตสถานะคำขอ
    cur.execute("""
        UPDATE special_price_requests
        SET status = 'rejected',
            rejection_reason = ?,
            updated_at = ?
        WHERE request_number = ? AND status = 'pending'
    """, (rejection_reason, now, request_number))
    
    if cur.rowcount == 0:
        conn.close()
        return False
    
    # ดึง quote_no
    cur.execute("""
        SELECT quote_no
        FROM special_price_requests
        WHERE request_number = ?
    """, (request_number,))
    
    result = cur.fetchone()
    if not result:
        conn.close()
        return False
    
    quote_no = result["quote_no"]
    
    # อัปเดต Quote_Header
    cur.execute("""
        UPDATE Quote_Header
        SET Status = 'draft',
            special_price_status = 'rejected',
            LastUpdate = ?
        WHERE QuoteNo = ?
    """, (now, quote_no))
    
    conn.commit()
    conn.close()
    
    return True
