# backend/invoice_router.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta

from config.db_mssql import get_mssql_conn


# ✅ ประกาศ prefix ที่ router เลย (เหมือน pricing / shipping)
router = APIRouter(
    prefix="/api/invoice",
    tags=["invoice"]
)


# -------------------------------------------------------
# Load invoice from Database
# -------------------------------------------------------
def load_invoice_from_db(
    document_no: Optional[str] = None,
    customer_no: Optional[str] = None,
    posting_date: Optional[str] = None,
    limit: int = 200,
):
    """
    ดึงข้อมูล Invoice จาก MSSQL Database
    """
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        # สร้าง SQL query
        sql = "SELECT TOP (?) Document_No, Order_No, customer_code, Sell_to_Customer_Name, "
        sql += "Posting_Date, sku, Description, Variant_Code, Quantity, Unit_of_Measure, "
        sql += "Unit_Price, Line_Amount, Line_Amount_Include_VAT "
        sql += "FROM dbo.Invoice WHERE 1=1"
        
        params = [limit]
        
        # เพิ่ม filter ถ้ามี
        if customer_no:
            sql += " AND customer_code = ?"
            params.append(customer_no)
        
        if document_no:
            sql += " AND Document_No = ?"
            params.append(document_no)
        
        if posting_date:
            sql += " AND Posting_Date = ?"
            params.append(posting_date)
        
        sql += " ORDER BY Posting_Date DESC"
        
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description]
        rows = []
        
        for row in cursor.fetchall():
            row_dict = {}
            for i, value in enumerate(row):
                col_name = columns[i]
                # แปลง column name ให้ตรงกับ format เดิมที่ API ส่งมา
                if col_name == "Document_No":
                    row_dict["Document No."] = value
                elif col_name == "Order_No":
                    row_dict["Order No."] = value
                elif col_name == "Sell_to_Customer_Name":
                    row_dict["Sell-to Customer Name"] = value
                elif col_name == "Posting_Date":
                    row_dict["Posting Date"] = value.isoformat() if value else None
                elif col_name == "Variant_Code":
                    row_dict["Variant Code"] = value
                elif col_name == "Unit_of_Measure":
                    row_dict["Unit of Measure"] = value
                elif col_name == "Unit_Price":
                    row_dict["Unit Price"] = float(value) if value else 0
                elif col_name == "Line_Amount":
                    row_dict["Amount"] = float(value) if value else 0
                elif col_name == "Line_Amount_Include_VAT":
                    row_dict["Amount Including VAT"] = float(value) if value else 0
                else:
                    row_dict[col_name] = value
            
            rows.append(row_dict)
        
        return rows
        
    except Exception as e:
        print(f"❌ Error loading invoice from database: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


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
    ดึงรายการ Invoice จาก MSSQL Database
    """
    rows = load_invoice_from_db(
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
    ดึงประวัติราคาสินค้าจาก MSSQL Database
    """
    conn = get_mssql_conn()
    cursor = conn.cursor()
    
    try:
        # ดึงข้อมูล 6 เดือนย้อนหลัง
        today = datetime.today()
        date_from = (today - timedelta(days=180)).date()
        
        sql = """
        SELECT TOP (?)
            Document_No,
            Posting_Date,
            Unit_Price,
            Quantity,
            Unit_of_Measure
        FROM dbo.Invoice
        WHERE sku = ? 
            AND customer_code = ?
            AND Posting_Date >= ?
        ORDER BY Posting_Date DESC
        """
        
        cursor.execute(sql, [limit, sku, customerCode, date_from])
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "invoiceNo": row[0],
                "date": row[1].isoformat() if row[1] else None,
                "price": float(row[2]) if row[2] else 0,
                "qty": int(row[3]) if row[3] else 0,
                "unit": row[4],
            })
        
        return results
        
    except Exception as e:
        print(f"❌ Error loading price history from database: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# -------------------------------------------------------
# GET /api/invoice/{document_no}
# -------------------------------------------------------
@router.get("/{document_no}")
def get_invoice(document_no: str):
    """
    ดึงรายละเอียด Invoice จาก MSSQL Database
    """
    rows = load_invoice_from_db(document_no=document_no, limit=1000)

    if not rows:
        raise HTTPException(status_code=404, detail="Invoice not found")

    df = pd.DataFrame(rows)

    # สร้าง header จากแถวแรก
    first_row = df.iloc[0]
    header = {
        "document_no": document_no,
        "order_no": first_row.get("Order No."),
        "customer_no": first_row.get("customer_code"),
        "customer_name": first_row.get("Sell-to Customer Name"),
        "posting_date": first_row.get("Posting Date"),
        "amount_including_vat": float(df["Amount Including VAT"].fillna(0).sum()),
    }

    # สร้าง lines
    lines = []
    for _, r in df.iterrows():
        lines.append({
            "sku": r.get("sku"),
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
