# customer.py  — SQLite Version (Derived Metrics from Invoice)
from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from datetime import datetime, timedelta
from db_sqlite import get_conn

router = APIRouter(prefix="/customer")

# =====================================================
# Helpers
# =====================================================
def clean(x):
    if x is None:
        return ""
    if pd.isna(x):
        return ""
    return str(x).strip()


def classify_group(no):
    """
    ใช้ตัวอักษรตัวแรกของ SKU
    G A S Y C E
    """
    if not isinstance(no, str) or len(no) == 0:
        return None
    return no[0].upper()


def load_customer_table(conn):
    return pd.read_sql_query('SELECT * FROM "Customer"', conn)


def load_invoice_by_customer(conn, customer_code):
    df = pd.read_sql_query(
        'SELECT * FROM "Invoice" WHERE "Sell-to Customer No." = ?',
        conn,
        params=[customer_code],
    )
    if not df.empty:
        df.columns = [c.strip() for c in df.columns]
    return df


# =====================================================
# GET /customer  → ลูกค้าทั้งหมด (master only)
# =====================================================
@router.get("/")
def get_customers():
    conn = get_conn()
    df = load_customer_table(conn)
    conn.close()
    return df.to_dict(orient="records")


# =====================================================
# GET /customer/search → ค้นหาลูกค้า + คำนวณ metric จาก Invoice
# =====================================================
@router.get("/search")
def search_customer(
    code: str | None = Query(None),
    phone: str | None = Query(None),
    name: str | None = Query(None),
):
    if not code and not phone and not name:
        raise HTTPException(
            status_code=400,
            detail="กรุณาระบุ code, phone หรือ name อย่างน้อย 1 ค่า",
        )

    conn = get_conn()

    # ---------- Load Customer master ----------
    df_cust = load_customer_table(conn)

    if df_cust.empty:
        conn.close()
        raise HTTPException(status_code=500, detail="Customer table is empty")

    found = pd.DataFrame()

    # 1) search by code
    if code:
        found = df_cust[df_cust["Customer"].astype(str).str.strip() == str(code).strip()]

    # 2) search by phone
    if found.empty and phone:
        def normalize_phone(x):
            return "".join(ch for ch in clean(x) if ch.isdigit())

        target = normalize_phone(phone)
        found = df_cust[
            df_cust["Tel"].apply(lambda x: normalize_phone(x) == target)
        ]

    # 3) search by name
    if found.empty and name:
        q = name.strip().lower()
        found = df_cust[
            df_cust["Name"].astype(str).str.strip().str.lower().str.contains(q)
        ]

    if found.empty:
        conn.close()
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลลูกค้า")

    r = found.iloc[0]
    customer_code = clean(r["Customer"])

    # =====================================================
    # Load Invoice (Fact)
    # =====================================================
    inv = load_invoice_by_customer(conn, customer_code)
    print("========== CUSTOMER METRIC DEBUG ==========")
    print("Customer:", customer_code)
    print("Invoice rows (all):", len(inv))

    if not inv.empty:
        print("Invoice Document No sample:")
        print(inv["Document No."].value_counts().head())

        print("Posting Date range:")
        print(inv["Posting Date"].min(), "→", inv["Posting Date"].max())

    # ---------- default metric ----------
    accum_6m = 0.0
    frequency = 0
    sales_g = sales_a = sales_s = sales_y = sales_c = sales_e = 0.0
    inv6 = inv.iloc[0:0]

    if not inv.empty:
        # parse date
        inv["Posting Date"] = pd.to_datetime(inv["Posting Date"], errors="coerce")

        anchor = inv["Posting Date"].max()
        if pd.isna(anchor):
            inv6 = inv.iloc[0:0]
        else:
            cutoff = anchor - timedelta(days=180)
            inv6 = inv[inv["Posting Date"] >= cutoff]


        if not inv6.empty:
            # Accum6m
            accum_6m = float(inv6["Amount Including VAT"].fillna(0).sum())

            # Frequency (count invoice)
            frequency = int(inv6["Document No."].nunique())

            # Group by SKU prefix
            inv6["group"] = inv6["No."].apply(classify_group)

            grp = (
                inv6
                .groupby("group")["Amount Including VAT"]
                .sum()
                .to_dict()
            )

            sales_g = float(grp.get("G", 0))
            sales_a = float(grp.get("A", 0))
            sales_s = float(grp.get("S", 0))
            sales_y = float(grp.get("Y", 0))
            sales_c = float(grp.get("C", 0))
            sales_e = float(grp.get("E", 0))

    print("Invoice rows (6M):", len(inv6))
    print("Frequency (distinct Document No.):", frequency)
    print("Accum6m:", accum_6m)

    print("Group sales:")
    print({
        "G": sales_g,
        "A": sales_a,
        "S": sales_s,
        "Y": sales_y,
        "C": sales_c,
        "E": sales_e,
    })
    print("==========================================")


    # =====================================================
    # Response (shape เดิม 100%)
    # =====================================================
    base = {
        "id": customer_code,
        "name": clean(r["Name"]),
        "tax_no": clean(r.get("Tax No.")),
        "phone": clean(r.get("Tel")),
        "gen_bus": clean(r.get("Gen Bus")),
        "customer_date": clean(r.get("Customer Date")),
        "payment_terms": clean(r.get("Payment Terms Code")),

        # ---- Derived metrics (แทน Excel เดิม) ----
        "accum_6m": accum_6m,
        "frequency": frequency,

        "sales_g_cust": sales_g,
        "sales_a_cust": sales_a,
        "sales_s_cust": sales_s,
        "sales_y_cust": sales_y,
        "sales_c_cust": sales_c,
        "sales_e_cust": sales_e,

        # เดิมใช้ E เป็น price level
        "price_level": sales_e,
    }

    # alias สำหรับ Pricing Model (เหมือนเดิม)
    base["creditTerm"] = base["payment_terms"]

    base["sales_g"] = base["sales_g_cust"]
    base["sales_a"] = base["sales_a_cust"]
    base["sales_s"] = base["sales_s_cust"]
    base["sales_y"] = base["sales_y_cust"]
    base["sales_c"] = base["sales_c_cust"]
    base["sales_e"] = base["sales_e_cust"]

    # relevantSales
    try:
        base["relevantSales"] = max(
            base["sales_g"],
            base["sales_a"],
            base["sales_s"],
            base["sales_y"],
            base["sales_c"],
            base["sales_e"],
        )
    except Exception:
        base["relevantSales"] = 0.0

    return base


# =====================================================
# GET /customer/search-list → dropdown
# =====================================================
@router.get("/search-list")
def search_customer_list(
    q: str = Query(..., min_length=1),
):
    conn = get_conn()
    df = load_customer_table(conn)
    conn.close()

    if df.empty:
        return []

    q_clean = q.strip().lower()

    def normalize_phone(x):
        return "".join(ch for ch in clean(x) if ch.isdigit())

    q_phone = normalize_phone(q)

    mask = (
        df["Customer"].astype(str).str.strip().str.lower().str.contains(q_clean)
        | df["Name"].astype(str).str.strip().str.lower().str.contains(q_clean)
        | df["Tel"].apply(lambda x: normalize_phone(x).startswith(q_phone) if q_phone else False)
    )

    found = df[mask].head(15)

    return [
        {
            "id": clean(r["Customer"]),
            "name": clean(r["Name"]),
            "phone": clean(r["Tel"]),
            "tax_no": clean(r.get("Tax No.")),
        }
        for _, r in found.iterrows()
    ]
