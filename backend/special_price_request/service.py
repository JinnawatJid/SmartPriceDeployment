# ============================================
# special_price_request_service.py
# Service สำหรับจัดการคำขอราคาพิเศษ
# ============================================

from datetime import datetime
from typing import List, Optional, Dict, Any
from config.db_mssql import get_mssql_conn


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
    
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    # นับจำนวนคำขอในวันนี้
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM special_price_requests
        WHERE request_number LIKE ?
    """, (f"{prefix}%",))
    
    result = cursor.fetchone()
    count = result[0] if result else 0
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
    """
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    # สร้างเลขที่คำขอ
    request_number = generate_request_number()
    
    # คำนวณ % ส่วนลด
    discount_pct = calculate_discount_percentage(
        data["original_total"],
        data["requested_total"]
    )
    
    now = datetime.now().isoformat(timespec="seconds")
    
    # Insert header
    try:
        cursor.execute("""
            INSERT INTO special_price_requests (
                request_number, quote_no, customer_code, customer_name, customer_type,
                requester_name, request_reason,
                original_total, requested_total, discount_percentage,
                status, approver_email, branch, valid_from, valid_to,
                email_sent_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_number,
            data["quote_no"],
            data.get("customer_code", ""),
            data.get("customer_name", ""),
            data.get("customer_type", ""),
            data["requester_name"],
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
    except Exception as e:
        conn.close()
        raise
    
    # Get request_id
    try:
        cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT) AS id")
        result = cursor.fetchone()
        
        if result is None or result[0] is None:
            # Fallback: query by request_number
            cursor.execute("""
                SELECT id FROM special_price_requests 
                WHERE request_number = ?
            """, (request_number,))
            result = cursor.fetchone()
        
        if result is None or result[0] is None:
            raise Exception("Failed to get request_id after INSERT")
        
        request_id = int(result[0])
    except Exception as e:
        conn.close()
        raise
    
    # Insert items
    for item in data.get("items", []):
        original_amount = item["w1_price"] * item["quantity"]
        requested_amount = item["requested_price"] * item["quantity"]
        is_below_w1 = item["requested_price"] < item["w1_price"]
        
        cursor.execute("""
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
    cursor.execute("""
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
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    # Build WHERE clause
    where_clause = ""
    params = []
    
    if status and status != "all":
        where_clause = "WHERE status = ?"
        params.append(status)
    
    # Count total
    count_sql = f"SELECT COUNT(*) as total FROM special_price_requests {where_clause}"
    cursor.execute(count_sql, tuple(params))
    total = cursor.fetchone()[0]
    
    # Get items (⭐ MSSQL: ใช้ OFFSET/FETCH แทน LIMIT)
    sql = f"""
        SELECT 
            request_number, quote_no, customer_code, customer_name,
            requester_name, original_total, requested_total,
            discount_percentage, status, approver_email, approved_by, approved_at,
            created_at, updated_at
        FROM special_price_requests
        {where_clause}
        ORDER BY created_at DESC
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
    """
    
    cursor.execute(sql, tuple(params + [offset, limit]))
    
    # ⭐ MSSQL: แปลง rows เป็น dict
    columns = [column[0] for column in cursor.description]
    items = []
    for row in cursor.fetchall():
        items.append(dict(zip(columns, row)))
    
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
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    # Get header
    cursor.execute("""
        SELECT *
        FROM special_price_requests
        WHERE request_number = ?
    """, (request_number,))
    
    header_row = cursor.fetchone()
    if not header_row:
        conn.close()
        return None
    
    # ⭐ MSSQL: แปลง row เป็น dict
    columns = [column[0] for column in cursor.description]
    header_dict = dict(zip(columns, header_row))
    
    # Get items
    cursor.execute("""
        SELECT *
        FROM special_price_request_items
        WHERE request_id = ?
        ORDER BY id
    """, (header_dict["id"],))
    
    # ⭐ MSSQL: แปลง rows เป็น list of dict
    item_columns = [column[0] for column in cursor.description]
    items = []
    for row in cursor.fetchall():
        items.append(dict(zip(item_columns, row)))
    
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
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat(timespec="seconds")
    
    # แปลง pdf_files เป็น JSON string
    import json
    pdf_files_json = json.dumps(pdf_files) if pdf_files else None
    
    # 🔍 DEBUG: แสดงข้อมูลที่จะบันทึก
    print(f"\n🔍 DEBUG approve_request:")
    print(f"   request_number: {request_number}")
    print(f"   approved_by: {approved_by}")
    print(f"   pdf_files: {pdf_files}")
    print(f"   pdf_files_json: {pdf_files_json}")
    
    # อัปเดตสถานะคำขอ
    cursor.execute("""
        UPDATE special_price_requests
        SET status = 'approved',
            approved_by = ?,
            approved_at = ?,
            approval_pdf_files = ?,
            updated_at = ?
        WHERE request_number = ? AND status = 'pending'
    """, (approved_by, now, pdf_files_json, now, request_number))
    
    rows_affected = cursor.rowcount
    print(f"   📝 UPDATE rows affected: {rows_affected}")
    
    if rows_affected == 0:
        print(f"   ❌ No rows updated (request not found or not pending)")
        conn.close()
        return False
    
    # ดึง quote_no
    cursor.execute("""
        SELECT quote_no
        FROM special_price_requests
        WHERE request_number = ?
    """, (request_number,))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    
    quote_no = result[0]  # ⭐ MSSQL: ใช้ index แทน dict key
    
    # อัปเดต Quote_Header
    cursor.execute("""
        UPDATE Quote_Header
        SET Status = 'open',
            special_price_status = 'approved',
            LastUpdate = ?
        WHERE QuoteNo = ?
    """, (now, quote_no))
    
    print(f"   ✅ Updated Quote_Header: {quote_no}, rows affected: {cursor.rowcount}")
    
    conn.commit()
    print(f"   ✅ Transaction committed successfully\n")
    conn.close()
    
    return True


def reject_request(request_number: str, rejected_by: str, rejection_reason: str) -> bool:
    """
    ปฏิเสธคำขอราคาพิเศษ
    
    Args:
        request_number: เลขที่คำขอ
        rejected_by: ชื่อผู้ปฏิเสธ
        rejection_reason: เหตุผลที่ปฏิเสธ
    
    Returns:
        bool: สำเร็จหรือไม่
    """
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat(timespec="seconds")
    
    # อัปเดตสถานะคำขอ (ใช้ approved_by และ approved_at เหมือนกับ approve)
    cursor.execute("""
        UPDATE special_price_requests
        SET status = 'rejected',
            approved_by = ?,
            approved_at = ?,
            rejection_reason = ?,
            updated_at = ?
        WHERE request_number = ? AND status = 'pending'
    """, (rejected_by, now, rejection_reason, now, request_number))
    
    if cursor.rowcount == 0:
        conn.close()
        return False
    
    # ดึง quote_no
    cursor.execute("""
        SELECT quote_no
        FROM special_price_requests
        WHERE request_number = ?
    """, (request_number,))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    
    quote_no = result[0]  # ⭐ MSSQL: ใช้ index แทน dict key
    
    # อัปเดต Quote_Header
    cursor.execute("""
        UPDATE Quote_Header
        SET Status = 'draft',
            special_price_status = 'rejected',
            LastUpdate = ?
        WHERE QuoteNo = ?
    """, (now, quote_no))
    
    conn.commit()
    conn.close()
    
    return True



