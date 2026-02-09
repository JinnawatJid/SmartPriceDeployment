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
    
    Returns:
        dict with customer analytics data
    """
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
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
# API 1: Monthly Summary (Simplified - ใช้ข้อมูลจาก DB)
# =====================================================
@router.get("/monthly-summary")
def customer_monthly_summary(
    customer_code: str = Query(..., description="รหัสลูกค้า เช่น 08015AY-1"),
    months: int = Query(6, ge=1, le=24, description="จำนวนเดือนย้อนหลัง (default = 6)"),
    anchor_date: str | None = Query(
        None, description="วันที่อ้างอิง (ไม่ใช้งานแล้ว - ใช้ calculation_date จาก DB)"
    ),
):
    """
    ====================================================
    ⚠️ API นี้ถูกปรับให้ใช้ข้อมูลจาก Database Cache
    ====================================================
    
    เนื่องจากข้อมูลถูกคำนวณไว้แล้วใน table Customer (6 เดือนย้อนหลัง)
    API นี้จึงส่งข้อมูล summary กลับไปแทน
    
    ถ้าต้องการข้อมูลรายเดือนแบบละเอียด ต้องเก็บ Invoice ลง DB ด้วย
    
    JSON Response:
    {
      "customer": "08015AY-1",
      "customer_name": "บริษัท ทดสอบ จำกัด",
      "calculation_date": "2025-02-09",
      "months": 6,
      "total": 218000.50,
      "frequency": 15,
      "note": "ข้อมูลจาก database cache (6 เดือนย้อนหลัง)"
    }
    ====================================================
    """
    
    if not USE_DATABASE_CACHE:
        raise HTTPException(
            status_code=503,
            detail="API นี้ต้องการ USE_DATABASE_CACHE=True"
        )
    
    analytics = get_customer_analytics_from_db(customer_code)
    
    return {
        "customer": customer_code,
        "customer_name": analytics["customer_name"],
        "calculation_date": analytics["calculation_date"],
        "months": 6,  # Fixed at 6 months (ตามที่เก็บใน DB)
        "total": analytics["accum_6m"],
        "frequency": analytics["frequency"],
        "note": "ข้อมูลจาก database cache (6 เดือนย้อนหลัง) - ไม่มีรายละเอียดรายเดือน",
    }


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
