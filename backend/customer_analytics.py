# customer_analytics.py
# -----------------------------------------------------
# Customer Analytics API
# - ใช้ส่งข้อมูลให้ทีมอื่น / เพื่อน
# - วิเคราะห์จาก Invoice โดยตรง
# - ไม่ผูกกับ pricing / quote flow
# -----------------------------------------------------

from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from datetime import datetime, timedelta
from db_sqlite import get_conn

router = APIRouter(
    prefix="/api/customer-analytics",
    tags=["customer-analytics"]
)

# =====================================================
# Helpers
# =====================================================

def classify_group(no):
    """
    ใช้ตัวอักษรตัวแรกของ SKU
    G A S Y C E
    """
    if not isinstance(no, str) or len(no) == 0:
        return None
    return no[0].upper()


def load_invoice_by_customer(conn, customer_code: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        'SELECT * FROM "Invoice" WHERE "Sell-to Customer No." = ?',
        conn,
        params=[customer_code],
    )
    if not df.empty:
        df.columns = [c.strip() for c in df.columns]
    return df


def resolve_anchor_and_cutoff(inv: pd.DataFrame, months: int, anchor_date: str | None):
    """
    กำหนด anchor date และ cutoff date

    - ถ้า caller ส่ง anchor_date มา → ใช้ค่านั้น
    - ถ้าไม่ส่ง → ใช้ Posting Date ล่าสุดใน Invoice
    """
    inv["Posting Date"] = pd.to_datetime(inv["Posting Date"], errors="coerce")

    if anchor_date:
        anchor = pd.to_datetime(anchor_date)
    else:
        anchor = inv["Posting Date"].max()

    if pd.isna(anchor):
        return None, None

    cutoff = anchor - timedelta(days=30 * months)
    return anchor, cutoff


# =====================================================
# API 1: Monthly Summary
# =====================================================
@router.get("/monthly-summary")
def customer_monthly_summary(
    customer_code: str = Query(..., description="รหัสลูกค้า เช่น 08015AY-1"),
    months: int = Query(6, ge=1, le=24, description="จำนวนเดือนย้อนหลัง (default = 6)"),
    anchor_date: str | None = Query(
        None, description="วันที่อ้างอิง เช่น 2025-06-30 (ถ้าไม่ส่ง จะใช้วันที่ล่าสุดใน Invoice)"
    ),
):
    """
    ====================================================
    JSON Response Example
    ====================================================
    {
      "customer": "08015AY-1",
      "anchor_date": "2025-06-30",
      "months": 6,
      "monthly": [
        { "month": "2025-01", "amount": 120000.50 },
        { "month": "2025-02", "amount": 98000.00 }
      ],
      "total": 218000.50
    }

    Field explanation:
    - customer      : รหัสลูกค้า
    - anchor_date   : วันที่อ้างอิงว่า “6 เดือนล่าสุด” คือถึงวันไหน
    - months        : window ที่ใช้คำนวณ
    - monthly[]     : ยอดขายรายเดือน (Amount Including VAT)
    - total         : ยอดรวมทั้งหมดในช่วงนี้
    ====================================================
    """

    conn = get_conn()
    inv = load_invoice_by_customer(conn, customer_code)
    conn.close()

    if inv.empty:
        return {
            "customer": customer_code,
            "anchor_date": anchor_date,
            "months": months,
            "monthly": [],
            "total": 0.0,
        }

    anchor, cutoff = resolve_anchor_and_cutoff(inv, months, anchor_date)
    if anchor is None:
        raise HTTPException(status_code=400, detail="ไม่สามารถกำหนด anchor date ได้")

    inv = inv[inv["Posting Date"] >= cutoff]
    inv["year_month"] = inv["Posting Date"].dt.to_period("M").astype(str)

    grp = (
        inv.groupby("year_month")["Amount Including VAT"]
        .sum()
        .sort_index()
    )

    monthly = [
        {"month": ym, "amount": float(val)}
        for ym, val in grp.items()
    ]

    return {
        "customer": customer_code,
        "anchor_date": anchor.date().isoformat(),
        "months": months,
        "monthly": monthly,
        "total": float(grp.sum()),
    }


# =====================================================
# API 2: Category Summary
# =====================================================
@router.get("/category-summary")
def customer_category_summary(
    customer_code: str = Query(..., description="รหัสลูกค้า เช่น 08015AY-1"),
    months: int = Query(6, ge=1, le=24, description="จำนวนเดือนย้อนหลัง (default = 6)"),
    anchor_date: str | None = Query(
        None, description="วันที่อ้างอิง เช่น 2025-06-30"
    ),
):
    """
    ====================================================
    JSON Response 
    ====================================================
    {
      "customer": "08015AY-1",
      "anchor_date": "2025-06-30",
      "months": 6,
      "by_category": {
        "G": 320000.0,
        "A": 185000.0,
        "S": 140000.0,
        "Y": 45000.0,
        "C": 32000.0,
        "E": 22000.0
      },
      "relevant_category": "G",
      "relevant_sales": 320000.0
    }

    Field explanation:
    - by_category        : ยอดขายแยกตามประเภทสินค้า (SKU ตัวแรก)
    - relevant_category : กลุ่มสินค้าที่มียอดขายสูงสุด
    - relevant_sales    : ยอดขายของกลุ่มนั้น
    ====================================================
    """

    conn = get_conn()
    inv = load_invoice_by_customer(conn, customer_code)
    conn.close()

    if inv.empty:
        return {
            "customer": customer_code,
            "anchor_date": anchor_date,
            "months": months,
            "by_category": {},
            "relevant_category": None,
            "relevant_sales": 0.0,
        }

    anchor, cutoff = resolve_anchor_and_cutoff(inv, months, anchor_date)
    if anchor is None:
        raise HTTPException(status_code=400, detail="ไม่สามารถกำหนด anchor date ได้")

    inv = inv[inv["Posting Date"] >= cutoff]
    inv["group"] = inv["No."].apply(classify_group)

    grp = (
        inv.groupby("group")["Amount Including VAT"]
        .sum()
        .sort_values(ascending=False)
    )

    return {
        "customer": customer_code,
        "anchor_date": anchor.date().isoformat(),
        "months": months,
        "by_category": {k: float(v) for k, v in grp.items()},
        "relevant_category": grp.index[0] if not grp.empty else None,
        "relevant_sales": float(grp.iloc[0]) if not grp.empty else 0.0,
    }
