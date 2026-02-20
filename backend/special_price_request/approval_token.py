# ============================================
# approval_token.py
# จัดการ Token สำหรับการอนุมัติผ่าน URL
# ============================================

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from config.db_sqlite import get_conn


def generate_approval_token(request_number: str, expires_hours: int = 72) -> str:
    """
    สร้าง token สำหรับการอนุมัติ
    
    Args:
        request_number: เลขที่คำขอ
        expires_hours: จำนวนชั่วโมงที่ token จะหมดอายุ (default 72 ชม. = 3 วัน)
    
    Returns:
        str: token
    """
    # สร้าง random token
    token = secrets.token_urlsafe(32)
    
    # คำนวณเวลาหมดอายุ
    expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat(timespec="seconds")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # บันทึก token
    cur.execute("""
        INSERT INTO approval_tokens (
            request_number, token, expires_at, created_at
        ) VALUES (?, ?, ?, ?)
    """, (
        request_number,
        token,
        expires_at,
        datetime.now().isoformat(timespec="seconds")
    ))
    
    conn.commit()
    conn.close()
    
    return token


def validate_token(token: str) -> Optional[str]:
    """
    ตรวจสอบ token และคืนค่า request_number ถ้า valid
    
    Args:
        token: token ที่ต้องการตรวจสอบ
    
    Returns:
        str: request_number ถ้า token valid, None ถ้า invalid หรือหมดอายุ
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # ค้นหา token
    cur.execute("""
        SELECT request_number, expires_at, used_at
        FROM approval_tokens
        WHERE token = ?
    """, (token,))
    
    result = cur.fetchone()
    conn.close()
    
    if not result:
        return None
    
    # ตรวจสอบว่าถูกใช้ไปแล้วหรือยัง
    if result["used_at"]:
        return None
    
    # ตรวจสอบว่าหมดอายุหรือยัง
    expires_at = datetime.fromisoformat(result["expires_at"])
    if datetime.now() > expires_at:
        return None
    
    return result["request_number"]


def mark_token_used(token: str) -> bool:
    """
    ทำเครื่องหมายว่า token ถูกใช้ไปแล้ว
    
    Args:
        token: token ที่ถูกใช้
    
    Returns:
        bool: สำเร็จหรือไม่
    """
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE approval_tokens
        SET used_at = ?
        WHERE token = ? AND used_at IS NULL
    """, (
        datetime.now().isoformat(timespec="seconds"),
        token
    ))
    
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    
    return success
