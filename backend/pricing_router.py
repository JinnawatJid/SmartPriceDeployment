import pandas as pd
import numpy as np
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


class PricingRequest(BaseModel):
    customerData: Dict[str, Any]
    deliveryType: str
    cart: List[CartItem]


# -------------------------------
#  CATEGORY SALES MAPPING
# -------------------------------
def _get_relevant_sales(row):
    cat = str(row.get("category", "")).upper()
    if cat == "G": return row.get("sales_g", 0)
    if cat == "A": return row.get("sales_a", 0)
    if cat == "S": return row.get("sales_s", 0)
    if cat == "Y": return row.get("sales_y", 0)
    if cat == "C": return row.get("sales_c", 0)
    if cat == "E": return row.get("sales_e", 0)
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

    # Ensure correct types
    df_calc["qty"] = pd.to_numeric(df_calc["qty"], errors="coerce").fillna(0)

    # Category from SKU
    df_calc["category"] = df_calc.get("category") or df_calc["sku"].apply(lambda x: str(x)[0].upper())

    # Attach customer data
    for k, v in req.customerData.items():
        df_calc[k] = v

    # Merge item data
    merge_cols = [
        "sku", "name", "category", "cost", "product_weight",
        "priceR1", "priceR2", "priceW1", "priceW2",
    ]
    safe_merge_cols = [c for c in merge_cols if c in df_items.columns]

    df_calc = df_calc.merge(df_items[safe_merge_cols], on="sku", how="left")

    # Normalize category
    if "category_y" in df_calc.columns:
        df_calc["category"] = df_calc["category_y"].astype(str)

    # Normal qty / Aluminium Weight
    df_calc["product_weight"] = pd.to_numeric(df_calc.get("product_weight", 0), errors="coerce").fillna(0)

    def _compute_real_qty(row):
        if str(row.get("category", "")).upper() == "A":
            return float(row["qty"]) * float(row.get("product_weight", 0) or 0)
        return float(row["qty"])

    df_calc["Quantity"] = df_calc.apply(_compute_real_qty, axis=1)

    # DeliveryType
    df_calc["DeliveryType"] = "1" if req.deliveryType.upper() == "PICKUP" else "0"

    # Relevant sales (E score)
    df_calc["_RelevantSales"] = df_calc.apply(_get_relevant_sales, axis=1)


    # -------------------------------------------------------------
    # DEFAULT MODE: ถ้าไม่มีรหัสลูกค้า → ใช้ Tier = R2 (ราคาขายหน้าร้าน)
    # -------------------------------------------------------------
    customer_code = str(req.customerData.get("code") or "").strip()

    if not customer_code:
        print("\n>>> DEFAULT PRICE MODE: NO CUSTOMER CODE → USE R2\n")

        # Tier_Z = 0 means R2
        df_calc["_Tier_Z"] = 0

        # ใช้ราคา R2 โดยตรง
        df_calc["NewPrice"] = pd.to_numeric(df_calc["priceR2"], errors="coerce").fillna(0)

        # คำนวณจำนวนเงิน
        df_calc["LineTotal"] = df_calc["NewPrice"] * df_calc["Quantity"]

        subtotal = float(df_calc["LineTotal"].sum())
        vat = float(round(subtotal * 0.07, 2))
        product_total = float(round(subtotal + vat, 2))

        shipping_customer_pay = float(req.customerData.get("shippingCustomerPay", 0) or 0)
        total_final = float(round(product_total + shipping_customer_pay, 2))

        results = [
            {
                "sku": row["sku"],
                "name": row.get("name"),
                "qty": row["Quantity"],
                "NewPrice": row["NewPrice"],
                "_LineTotal": row["LineTotal"],
                "_Tier_Z": 0,  # R2
            }
            for _, row in df_calc.iterrows()
        ]

        return {
            "items": results,
            "totals": {
                "subtotal": subtotal,
                "vat": vat,
                "product_total": product_total,
                "shippingCustomerPay": shipping_customer_pay,
                "total": total_final,
                "profit": 0,
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
    _safe_print_df(df_lp, ["sku", "_Tier_Z", "_Score_Z"], "AFTER LEVEL PRICE")

    # Run Price()
    df_price = Price(df_lp)
    _safe_print_df(df_price, ["sku", "NewPrice", "_LineTotal"], "AFTER PRICE CALC")

    # Prepare return values
    subtotal = float((df_price["NewPrice"] * df_price["Quantity"]).sum())
    vat = float(round(subtotal * 0.07, 2))
    product_total = float(round(subtotal + vat, 2))
    shipping_customer_pay = float(req.customerData.get("shippingCustomerPay", 0) or 0)
    total_final = float(round(product_total + shipping_customer_pay, 2))

    # Profit
    if "cost" in df_price.columns:
        df_price["cost"] = pd.to_numeric(df_price["cost"], errors="coerce").fillna(0)
        profit = float(((df_price["NewPrice"] - df_price["cost"]) * df_price["Quantity"]).sum())
    else:
        profit = 0

    results = []
    for _, row in df_price.iterrows():
        results.append({
            "sku": row["sku"],
            "name": row.get("name"),
            "qty": row["Quantity"],
            "NewPrice": row["NewPrice"],
            "_LineTotal": row["NewPrice"] * row["Quantity"],
            "_Tier_Z": row["_Tier_Z"],
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
        "customer_tier": results[0]["_Tier_Z"] if results else "N/A",
    }
