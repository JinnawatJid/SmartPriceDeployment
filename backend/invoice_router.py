# backend/invoice_router.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
from db_sqlite import get_conn

# ✅ ประกาศ prefix ที่ router เลย (เหมือน pricing / shipping)
router = APIRouter(
    prefix="/api/invoice",
    tags=["invoice"]
)

TABLE_NAME = "Invoice"



# -------------------------------------------------------
# Load invoice
# -------------------------------------------------------
def load_invoice():
    conn = get_conn()
    df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}"', conn)
    conn.close()

    df.columns = [c.strip() for c in df.columns]
    return df


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
    df = load_invoice()
    if df.empty:
        return []

    if document_no:
        df = df[df["Document No."].astype(str).str.contains(document_no)]

    if customer_no:
        df = df[df["Sell-to Customer No."].astype(str).str.contains(customer_no)]

    if posting_date:
        df = df[df["Posting Date"].astype(str) == posting_date]

    return df.head(limit).to_dict(orient="records")


#Loadมาใช้ตรงDropdown

@router.get("/item-price-history")
def item_price_history(
    sku: str = Query(...),
    customerCode: str = Query(...),
    limit: int = Query(10),
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            "Document No."      AS invoiceNo,
            "Posting Date"      AS date,
            "Unit Price"        AS price
        FROM "Invoice"
        WHERE "No." = ?
          AND "Sell-to Customer No." = ?
        ORDER BY "Posting Date" DESC
        LIMIT ?
    """, (sku, customerCode, limit))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "invoiceNo": r[0],
            "date": r[1],
            "price": r[2],
        }
        for r in rows
    ]


# -------------------------------------------------------
# GET /api/invoice/{document_no}
# -------------------------------------------------------
@router.get("/{document_no}")
def get_invoice(document_no: str):
    df = load_invoice()
    df = df[df["Document No."].astype(str) == document_no]

    if df.empty:
        raise HTTPException(status_code=404, detail="Invoice not found")

    header = {
        "document_no": document_no,
        "order_no": df.iloc[0]["Order No."],
        "customer_no": df.iloc[0]["Sell-to Customer No."],
        "customer_name": df.iloc[0]["Sell-to Customer Name"],
        "posting_date": df.iloc[0]["Posting Date"],
        "amount_including_vat": float(df["Amount Including VAT"].sum()),
    }

    lines = []
    for _, r in df.iterrows():
        lines.append({
            "sku": r["No."],
            "description": r["Description"],
            "unit": r["Unit of Measure"],
            "qty": int(r["Quantity"] or 0),
            "unit_price": float(r["Unit Price"] or 0),
            "amount": float(r["Amount"] or 0),
            "variantCode": r.get("Variant Code"),
        })

    return {
        "header": header,
        "lines": lines,
    }


   
