# customer.py  --- ใช้ SQLite เต็มรูปแบบ
from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from db_sqlite import get_conn

router = APIRouter(prefix="/customer")


# ----------------------------------------
#  GET /customers  → ลูกค้าทั้งหมด
# ----------------------------------------
@router.get("/")
def get_customers():
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM "Customer"', conn)
    conn.close()
    return df.to_dict(orient="records")


# ----------------------------------------
#  /customers/search → ค้นหาด้วย code / phone / name
# ----------------------------------------
@router.get("/search")
def search_customer(
    code: str | None = Query(None),
    phone: str | None = Query(None),
    name: str | None = Query(None)
):
    if not code and not phone and not name:
        raise HTTPException(status_code=400, detail="กรุณาระบุ code, phone หรือ name อย่างน้อย 1 ค่า")

    conn = get_conn()

    # --- Load entire table (ง่ายที่สุด และรองรับ column ที่มี space) ---
    df = pd.read_sql_query('SELECT * FROM "Customer"', conn)
    conn.close()

    if df.empty:
        raise HTTPException(status_code=500, detail="Customer table is empty")

    def clean(x):
        if x is None:
            return ""
        if pd.isna(x):
            return ""
        return str(x).strip()

    # -------- 1) ค้นด้วยรหัสลูกค้า ------------
    found = pd.DataFrame()
    if code:
        found = df[df["Customer"].astype(str).str.strip() == str(code).strip()]

    # -------- 2) ค้นด้วยเบอร์โทร ------------
    if found.empty and phone:
        def normalize_phone(x):
            x = clean(x)
            return "".join(ch for ch in x if ch.isdigit())

        target = normalize_phone(phone)
        mask = df["Tel"].apply(lambda x: normalize_phone(x) == target)
        found = df[mask]

    # -------- 3) ค้นด้วยชื่อ ------------
    if found.empty and name:
        search_name = name.strip().lower()
        mask = df["Name"].astype(str).str.strip().str.lower().str.contains(search_name)
        found = df[mask]

    if found.empty:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลลูกค้า")

    r = found.iloc[0]

    # --------  ส่งข้อมูลกลับแบบ JSON  --------
        # --------  ส่งข้อมูลกลับแบบ JSON  --------
    base = {
        "id": clean(r["Customer"]),
        "name": clean(r["Name"]),
        "tax_no": clean(r["Tax No."]),
        "phone": clean(r["Tel"]),
        "gen_bus": clean(r["Gen Bus"]),
        "customer_date": clean(r["Customer Date"]),
        "payment_terms": clean(r["Payment Terms Code"]),
        "accum_6m": clean(r["Accum6m"]),
        "frequency": clean(r["Frequency"]),

        # sales แบบเดิม
        "sales_g_cust": clean(r["G"]),
        "sales_a_cust": clean(r["A"]),
        "sales_s_cust": clean(r["S"]),
        "sales_y_cust": clean(r["Y"]),
        "sales_c_cust": clean(r["C"]),
        "sales_e_cust": clean(r["E"]),
        "price_level": clean(r["E"]),
    }

    # ---------------------------------
    # ⭐ เพิ่ม Normalize Customer (ของใหม่)
    # ---------------------------------
    base["creditTerm"] = base["payment_terms"]

    # alias สำหรับ Pricing Model
    base["sales_g"] = base["sales_g_cust"]
    base["sales_a"] = base["sales_a_cust"]
    base["sales_s"] = base["sales_s_cust"]
    base["sales_y"] = base["sales_y_cust"]
    base["sales_c"] = base["sales_c_cust"]
    base["sales_e"] = base["sales_e_cust"]

    # relevantSales (ค่าที่มากที่สุด)
    try:
        vals = [
            float(base["sales_g"] or 0),
            float(base["sales_a"] or 0),
            float(base["sales_s"] or 0),
            float(base["sales_y"] or 0),
            float(base["sales_c"] or 0),
            float(base["sales_e"] or 0),
        ]
        base["relevantSales"] = max(vals)
    except:
        base["relevantSales"] = 0.0

    return base



