import pandas as pd
import numpy as np
import math
import requests
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from LevelPrice import LevelPrice
from price import Price
from config.db_mssql import get_mssql_conn
from auth_dependency import get_branch_code


router = APIRouter(prefix="/api/pricing", tags=["pricing"])


# -------------------------------
#  MODELS
# -------------------------------
class CartItem(BaseModel):
    sku: str
    qty: float
    name: str
    price: float | None = None
    sqft_sheet: float | None = None
    
    pkg_size: float | None = None
    cost: float | None = None
    category: str | None = None
    unit: str | None = None
    product_weight: float | None = None
    relevantSales: float | None = None


class PricingRequest(BaseModel):
    customerData: Dict[str, Any]
    deliveryType: str
    cart: List[CartItem]


# -------------------------------
#  CATEGORY SALES MAPPING
# -------------------------------
def _num(x):
    try:
        v = pd.to_numeric(x, errors="coerce")
        return 0 if pd.isna(v) else float(v)
    except Exception:
        return 0



# -------------------------------
#  SAFE DEBUG
# -------------------------------
def _safe_print_df(df, cols, title):
    try:
        print("\n=== " + title)
        existing = [c for c in cols if c in df.columns]
        print(df[existing].head().to_string(index=False))
        print("===")
    except Exception:
        pass

def round_up_050(x: float) -> float:
    if x < 1:
        return round(x, 2)
    return math.ceil(x * 2) / 2

