# customer.py — MSSQL Database Version
from fastapi import APIRouter, Query, HTTPException
from config.db_mssql import get_mssql_conn

router = APIRouter(prefix="/api/customer")

# =====================================================
# Helpers
# =====================================================
def clean(x):
    if x is None:
        return ""
    return str(x).strip() if x else ""


# =====================================================
# Database Search Functions
# =====================================================

def search_customer_from_db(
    code: str | None = None,
    phone: str | None = None,
    name: str | None = None,
    product_group: str | None = None
) -> dict:
    """
    Search customer from database table.
    
    Args:
        code: Customer code for exact match
        phone: Phone number for normalized match
        name: Customer name for partial match
        product_group: Product group (G/A/S/Y/C/E) to calculate relevantSales
    
    Returns:
        Customer data with analytics
    """
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_parts = []
        params = []
        
        if code:
            where_parts.append("customer_code = ?")
            params.append(code.strip())
        elif phone:
            # Normalize phone (remove non-digits)
            normalized_phone = "".join(ch for ch in phone if ch.isdigit())
            where_parts.append("REPLACE(REPLACE(REPLACE(REPLACE(phone, '-', ''), ' ', ''), '(', ''), ')', '') LIKE ?")
            params.append(f"%{normalized_phone}%")
        elif name:
            where_parts.append("LOWER(customer_name) LIKE ?")
            params.append(f"%{name.strip().lower()}%")
        
        if not where_parts:
            raise HTTPException(status_code=400, detail="กรุณาระบุ code, phone หรือ name อย่างน้อย 1 ค่า")
        
        query = f"""
            SELECT TOP 1
                customer_code, customer_name, phone, tax_no, gen_bus,
                payment_terms, customer_date, accum_6m, frequency,
                sales_g_cust, sales_a_cust, sales_s_cust, sales_y_cust,
                sales_c_cust, sales_e_cust
            FROM Customer
            WHERE {' OR '.join(where_parts)}
        """
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูลลูกค้า")
        
        # Build response
        sales_g = float(row.sales_g_cust or 0)
        sales_a = float(row.sales_a_cust or 0)
        sales_s = float(row.sales_s_cust or 0)
        sales_y = float(row.sales_y_cust or 0)
        sales_c = float(row.sales_c_cust or 0)
        sales_e = float(row.sales_e_cust or 0)
        
        # Calculate relevant_sales based on product_group
        sales_map = {
            "G": sales_g,
            "A": sales_a,
            "S": sales_s,
            "Y": sales_y,
            "C": sales_c,
            "E": sales_e,
        }
        
        # If product_group is specified, use that group's sales
        # Otherwise, use max of all groups (backward compatible)
        if product_group and product_group.upper() in sales_map:
            relevant_sales = sales_map[product_group.upper()]
        else:
            relevant_sales = max(sales_g, sales_a, sales_s, sales_y, sales_c, sales_e)
        
        price_level = sales_e
        
        base = {
            "id": row.customer_code or "",
            "name": row.customer_name or "",
            "tax_no": row.tax_no or "",
            "phone": row.phone or "",
            "gen_bus": row.gen_bus or "",
            "customer_date": str(row.customer_date) if row.customer_date else "",
            "payment_terms": row.payment_terms or "",
            
            "accum_6m": float(row.accum_6m or 0),
            "frequency": int(row.frequency or 0),
            
            "sales_g_cust": sales_g,
            "sales_a_cust": sales_a,
            "sales_s_cust": sales_s,
            "sales_y_cust": sales_y,
            "sales_c_cust": sales_c,
            "sales_e_cust": sales_e,
            
            "price_level": price_level,
        }
        
        base["creditTerm"] = base["payment_terms"]
        
        base["sales_g"] = base["sales_g_cust"]
        base["sales_a"] = base["sales_a_cust"]
        base["sales_s"] = base["sales_s_cust"]
        base["sales_y"] = base["sales_y_cust"]
        base["sales_c"] = base["sales_c_cust"]
        base["sales_e"] = base["sales_e_cust"]
        
        base["relevantSales"] = relevant_sales
        
        cursor.close()
        conn.close()
        
        return base
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error searching customer from database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ไม่สามารถค้นหาข้อมูลลูกค้าได้: {str(e)}"
        )


