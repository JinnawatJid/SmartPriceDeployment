import pandas as pd
import numpy as np
import math
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any

from LevelPrice import LevelPrice
from price import Price
from items import load_items_sqlite

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
    return math.ceil(x * 2) / 2


# -------------------------------
#  MAIN ENDPOINT
# -------------------------------
@router.post("/calculate")
async def calculate_pricing(req: PricingRequest = Body(...)):

    # No items
    if not req.cart:
        return {"items": [], "subtotal": 0, "customer_tier": "N/A"}

    # Load Items DB
    df_items = load_items_sqlite()
    if df_items.empty:
        raise HTTPException(500, "ไม่สามารถโหลด Items_Test")

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

    df_calc["payment_terms"] = (
        req.customerData.get("payment_terms")
        or req.customerData.get("paymentTerm")   # ⭐ ต้องเพิ่มบรรทัดนี้
        or req.customerData.get("creditTerm")
        or req.customerData.get("CreditTerm")
        or ""
    )

    
    print("ITEMS COLUMNS =", df_items.columns.tolist())
    # Merge item data
    merge_cols = [
        "sku", "name", "category", "cost", "product_weight",
        "priceR1", "priceR2", "priceW1", "priceW2","pkg_size","unit","Base Unit of Measure",
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
    # MAP relevantSales FROM FE (SAFE)
    # -----------------------------
    if "relevantSales" in df_calc.columns:
        df_calc["_RelevantSales"] = pd.to_numeric(
            df_calc["relevantSales"], errors="coerce"
        ).fillna(0)
    else:
        df_calc["_RelevantSales"] = 0




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


    # ⭐ FIX UNIT (Normal Mode)
    if "Base Unit of Measure" in df_price.columns:
        df_price["unit"] = df_price["Base Unit of Measure"]
    else:
        df_price["unit"] = ""


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

        })

    print(
    "\n=== PRODUCT WEIGHT CHECK ===\n",
    df_price[["sku", "product_weight"]].head().to_string(index=False)
)

    print("\n=== PRICING RESPONSE ITEMS (BACKEND) ===")
    for r in results:
        print(r["sku"], r.get("unit"))
    print("=== END PRICING RESPONSE ITEMS ===\n")

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
        "customer_tier": results[0]["_Tier_Z"] if results else "N/A",
    }