# -------------------------------
#  MAIN ENDPOINT
# -------------------------------
@router.post("/calculate")
async def calculate_pricing(req: PricingRequest = Body(...), branch_code: str = Depends(get_branch_code)):

    # No items
    if not req.cart:
        return {"items": [], "subtotal": 0, "customer_tier": "N/A"}
    
    # ⭐ ไม่ต้องดึง product_group จาก SKU ตัวแรกแล้ว
    # จะใช้ category (Inventory_Posting_Group) ของแต่ละสินค้าแทน
    
    print(f"🔍 DEBUG: Branch Code from JWT: '{branch_code}'")
    print(f"🔍 DEBUG: All SKUs in cart: {[item.sku for item in req.cart]}")
    print(f"🔍 DEBUG: Customer Data keys: {list(req.customerData.keys())}")

    # Load Items DB
    def load_items_by_skus(skus: list[str]) -> pd.DataFrame:
        if not skus:
            return pd.DataFrame()

        conn = get_mssql_conn()
        placeholders = ",".join(["?"] * len(skus))

        # Updated to use Item_Master + Item_Price with branch filtering
        sql = f"""
            SELECT
                im.SKU AS sku,
                im.No_2 AS sku2,
                im.Inventory_Posting_Group AS category,
                im.Base_Unit_of_Measure,
                ip.PackageSize AS pkg_size,
                0 AS Product_Weight,
                0 AS Sqft_Sheet,
                ip.R1, ip.R2, ip.W1, ip.W2,
                im.Product_Group,
                im.Product_Sub_Group,
                ip.AlternateName,
                0 AS RE
            FROM Item_Master im
            LEFT JOIN Item_Price ip ON im.SKU = ip.SKU AND ip.BranchCode = ?
            WHERE im.SKU IN ({placeholders})
        """

        # Add branch_code as first parameter, then SKUs
        params = [branch_code] + skus
        print(f"🔍 DEBUG SQL: branch_code='{branch_code}', skus={skus[:3]}...")  # Show first 3 SKUs
        df = pd.read_sql(sql, conn, params=params)
        conn.close()

        if df.empty:
            return df

        # normalize price columns (เหมือนของเดิม)
        for c in ["R1", "R2", "W1", "W2"]:
            df[f"price{c}"] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        
        print(f"🔍 DEBUG: Loaded {len(df)} items, sample prices:")
        if not df.empty:
            print(df[["sku", "R1", "R2", "priceR1", "priceR2"]].head(3).to_string(index=False))

        df["pkg_size"] = pd.to_numeric(df.get("pkg_size"), errors="coerce").fillna(1)
        df["product_weight"] = pd.to_numeric(df.get("Product_Weight"), errors="coerce").fillna(0)

        return df


    # Cart → DataFrame
    df_calc = pd.DataFrame([item.model_dump() for item in req.cart])

    df_calc["Pieces"] = pd.to_numeric(df_calc["qty"], errors="coerce").fillna(0)

    # sqft_sheet (จาก FE) = ตารางฟุตต่อแผ่น (ถ้าไม่มีให้เป็น 0)
    df_calc["Sqft_Sheet"] = pd.to_numeric(df_calc.get("sqft_sheet", 0), errors="coerce").fillna(0)


    # Category from SKU
    df_calc["category"] = (
        df_calc["category"]
        if "category" in df_calc.columns
        else df_calc["sku"].astype(str).str[0].str.upper()
    )
    
    df_calc["Quantity"] = np.where(
        df_calc["category"].astype(str).str.upper() == "G",
        df_calc["Pieces"] * df_calc["Sqft_Sheet"],   # ✅ กระจก: sqft รวม
        df_calc["Pieces"]                            # ✅ อื่น ๆ: ชิ้น/เส้น
    )


    # Attach customer data
    for k, v in req.customerData.items():
        df_calc[k] = v
    
    # ⭐ ไม่ต้องเพิ่ม product_group แบบเดิมแล้ว
    # จะใช้ category ของแต่ละสินค้าแทน

    df_calc["payment_terms"] = (
        req.customerData.get("payment_terms")
        or req.customerData.get("paymentTerm")   # ⭐ ต้องเพิ่มบรรทัดนี้
        or req.customerData.get("creditTerm")
        or req.customerData.get("CreditTerm")
        or ""
    )

    # ✅ FIX: โหลด items เฉพาะ SKU ใน cart
    cart_skus = df_calc["sku"].dropna().astype(str).unique().tolist()
    df_items = load_items_by_skus(cart_skus)

    if df_items.empty:
        raise HTTPException(500, "ไม่สามารถโหลด Item_Master ตาม SKU ใน cart")

    print("ITEMS COLUMNS =", df_items.columns.tolist())
    # Merge item data
    merge_cols = [
        "sku",
        "category",
        "RE",
        "product_weight",
        "priceR1", "priceR2", "priceW1", "priceW2",
        "pkg_size",
        "Base_Unit_of_Measure",
    ]
    safe_merge_cols = [c for c in merge_cols if c in df_items.columns]


    # ✅ Ensure pkg_size exists and usable (priority: FE > master > 1)
    df_calc["pkg_size"] = pd.to_numeric(df_calc.get("pkg_size", 1), errors="coerce")

    if "pkg_size_y" in df_calc.columns:
        # ถ้า merge แล้วเกิดซ้ำชื่อ (มีทั้งจาก FE และ master)
        master_pkg = pd.to_numeric(df_calc["pkg_size_y"], errors="coerce")
        df_calc["pkg_size"] = df_calc["pkg_size"].fillna(master_pkg)

    df_calc["pkg_size"] = df_calc["pkg_size"].fillna(1)
    df_calc.loc[df_calc["pkg_size"] <= 0, "pkg_size"] = 1

    
    df_calc = df_calc.merge(df_items[safe_merge_cols], on="sku", how="left")
    if "Base Unit of Measure" in df_calc.columns:
        df_calc["unit"] = df_calc["Base Unit of Measure"]
    else:
        df_calc["unit"] = ""

    # ✅ FIX: normalize cost column ให้เป็น cost (ตามที่โค้ดด้านล่างใช้)
    if "Cost" in df_calc.columns and "cost" not in df_calc.columns:
        df_calc["cost"] = pd.to_numeric(df_calc["Cost"], errors="coerce").fillna(0)
    else:
        df_calc["cost"] = pd.to_numeric(df_calc.get("cost", 0), errors="coerce").fillna(0)



    print("\n=== AFTER MERGE UNIT CHECK ===")
    print(df_calc[["sku", "unit"]].head(10).to_string(index=False))
    print("=== END AFTER MERGE UNIT CHECK ===\n")



    # Normalize category
    if "category" not in df_calc.columns or df_calc["category"].isna().all():
        df_calc["category"] = df_calc["sku"].astype(str).str[0].str.upper()


    # Normal qty / Aluminium Weight
    # ensure product_weight exists and is numeric
    df_calc["product_weight"] = (
        pd.to_numeric(df_calc.get("product_weight_x"), errors="coerce")
        .fillna(pd.to_numeric(df_calc.get("product_weight_y"), errors="coerce"))
        .fillna(0)
    )
    # FIX: Aluminium ต้องมีน้ำหนักอย่างน้อย 1
    df_calc.loc[
        (df_calc["category"].astype(str).str.upper() == "A") &
        (df_calc["product_weight"] <= 0),
        "product_weight"
    ] = 1



    # DeliveryType
    df_calc["DeliveryType"] = "1" if req.deliveryType.upper() == "PICKUP" else "0"

    # -----------------------------
    # MAP relevantSales FROM CUSTOMER DATA (ตาม category ของแต่ละสินค้า)
    # -----------------------------
    # ⭐ คำนวณ relevantSales ตาม category (Inventory_Posting_Group) ของแต่ละสินค้า
    print(f"🔍 DEBUG: Calculating relevantSales per item based on category")
    
    def get_relevant_sales_for_category(row):
        """คำนวณ relevantSales ตาม category ของสินค้า"""
        category = row.get('category', None)
        
        if not category or category not in ['G', 'A', 'S', 'Y', 'C', 'E']:
            # Fallback: ใช้ relevantSales จาก FE ถ้ามี
            return row.get('relevantSales', 0)
        
        sales_key = f"sales_{category.lower()}_cust"
        sales_value = row.get(sales_key, 0)
        
        print(f"  SKU {row.get('sku', 'N/A')}: category={category} → {sales_key}={sales_value}")
        
        return sales_value
    
    # Apply ให้แต่ละแถว
    df_calc["_RelevantSales"] = df_calc.apply(get_relevant_sales_for_category, axis=1)
    df_calc["_RelevantSales"] = pd.to_numeric(df_calc["_RelevantSales"], errors="coerce").fillna(0)




    # -------------------------------------------------------------
    # DEFAULT MODE NORMALIZATION
    # -------------------------------------------------------------
    customer_code = str(
        req.customerData.get("customerCode")
        or req.customerData.get("code")
        or req.customerData.get("CustomerCode")
        or ""
    ).strip()

    customer_code_norm = customer_code.upper()

    IS_DEFAULT_MODE = (
        customer_code_norm == ""
        or customer_code_norm in ["N/A", "NA", "NONE", "NULL", "-"]
    )

    # ✅ ถ้าเป็น Default Mode → บังคับให้ customer_code ว่าง
    # เพื่อให้เข้า block pricing R2 ด้านล่าง
    if IS_DEFAULT_MODE:
        print("\n>>> DEFAULT PRICE MODE: NO CUSTOMER CODE → USE R2\n")
        customer_code = ""




    if not customer_code:
        print("\n>>> DEFAULT PRICE MODE: NO CUSTOMER CODE → USE R2\n")

        # Tier_Z = 0 means R2
        df_calc["_Tier_Z"] = 0

        # ใช้ราคา R2 โดยตรง
        df_calc["NewPrice"] = pd.to_numeric(df_calc["priceR2"], errors="coerce").fillna(0)

        # ราคาต่อเส้น (Aluminium)
        df_calc["UnitPrice"] = df_calc.apply(
            lambda r: round_up_050(
                float(r["NewPrice"]) * float(r.get("product_weight", 0) or 0)
                if str(r.get("category","")).upper() == "A"
                else float(r["NewPrice"])
            ),
            axis=1
        )


        df_calc["LineTotal"] = df_calc["UnitPrice"] * df_calc["Quantity"]
        # ===== TOTAL CALC (MATCH NORMAL MODE) =====

        subtotal_gross = float(df_calc["LineTotal"].sum())

        shipping_customer_pay = float(
            req.customerData.get("shippingCustomerPay", 0) or 0
        )

        gross_before_vat = subtotal_gross + shipping_customer_pay

        subtotal = float(round(gross_before_vat / 1.07, 2))
        vat = float(round(gross_before_vat - subtotal, 2))

        product_total = gross_before_vat
        total_final = product_total


        # -----------------------------
        # Profit (DEFAULT MODE)
        # -----------------------------
        if "cost" in df_calc.columns:
            df_calc["cost"] = pd.to_numeric(df_calc["cost"], errors="coerce").fillna(0)

            def _compute_profit_default(row):
                if str(row.get("category", "")).upper() == "A":
                    unit_cost = float(row["cost"]) * float(row.get("product_weight", 0) or 0)
                    return (row["UnitPrice"] - unit_cost) * row["Quantity"]
                return (row["NewPrice"] - row["cost"]) * row["Quantity"]

            profit = float(df_calc.apply(_compute_profit_default, axis=1).sum())
        else:
            profit = 0



        results = []
        for _, row in df_calc.iterrows():
            is_glass = str(row.get("category", "")).upper() == "G"

            price_per_sheet = (
                round(row["UnitPrice"] * row.get("Sqft_Sheet", 0), 2)
                if is_glass
                else row["UnitPrice"]
            )

            results.append({
                "sku": row["sku"],
                "name": row.get("name"),
                "qty": row.get("Pieces", row["Quantity"]),
                "sqft_sheet": row.get("Sqft_Sheet", 0),
                "unit": row.get("unit", ""),
                "UnitPrice": row["UnitPrice"],
                "price_per_sheet": price_per_sheet,   # ⭐
                "_LineTotal": row["LineTotal"],
                "_Tier_Z": 0,
                "product_weight": float(row.get("product_weight", 0) or 0),
            })


        return {
            "items": results,
            "totals": {
                "subtotal": subtotal,
                "vat": vat,
                "product_total": product_total,
                "shippingCustomerPay": shipping_customer_pay,
                "total": total_final,
                "profit": profit,
            },
            "customer_tier": "R2",
        }


    # -------------------------------------------------------------
    # NORMAL FLOW (มี customer code → คำนวณด้วย LevelPrice, Price)
    # -------------------------------------------------------------

    _safe_print_df(df_calc,
                   ["sku", "name", "Quantity", "priceR1", "priceR2", "category"],
                   "AFTER MERGE ITEM DATA")
    
    

    
    # Run LevelPrice
    df_lp = LevelPrice(df_calc)
    
    df_lp["payment_terms"] = df_calc.get("payment_terms", "")

    # 🔥 FIX: ส่ง column ที่ Price ต้องใช้ "ตั้งแต่ตรงนี้"
    price_input_cols = [
        "sku",
        "Quantity",
        "pkg_size",
        "_RelevantSales",
        "DeliveryType",
    ]

    # กันพลาด: ถ้า col ไหนไม่มี ให้สร้าง default
    for c in price_input_cols:
        if c not in df_lp.columns:
            if c == "pkg_size":
                df_lp[c] = 1
            elif c == "Quantity":
                df_lp[c] = 0
            elif c == "DeliveryType":
                df_lp[c] = "0"

    # 👉 ตอนนี้ df_lp schema ตรงกับที่ Price.py ต้องการแล้ว
    df_price = Price(df_lp)
    
    # ⭐ เพิ่ม: ตรวจสอบประวัติราคาและใช้ราคาครั้งก่อนถ้าสูงกว่าราคาระบบ
    from config.config_external_api import INVOICE_API_URL, INVOICE_API_HEADERS
    from datetime import datetime, timedelta
    
    # ดึงข้อมูล Invoice 6 เดือนย้อนหลัง
    today = datetime.today()
    date_from = (today - timedelta(days=180)).date().isoformat()
    
    for idx, row in df_price.iterrows():
        sku = row["sku"]
        system_price = float(row["NewPrice"])
        
        try:
            # ดึงราคาล่าสุดจาก D365 API
            payload = {
                "page": 1,
                "size": 1,
                "customer_code": {"$eq": customer_code},
                "sku": {"$eq": sku},
                "Posting Date": {"$gte": date_from},
            }
            
            resp = requests.post(
                INVOICE_API_URL,
                json=payload,
                headers=INVOICE_API_HEADERS,
                timeout=10,
            )
            
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data") or []
                
                if items:
                    # Sort by Posting Date (ใหม่สุดก่อน)
                    items_sorted = sorted(
                        items, 
                        key=lambda x: x.get("Posting Date", ""), 
                        reverse=True
                    )
                    last_price = float(items_sorted[0].get("Unit Price") or 0)
                    
                    # ⭐ ถ้าราคาครั้งก่อนสูงกว่าราคาระบบ → ใช้ราคาครั้งก่อน
                    if last_price > system_price:
                        print(f"✅ SKU {sku}: ใช้ราคาครั้งก่อน {last_price:.2f} (สูงกว่าระบบ {system_price:.2f})")
                        df_price.at[idx, "NewPrice"] = last_price
                        df_price.at[idx, "price_source"] = "history"  # ⭐ เพิ่ม flag
                    else:
                        df_price.at[idx, "price_source"] = "system"
                else:
                    df_price.at[idx, "price_source"] = "system"
            else:
                df_price.at[idx, "price_source"] = "system"
                
        except Exception as e:
            print(f"⚠️ ไม่สามารถตรวจสอบประวัติราคาสำหรับ SKU {sku}: {e}")
            df_price.at[idx, "price_source"] = "system"


    # ⭐ FIX UNIT (Normal Mode)
    if "Base_Unit_of_Measure" in df_calc.columns:
        df_calc["unit"] = df_calc["Base_Unit_of_Measure"]
    else:
        df_calc["unit"] = ""



    print("\n=== AFTER PRICE UNIT CHECK ===")
    if "unit" in df_price.columns:
        print(df_price[["sku", "unit"]].head(10).to_string(index=False))
    else:
        print("⚠️ unit column NOT FOUND in df_price")
        print("columns =", list(df_price.columns))
    print("=== END AFTER PRICE UNIT CHECK ===\n")





    def _compute_unit_price(row):
        raw = (
            float(row["NewPrice"]) * float(row.get("product_weight", 0) or 0)
            if str(row.get("category", "")).upper() == "A"
            else float(row["NewPrice"])
        )
        return round_up_050(raw)

    df_price["UnitPrice"] = df_price.apply(_compute_unit_price, axis=1)

    df_price["_LineTotal"] = df_price["UnitPrice"] * df_price["Quantity"]

    _safe_print_df(df_price, ["sku", "NewPrice", "_LineTotal"], "AFTER PRICE CALC")

    # Prepare return values