# =====================================================
# GET /customer/search (รองรับทั้ง GET และ POST)
# =====================================================
@router.get("/search")
@router.post("/search")
def search_customer(
    code: str | None = Query(None),
    phone: str | None = Query(None),
    name: str | None = Query(None),
    product_group: str | None = Query(None, description="Product group (G/A/S/Y/C/E) for relevantSales calculation"),
):
    """
    ค้นหาลูกค้าจาก MSSQL Database
    
    Parameters:
        - code: รหัสลูกค้า (exact match)
        - phone: เบอร์โทรศัพท์ (partial match)
        - name: ชื่อลูกค้า (partial match)
        - product_group: กลุ่มสินค้า (G/A/S/Y/C/E) สำหรับคำนวณ relevantSales
    
    Returns:
        Customer data with analytics from database
        
    Examples:
        - /api/customer/search?code=08015AY
        - /api/customer/search?code=08015AY&product_group=E
        - /api/customer/search?name=จำรัส&product_group=G
    """
    if not code and not phone and not name:
        raise HTTPException(
            status_code=400,
            detail="กรุณาระบุ code, phone หรือ name อย่างน้อย 1 ค่า",
        )
    
    # ใช้ MSSQL Database เท่านั้น
    return search_customer_from_db(code=code, phone=phone, name=name, product_group=product_group)

def search_customer_list_from_db(query: str) -> list:
    """
    Search customer list from database for autocomplete.
    Uses smart ranking: exact match first, then starts-with, then contains
    
    Args:
        query: Search query string
    
    Returns:
        List of customer summaries (max 15 results)
    """
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        q_clean = query.strip().lower()
        
        # Normalize phone query
        q_phone = "".join(ch for ch in query if ch.isdigit())
        
        # Smart search with ranking:
        # 1. Exact match (rank 1)
        # 2. Starts with (rank 2)
        # 3. Contains (rank 3)
        sql = """
            SELECT TOP 15
                customer_code, 
                customer_name, 
                phone, 
                tax_no,
                CASE
                    -- Exact match (highest priority)
                    WHEN LOWER(customer_code) = ? THEN 1
                    WHEN LOWER(customer_name) = ? THEN 1
                    -- Starts with (medium priority)
                    WHEN LOWER(customer_code) LIKE ? THEN 2
                    WHEN LOWER(customer_name) LIKE ? THEN 2
                    -- Contains (lowest priority)
                    ELSE 3
                END AS rank
            FROM Customer
            WHERE 
                LOWER(customer_code) LIKE ?
                OR LOWER(customer_name) LIKE ?
                OR REPLACE(REPLACE(REPLACE(REPLACE(phone, '-', ''), ' ', ''), '(', ''), ')', '') LIKE ?
            ORDER BY 
                rank ASC,
                LEN(customer_code) ASC,
                customer_name ASC
        """
        
        cursor.execute(sql, (
            q_clean,                    # exact match code
            q_clean,                    # exact match name
            f"{q_clean}%",              # starts with code
            f"{q_clean}%",              # starts with name
            f"%{q_clean}%",             # contains code
            f"%{q_clean}%",             # contains name
            f"%{q_phone}%"              # contains phone
        ))
        rows = cursor.fetchall()
        
        result = [
            {
                "id": row.customer_code or "",
                "name": row.customer_name or "",
                "phone": row.phone or "",
                "tax_no": row.tax_no or "",
            }
            for row in rows
        ]
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Error searching customer list from database: {e}")
        return []


# =====================================================
# GET /customer/search-list → dropdown (autocomplete)
# =====================================================
@router.get("/search-list")
@router.post("/search-list")
def search_customer_list(
    q: str = Query(..., min_length=1),
):
    """
    ค้นหารายชื่อลูกค้าจาก MSSQL Database (สำหรับ autocomplete)
    
    Parameters:
        - q: คำค้นหา (ค้นหาจาก code, name, phone)
    
    Returns:
        List of customers (max 15 results)
    """
    # ใช้ MSSQL Database เท่านั้น
    return search_customer_list_from_db(q)

