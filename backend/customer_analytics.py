# customer_analytics.py
# -----------------------------------------------------
# Customer Analytics API
# - ใช้ส่งข้อมูลให้ทีมอื่น / เพื่อน
# - ดึงข้อมูลจาก Database Cache (ไม่ต้องเรียก D365 API)
# - ไม่ผูกกับ pricing / quote flow
# -----------------------------------------------------

from fastapi import APIRouter, Query, HTTPException
from config.db_mssql import get_mssql_conn
from config.cache_config import USE_DATABASE_CACHE

router = APIRouter(
    prefix="/api/customer-analytics",
    tags=["customer-analytics"]
)

# =====================================================
# Helpers
# =====================================================

def get_customer_analytics_from_db(customer_code: str) -> dict:
    """
    ดึงข้อมูล analytics ของลูกค้าจาก database
    รวมข้อมูลตาม tax_no (ถ้ามี) แทนที่จะเป็น customer_code
    
    Returns:
        dict with customer analytics data
    """
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # ขั้นตอนที่ 1: หา tax_no ของลูกค้า
        query_tax = """
            SELECT tax_no
            FROM Customer
            WHERE customer_code = ?
        """
        
        cursor.execute(query_tax, (customer_code,))
        tax_row = cursor.fetchone()
        
        if not tax_row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลลูกค้า: {customer_code}")
        
        tax_no = tax_row.tax_no
        
        # ขั้นตอนที่ 2: รวมข้อมูลตาม tax_no (ถ้ามี) หรือ customer_code (ถ้าไม่มี tax_no)
        if tax_no and tax_no.strip():
            # รวมข้อมูลทุก customer_code ที่มี tax_no เดียวกัน
            query = """
                SELECT 
                    ? as customer_code,
                    MAX(customer_name) as customer_name,
                    SUM(ISNULL(accum_6m, 0)) as accum_6m,
                    SUM(ISNULL(frequency, 0)) as frequency,
                    SUM(ISNULL(sales_g_cust, 0)) as sales_g_cust,
                    SUM(ISNULL(sales_a_cust, 0)) as sales_a_cust,
                    SUM(ISNULL(sales_s_cust, 0)) as sales_s_cust,
                    SUM(ISNULL(sales_y_cust, 0)) as sales_y_cust,
                    SUM(ISNULL(sales_c_cust, 0)) as sales_c_cust,
                    SUM(ISNULL(sales_e_cust, 0)) as sales_e_cust,
                    MAX(calculation_date) as calculation_date
                FROM Customer
                WHERE tax_no = ? AND tax_no IS NOT NULL AND tax_no != ''
            """
            cursor.execute(query, (customer_code, tax_no))
        else:
            # ไม่มี tax_no ให้ใช้ customer_code เดิม
            query = """
                SELECT 
                    customer_code, customer_name, accum_6m, frequency,
                    sales_g_cust, sales_a_cust, sales_s_cust, 
                    sales_y_cust, sales_c_cust, sales_e_cust,
                    calculation_date
                FROM Customer
                WHERE customer_code = ?
            """
            cursor.execute(query, (customer_code,))
        
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"ไม่พบข้อมูลลูกค้า: {customer_code}")
        
        return {
            "customer_code": row.customer_code or "",
            "customer_name": row.customer_name or "",
            "accum_6m": float(row.accum_6m or 0),
            "frequency": int(row.frequency or 0),
            "sales_g_cust": float(row.sales_g_cust or 0),
            "sales_a_cust": float(row.sales_a_cust or 0),
            "sales_s_cust": float(row.sales_s_cust or 0),
            "sales_y_cust": float(row.sales_y_cust or 0),
            "sales_c_cust": float(row.sales_c_cust or 0),
            "sales_e_cust": float(row.sales_e_cust or 0),
            "calculation_date": str(row.calculation_date) if row.calculation_date else None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting customer analytics from database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ไม่สามารถดึงข้อมูล analytics ได้: {str(e)}"
        )