# ยอดรวมสินค้า (ราคาขายรวม VAT แล้ว)
    subtotal_gross = float(df_price["_LineTotal"].sum())
    shipping_customer_pay = float(
        req.customerData.get("shippingCustomerPay", 0) or 0
    )

    # 👉 รวมสินค้า + ค่าขนส่ง
    gross_before_vat = subtotal_gross + shipping_customer_pay

    # 👉 คิด VAT จากยอดรวม
    subtotal = float(round(gross_before_vat / 1.07, 2))
    vat = float(round(gross_before_vat - subtotal, 2))

    # 👉 ยอดสุทธิ
    product_total = gross_before_vat
    total_final = product_total


    # Profit
    if "cost" in df_price.columns:
        df_price["cost"] = pd.to_numeric(df_price["cost"], errors="coerce").fillna(0)
        def _compute_profit(row):
            if str(row.get("category", "")).upper() == "A":
                unit_cost = float(row.get("cost", 0)) * float(row.get("product_weight", 0) or 0)
                return (row["UnitPrice"] - unit_cost) * row["Quantity"]
            return (row["NewPrice"] - float(row.get("cost", 0))) * row["Quantity"]

        profit = float(df_price.apply(_compute_profit, axis=1).sum())

    else:
        profit = 0

    results = []
    for _, row in df_price.iterrows():
        
        is_glass = str(row.get("category", "")).upper() == "G"

        price_per_sheet = (
            round(row["UnitPrice"] * row.get("Sqft_Sheet", 0), 2)
            if is_glass
            else row["UnitPrice"]
        )

        results.append({
            "sku": row["sku"],
            "name": row.get("name"),
            "qty": row.get("Pieces", row["Quantity"]),
            "sqft_sheet": row.get("Sqft_Sheet", 0),
            "unit": row.get("unit", ""),
            "UnitPrice": row["UnitPrice"],          # ยังส่งไว้ (เผื่อใช้)
            "price_per_sheet": price_per_sheet,     # ⭐ ตัวใหม่
            "_LineTotal": row["_LineTotal"],
            "_Tier_Z": row["_Tier_Z"],
            "product_weight": float(row.get("product_weight", 0) or 0),
            "price_source": row.get("price_source", "system"),  # ⭐ เพิ่ม flag

        })

    print(
    "\n=== PRODUCT WEIGHT CHECK ===\n",
    df_price[["sku", "product_weight"]].head().to_string(index=False)
)

    print("\n=== PRICING RESPONSE ITEMS (BACKEND) ===")
    for r in results:
        print(r["sku"], r.get("unit"))
    print("=== END PRICING RESPONSE ITEMS ===\n")

    # FIX: Sanitize NaNs for JSON compliance
    def sanitize(val):
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return 0.0 # or None
        return val

    sanitized_results = [
        {k: sanitize(v) for k, v in item.items()}
        for item in results
    ]

    sanitized_totals = {
        "subtotal": sanitize(subtotal),
        "vat": sanitize(vat),
        "product_total": sanitize(product_total),
        "shippingCustomerPay": sanitize(shipping_customer_pay),
        "total": sanitize(total_final),
        "profit": sanitize(profit),
    }

    return {
        "items": sanitized_results,
        "totals": sanitized_totals,
        "customer_tier": results[0]["_Tier_Z"] if results else "N/A",
    }
