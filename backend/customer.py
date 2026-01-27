# customer.py — API Version (Customer + Invoice from D365)
from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from datetime import datetime, timedelta
import requests

from config.config_external_api import (
    CUSTOMER_API_URL,
    CUSTOMER_API_HEADERS,
    INVOICE_API_URL,
    INVOICE_API_HEADERS,
)

router = APIRouter(prefix="/api/customer")

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


# =====================================================
# Load Customer from API
# =====================================================
def load_customer_from_api():
    rows = []
    gen_bus_list = ["R", "W", "I", "P"]

    page = 1
    size = 100
    max_page = 50  # ⭐ เพิ่มจาก 10 → 50 (5000 รายการต่อ gen_bus)

    for gen_bus in gen_bus_list:
        page = 1
        print(f"📥 Loading customers for gen_bus={gen_bus}...")
        
        while True:
            payload = {
                "page": page,
                "size": size,
                "gen_bus": {"$eq": gen_bus},
            }

            try:
                resp = requests.post(
                    CUSTOMER_API_URL,
                    json=payload,
                    headers=CUSTOMER_API_HEADERS,
                    timeout=20,
                )
                resp.raise_for_status()

                data = resp.json()
                items = data.get("data") or data

                if not items:
                    print(f"  ✓ gen_bus={gen_bus} page={page}: No more data")
                    break

                rows.extend(items)
                print(f"  ✓ gen_bus={gen_bus} page={page}: Loaded {len(items)} customers (total: {len(rows)})")

                # ⭐ ถ้าได้น้อยกว่า size แสดงว่าหมดแล้ว
                if len(items) < size:
                    print(f"  ✓ gen_bus={gen_bus}: Completed (last page)")
                    break

                page += 1
                
                # ⭐ ป้องกัน infinite loop
                if page > max_page:
                    print(f"  ⚠️ gen_bus={gen_bus}: Reached max_page={max_page}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Error loading gen_bus={gen_bus} page={page}: {e}")
                break

    print(f"📊 Total customers loaded: {len(rows)}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # ---- map field ให้เหมือน SQLite เดิม ----
    rename_map = {
        "customer_code": "Customer",
        "customer_name": "Name",
        "phone": "Tel",
        "gen_bus": "Gen Bus",
        "payment_terms": "Payment Terms Code",
        "tax_no": "Tax No.",
        "customer_date": "Customer Date",
    }

    for src, dst in rename_map.items():
        if src in df.columns:
            df[dst] = df[src]

    return df


# =====================================================
# Load Invoice from API (6 months)
# =====================================================
def load_invoice_by_customer_api(customer_code: str):
    rows = []

    page = 1
    size = 200
    max_page = 5

    today = datetime.today()
    date_to = today.date().isoformat()
    date_from = (today - timedelta(days=180)).date().isoformat()

    while True:
        payload = {
            "page": page,
            "size": size,

            # ✅ ใช้ operator แบบ D365
            "customer_code": {"$eq": customer_code},
            "Posting Date": {
                "$gte": date_from,
                "$lte": date_to,
            },
        }

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

    return rows


# =====================================================
# GET /customer/search (รองรับทั้ง GET และ POST)
# =====================================================
@router.get("/search")
@router.post("/search")
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

    # ---------- Load Customer ----------
    try:
        df_cust = load_customer_from_api()
    except Exception as e:
        print(f"❌ Error loading customer from API: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"ไม่สามารถโหลดข้อมูลลูกค้าได้: {str(e)}"
        )

    if df_cust.empty:
        raise HTTPException(status_code=500, detail="Customer data is empty")

    found = pd.DataFrame()

    # search by code
    if code:
        found = df_cust[df_cust["Customer"].astype(str).str.strip() == str(code).strip()]

    # search by phone
    if found.empty and phone:
        def normalize_phone(x):
            return "".join(ch for ch in clean(x) if ch.isdigit())

        target = normalize_phone(phone)
        found = df_cust[
            df_cust["Tel"].apply(lambda x: normalize_phone(x) == target)
        ]

    # search by name
    if found.empty and name:
        q = name.strip().lower()
        found = df_cust[
            df_cust["Name"].astype(str).str.strip().str.lower().str.contains(q, na=False)
        ]

    if found.empty:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลลูกค้า")

    r = found.iloc[0]
    customer_code = clean(r["Customer"])

    # =====================================================
    # Load Invoice
    # =====================================================
    try:
        invoice_rows = load_invoice_by_customer_api(customer_code)
    except Exception as e:
        print(f"⚠️ Warning: Cannot load invoice for {customer_code}: {e}")
        invoice_rows = []  # ถ้าโหลด invoice ไม่ได้ ให้ใช้ค่าว่าง
    
    inv = pd.DataFrame(invoice_rows)

    accum_6m = 0.0
    frequency = 0
    sales_g = sales_a = sales_s = sales_y = sales_c = sales_e = 0.0
    inv6 = inv.iloc[0:0]

    if not inv.empty:
        if "No." not in inv.columns and "sku" in inv.columns:
            inv["No."] = inv["sku"]

        inv["Posting Date"] = pd.to_datetime(inv["Posting Date"], errors="coerce")

        anchor = inv["Posting Date"].max()
        if not pd.isna(anchor):
            cutoff = anchor - timedelta(days=180)
            inv6 = inv[inv["Posting Date"] >= cutoff]

        if not inv6.empty:
            accum_6m = float(inv6["Amount Including VAT"].fillna(0).sum())
            frequency = int(inv6["Document No."].nunique())

            inv6["group"] = inv6["No."].apply(classify_group)
            grp = inv6.groupby("group")["Amount Including VAT"].sum().to_dict()

            sales_g = float(grp.get("G", 0))
            sales_a = float(grp.get("A", 0))
            sales_s = float(grp.get("S", 0))
            sales_y = float(grp.get("Y", 0))
            sales_c = float(grp.get("C", 0))
            sales_e = float(grp.get("E", 0))

    # =====================================================
    # Response (เหมือนเดิม 100%)
    # =====================================================
    base = {
        "id": customer_code,
        "name": clean(r["Name"]),
        "tax_no": clean(r.get("Tax No.")),
        "phone": clean(r.get("Tel")),
        "gen_bus": clean(r.get("Gen Bus")),
        "customer_date": clean(r.get("Customer Date")),
        "payment_terms": clean(r.get("Payment Terms Code")),

        "accum_6m": accum_6m,
        "frequency": frequency,

        "sales_g_cust": sales_g,
        "sales_a_cust": sales_a,
        "sales_s_cust": sales_s,
        "sales_y_cust": sales_y,
        "sales_c_cust": sales_c,
        "sales_e_cust": sales_e,

        "price_level": sales_e,
    }

    base["creditTerm"] = base["payment_terms"]

    base["sales_g"] = base["sales_g_cust"]
    base["sales_a"] = base["sales_a_cust"]
    base["sales_s"] = base["sales_s_cust"]
    base["sales_y"] = base["sales_y_cust"]
    base["sales_c"] = base["sales_c_cust"]
    base["sales_e"] = base["sales_e_cust"]

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
# GET /customer/search-list → dropdown (autocomplete)
# =====================================================
@router.get("/search-list")
@router.post("/search-list")
def search_customer_list(
    q: str = Query(..., min_length=1),
):
    try:
        df = load_customer_from_api()
    except Exception as e:
        print(f"❌ Error loading customer list from API: {e}")
        return []

    if df.empty:
        return []

    q_clean = q.strip().lower()

    def normalize_phone(x):
        return "".join(ch for ch in clean(x) if ch.isdigit())

    q_phone = normalize_phone(q)

    mask = (
        df["Customer"].astype(str).str.strip().str.lower().str.contains(q_clean, na=False)
        | df["Name"].astype(str).str.strip().str.lower().str.contains(q_clean, na=False)
        | df["Tel"].apply(
            lambda x: normalize_phone(x).startswith(q_phone) if q_phone else False
        )
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