# =====================================================
# API 1: Monthly Summary (แยกรายเดือน)
# =====================================================
@router.get("/monthly-summary")
def customer_monthly_summary(
    customer_code: str = Query(..., description="รหัสลูกค้า เช่น 08015AY-1"),
    months: int = Query(6, ge=1, le=12, description="จำนวนเดือนย้อนหลัง (default = 6, รวมเดือนปัจจุบัน)"),
):
    """
    ดึงยอดซื้อแยกรายเดือน (รวมเดือนปัจจุบัน) จาก D365 API
    
    JSON Response:
    {
      "customer": "08015AY",
      "anchor_date": "2025-06-28",
      "months": 6,
      "monthly": [
        {"month": "2025-01", "amount": 1832844.36},
        {"month": "2025-02", "amount": 1390871.59},
        ...
      ],
      "total": 9917398.51
    }
    """
    
    try:
        import requests
        from datetime import datetime, timedelta
        from collections import defaultdict
        from config.config_external_api import INVOICE_API_URL, INVOICE_API_HEADERS
        
        # คำนวณวันที่เริ่มต้น (months เดือนย้อนหลัง รวมเดือนปัจจุบัน)
        today = datetime.today()
        anchor_date = today.date().isoformat()
        start_date = (today - timedelta(days=months * 31)).date().isoformat()
        
        # ดึงข้อมูล invoice จาก API
        all_invoices = []
        page = 1
        max_page = 10
        
        while page <= max_page:
            payload = {
                "page": page,
                "size": 200,
                "customer_code": {"$eq": customer_code},
                "Posting Date": {"$gte": start_date}
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
                
                all_invoices.extend(items)
                
                if len(items) < 200:
                    break
                    
                page += 1
                
            except Exception as e:
                print(f"❌ Error loading invoices from API (page {page}): {e}")
                break
        
        # จัดกลุ่มตามเดือน
        monthly_sales = defaultdict(float)
        
        for inv in all_invoices:
            posting_date = inv.get("Posting Date")
            if not posting_date:
                continue
            
            # แปลงวันที่เป็น YYYY-MM
            try:
                date_obj = datetime.fromisoformat(posting_date.replace("Z", "+00:00"))
                month_key = date_obj.strftime("%Y-%m")
                
                amount = float(inv.get("Amount Including VAT") or 0)
                monthly_sales[month_key] += amount
                    
            except Exception as e:
                print(f"⚠️ Error parsing date {posting_date}: {e}")
                continue
        
        # สร้าง monthly array (เรียงตามลำดับเดือน)
        monthly = []
        total = 0
        
        for month_key in sorted(monthly_sales.keys()):
            amount = monthly_sales[month_key]
            monthly.append({
                "month": month_key,
                "amount": round(amount, 2)
            })
            total += amount
        
        return {
            "customer": customer_code,
            "anchor_date": anchor_date,
            "months": months,
            "monthly": monthly,
            "total": round(total, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting monthly summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"ไม่สามารถดึงข้อมูลรายเดือนได้: {str(e)}"
        )


# =====================================================
# API 2: Category Summary (ใช้ข้อมูลจาก DB)
# =====================================================
@router.get("/category-summary")
def customer_category_summary(
    customer_code: str = Query(..., description="รหัสลูกค้า เช่น 08015AY-1"),
    months: int = Query(6, ge=1, le=24, description="จำนวนเดือนย้อนหลัง (ไม่ใช้งานแล้ว - fixed at 6)"),
    anchor_date: str | None = Query(
        None, description="วันที่อ้างอิง (ไม่ใช้งานแล้ว - ใช้ calculation_date จาก DB)"
    ),
):
    """
    ====================================================
    ✅ API นี้ใช้ข้อมูลจาก Database Cache
    ====================================================
    
    JSON Response:
    {
      "customer": "08015AY-1",
      "customer_name": "บริษัท ทดสอบ จำกัด",
      "calculation_date": "2025-02-09",
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
    - by_category        : ยอดขายแยกตามประเภทสินค้า (G, A, S, Y, C, E)
    - relevant_category  : กลุ่มสินค้าที่มียอดขายสูงสุด
    - relevant_sales     : ยอดขายของกลุ่มนั้น
    ====================================================
    """
    
    if not USE_DATABASE_CACHE:
        raise HTTPException(
            status_code=503,
            detail="API นี้ต้องการ USE_DATABASE_CACHE=True"
        )
    
    analytics = get_customer_analytics_from_db(customer_code)
    
    # สร้าง by_category dict
    by_category = {
        "G": analytics["sales_g_cust"],
        "A": analytics["sales_a_cust"],
        "S": analytics["sales_s_cust"],
        "Y": analytics["sales_y_cust"],
        "C": analytics["sales_c_cust"],
        "E": analytics["sales_e_cust"],
    }
    
    # หา category ที่มียอดสูงสุด
    relevant_category = max(by_category, key=by_category.get)
    relevant_sales = by_category[relevant_category]
    
    return {
        "customer": customer_code,
        "customer_name": analytics["customer_name"],
        "calculation_date": analytics["calculation_date"],
        "months": 6,  # Fixed at 6 months
        "by_category": by_category,
        "relevant_category": relevant_category if relevant_sales > 0 else None,
        "relevant_sales": relevant_sales,
    }
