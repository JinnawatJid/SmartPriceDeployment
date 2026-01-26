from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import math

from config.db_mssql import get_mssql_conn   # ✅ FIX


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(prefix="/api/shipping", tags=["shipping"])


# =====================================================
# CONFIG รถ
# =====================================================

VEHICLE_CONFIG = {
    "PICKUP": {"fuel_rate": 10, "avg_speed": 50, "fix_cost_per_hour": 36},
    "4 ล้อใหญ่": {"fuel_rate": 9.5, "avg_speed": 45, "fix_cost_per_hour": 46},
    "6 ล้อจิ๋ว": {"fuel_rate": 9.0, "avg_speed": 45, "fix_cost_per_hour": 58},
    "6 ล้อเล็ก": {"fuel_rate": 7.0, "avg_speed": 45, "fix_cost_per_hour": 74},
    "6 ล้อใหญ่": {"fuel_rate": 5.0, "avg_speed": 45, "fix_cost_per_hour": 90},
    "10 ล้อ": {"fuel_rate": 4.5, "avg_speed": 40, "fix_cost_per_hour": 148},
}

FUEL_PRICE = 32  # บาท/ลิตร


# =====================================================
# MODELS (เดิม)
# =====================================================

class ShippingRequest(BaseModel):
    vehicle_type: str
    distance_km: float
    unload_hours: float
    staff_count: int
    profit: float


# =====================================================
# MODELS (จาก Cart)
# =====================================================

class CartLine(BaseModel):
    sku: str
    qty: float
    price: float
    category: Optional[str] = None
    product_weight: Optional[float] = 0
    sqft_sheet: Optional[float] = 0


class ShippingFromCartRequest(BaseModel):
    vehicle_type: str
    distance_km: float
    unload_hours: float
    staff_count: int
    cart: List[CartLine]


def round_shipping_baht(x: float) -> int:
    return int(math.floor(x))


# =====================================================
# 🔧 FIX: LOAD ITEMS BY SKU (แทน load_items_mssql)
# =====================================================

def load_items_by_skus(skus: list[str]) -> pd.DataFrame:
    if not skus:
        return pd.DataFrame()

    conn = get_mssql_conn()
    placeholders = ",".join(["?"] * len(skus))

    sql = f"""
        SELECT
            No AS sku,
            RE
        FROM Items_Test
        WHERE No IN ({placeholders})
    """

    df = pd.read_sql(sql, conn, params=skus)
    conn.close()

    return df


# =====================================================
# CORE: คำนวณ profit จาก Cart
# =====================================================

def compute_profit_from_cart(cart: List[CartLine]):
    if not cart:
        return 0.0, False

    df_cart = pd.DataFrame([c.model_dump() for c in cart])

    df_cart["qty"] = pd.to_numeric(df_cart["qty"], errors="coerce").fillna(0)
    df_cart["price"] = pd.to_numeric(df_cart["price"], errors="coerce").fillna(0)
    df_cart["product_weight"] = pd.to_numeric(
        df_cart.get("product_weight", 0), errors="coerce"
    ).fillna(0)
    df_cart["sqft_sheet"] = pd.to_numeric(
        df_cart.get("sqft_sheet", 0), errors="coerce"
    ).fillna(0)

    # ✅ FIX: โหลด cost เฉพาะ SKU ใน cart
    cart_skus = df_cart["sku"].dropna().astype(str).unique().tolist()
    df_items = load_items_by_skus(cart_skus)

    df = df_cart.merge(df_items, on="sku", how="left")
    df["cost"] = pd.to_numeric(df.get("RE"), errors="coerce").fillna(0)

    has_missing_cost = False

    def _profit(row):
        nonlocal has_missing_cost
        cost = row["cost"]

        if cost <= 0:
            has_missing_cost = True
            return 0

        category = (row.get("category") or row["sku"][:1]).upper()

        if category == "A":
            unit_cost = cost * row["product_weight"]
            return (row["price"] - unit_cost) * row["qty"]

        if category == "G":
            sqft = row["sqft_sheet"]
            if sqft <= 0:
                has_missing_cost = True
                return 0

            price_per_sheet = row["price"]
            price_per_sqft = price_per_sheet / sqft
            unit_profit = price_per_sqft - cost
            total_sqft = row["qty"] * sqft
            return unit_profit * total_sqft

        return (row["price"] - cost) * row["qty"]

    df["profit"] = df.apply(_profit, axis=1)

    print("\n--- PROFIT TABLE ---")
    print(
        df[
            [
                "sku",
                "qty",
                "price",
                "cost",
                "product_weight",
                "sqft_sheet",
                "profit",
            ]
        ].to_string(index=False)
    )
    print("--- END PROFIT TABLE ---\n")

    return float(df["profit"].sum()), has_missing_cost


# =====================================================
# CORE: คำนวณค่าขนส่ง
# =====================================================

def _calculate_shipping_cost(
    vehicle_type: str,
    distance_km: float,
    unload_hours: float,
    staff_count: int,
    profit: float,
):
    vt = vehicle_type.upper()
    cfg = VEHICLE_CONFIG.get(vt)
    if not cfg:
        raise HTTPException(400, f"Unknown vehicle type: {vehicle_type}")

    fuel_rate = cfg["fuel_rate"]
    avg_speed = cfg["avg_speed"]
    fix_cost = cfg["fix_cost_per_hour"]

    travel_hours = distance_km / avg_speed if avg_speed > 0 else 0
    fuel_cost = (distance_km / fuel_rate) * FUEL_PRICE if fuel_rate > 0 else 0
    fix_cost_total = (travel_hours + unload_hours) * fix_cost
    labor_cost = (72 + 55 * staff_count) * (travel_hours + unload_hours)

    shipping_cost = fuel_cost + fix_cost_total + labor_cost

    cap = max(0, profit) * 0.05
    company_pay = min(shipping_cost, cap)
    customer_pay = max(0, shipping_cost - company_pay)

    return {
        "travel_hours": round(travel_hours, 2),
        "fuel_cost": round(fuel_cost, 2),
        "fix_cost": round(fix_cost_total, 2),
        "labor_cost": round(labor_cost, 2),
        "shipping_cost": round(shipping_cost, 2),
        "shipping_cap": round(cap, 2),
        "company_pay": round_shipping_baht(company_pay),
        "customer_pay": round_shipping_baht(customer_pay),
    }


# =====================================================
# ENDPOINT เดิม
# =====================================================

@router.post("/calculate")
def calculate_shipping(data: ShippingRequest):
    result = _calculate_shipping_cost(
        vehicle_type=data.vehicle_type,
        distance_km=data.distance_km,
        unload_hours=data.unload_hours,
        staff_count=data.staff_count,
        profit=data.profit,
    )
    return {
        "vehicle_type": data.vehicle_type.upper(),
        **result,
    }


# =====================================================
# ENDPOINT: จาก Cart
# =====================================================

@router.post("/calculate_from_cart")
def calculate_shipping_from_cart(data: ShippingFromCartRequest):

    profit, has_missing_cost = compute_profit_from_cart(data.cart)

    result = _calculate_shipping_cost(
        vehicle_type=data.vehicle_type,
        distance_km=data.distance_km,
        unload_hours=data.unload_hours,
        staff_count=data.staff_count,
        profit=profit,
    )

    return {
        "vehicle_type": data.vehicle_type.upper(),
        "profit_for_shipping": round(profit, 2),
        "has_missing_cost": has_missing_cost,
        **result,
    }
