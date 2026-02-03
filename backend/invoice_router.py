# backend/invoice_router.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
import requests
from datetime import datetime, timedelta

from config.config_external_api import (
    INVOICE_API_URL,
    INVOICE_API_HEADERS,
)


# ✅ ประกาศ prefix ที่ router เลย (เหมือน pricing / shipping)
router = APIRouter(
    prefix="/api/invoice",
    tags=["invoice"]
)


# -------------------------------------------------------
# Load invoice from API
# -------------------------------------------------------
def load_invoice_from_api(
    document_no: Optional[str] = None,
    customer_no: Optional[str] = None,
    posting_date: Optional[str] = None,
    limit: int = 200,
):
    """
    ดึงข้อมูล Invoice จาก D365 API
    """
    rows = []
    page = 1
    size = 200
    max_page = 5  # จำกัดไว้ 5 หน้า

    while True:
        payload = {
            "page": page,
            "size": size,
        }

        # เพิ่ม filter ถ้ามี
        if customer_no:
            payload["customer_code"] = {"$eq": customer_no}
        
        if document_no:
            payload["Document No."] = {"$eq": document_no}
        
        if posting_date:
            payload["Posting Date"] = {"$eq": posting_date}

        try:
            resp = requests.post(
                INVOICE_API_URL,
                json=payload,
                headers=INVOICE_API_HEADERS,
                timeout=30,
            )

            resp.raise_for_status()

            data = resp.json()
            items = data.get("data") or []

            if not items:
                break

            rows.extend(items)

            # ถ้าได้ครบตาม limit ที่ต้องการแล้ว หยุด
            if len(rows) >= limit:
                rows = rows[:limit]
                break

            if len(items) < size:
                break

            page += 1
            if page > max_page:
                break

        except Exception as e:
            print(f"❌ Error loading invoice from API: {e}")
            break

    return rows


# -------------------------------------------------------
# GET /api/invoice/list
# -------------------------------------------------------
@router.get("/list")
def list_invoice(
    document_no: Optional[str] = Query(None),
    customer_no: Optional[str] = Query(None),
    posting_date: Optional[str] = Query(None),
    limit: int = 200,
):
    """
    ดึงรายการ Invoice จาก D365 API
    """
    rows = load_invoice_from_api(
        document_no=document_no,
        customer_no=customer_no,
        posting_date=posting_date,
        limit=limit,
    )
    
    return rows


# -------------------------------------------------------
# GET /api/invoice/item-price-history
# -------------------------------------------------------
@router.get("/item-price-history")
def item_price_history(
    sku: str = Query(...),
    customerCode: str = Query(...),
    limit: int = Query(10),
):
    """
    ดึงประวัติราคาสินค้าจาก D365 API
    """
    rows = []
    page = 1
    size = 200
    max_page = 3

    # ดึงข้อมูล 6 เดือนย้อนหลัง
    today = datetime.today()
    date_from = (today - timedelta(days=180)).date().isoformat()

    while True:
        payload = {
            "page": page,
            "size": size,
            "customer_code": {"$eq": customerCode},
            "sku": {"$eq": sku},
            "Posting Date": {
                "$gte": date_from,
            },
        }

        try:
            resp = requests.post(
                INVOICE_API_URL,
                json=payload,
                headers=INVOICE_API_HEADERS,
                timeout=30,
            )

            resp.raise_for_status()

            data = resp.json()
            items = data.get("data") or []

            if not items:
                break

            rows.extend(items)

            if len(items) < size:
                break

            page += 1
            if page > max_page:
                break

        except Exception as e:
            print(f"❌ Error loading price history from API: {e}")
            break

    # แปลงเป็น DataFrame เพื่อ sort และ limit
    if not rows:
        return []

    df = pd.DataFrame(rows)
    
    # Sort by Posting Date (ใหม่สุดก่อน)
    df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")
    df = df.sort_values("Posting Date", ascending=False)
    
    # จำกัดจำนวน
    df = df.head(limit)

    return [
        {
            "invoiceNo": row.get("Document No."),
            "date": row.get("Posting Date"),
            "price": float(row.get("Unit Price") or 0),
            "qty": int(row.get("Quantity") or 0),
            "unit": row.get("Unit of Measure"),
        }
        for _, row in df.iterrows()
    ]


# -------------------------------------------------------
# GET /api/invoice/{document_no}
# -------------------------------------------------------
@router.get("/{document_no}")
def get_invoice(document_no: str):
    """
    ดึงรายละเอียด Invoice จาก D365 API
    """
    rows = load_invoice_from_api(document_no=document_no, limit=1000)

    if not rows:
        raise HTTPException(status_code=404, detail="Invoice not found")

    df = pd.DataFrame(rows)

    # สร้าง header จากแถวแรก
    first_row = df.iloc[0]
    header = {
        "document_no": document_no,
        "order_no": first_row.get("Order No."),
        "customer_no": first_row.get("customer_code") or first_row.get("Sell-to Customer No."),
        "customer_name": first_row.get("customer_name") or first_row.get("Sell-to Customer Name"),
        "posting_date": first_row.get("Posting Date"),
        "amount_including_vat": float(df["Amount Including VAT"].fillna(0).sum()),
    }

    # สร้าง lines
    lines = []
    for _, r in df.iterrows():
        lines.append({
            "sku": r.get("sku") or r.get("No."),
            "description": r.get("Description"),
            "unit": r.get("Unit of Measure"),
            "qty": int(r.get("Quantity") or 0),
            "unit_price": float(r.get("Unit Price") or 0),
            "amount": float(r.get("Amount") or 0),
            "variantCode": r.get("Variant Code"),
        })

    return {
        "header": header,
        "lines": lines,
    }
