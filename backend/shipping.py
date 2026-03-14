from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import math
import requests
import logging

from config.db_mssql import get_mssql_conn   # ✅ FIX
from config.config_external_api import ITEMCOST_API_URL, ITEMCOST_API_HEADERS
from auth_dependency import get_branch_code

logger = logging.getLogger(__name__)


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
    isSoldByPack: Optional[bool] = False


class ShippingFromCartRequest(BaseModel):
    vehicle_type: str
    distance_km: float
    unload_hours: float
    staff_count: int
    location_code: str = ""  # ⭐ เพิ่มเพื่อดึงต้นทุนจาก API
    cart: List[CartLine]


def round_shipping_baht(x: float) -> int:
    return int(math.floor(x))


# =====================================================
# 🔧 FIX: FETCH ITEM COST FROM API
# =====================================================

def fetch_item_cost_from_api(item_no: str, location_code: str) -> Optional[float]:
    """
    ดึงต้นทุนสินค้าจาก ITEMCOST API (POST)
    
    Args:
        item_no: หมายเลขสินค้า (SKU)
        location_code: รหัสสาขา
    
    Returns:
        Unit_Cost หรือ None ถ้าไม่พบ
    """
    try:
        url = ITEMCOST_API_URL
        payload = {
            "Item_No": {"$eq": item_no},
            "Location_Code": {"$eq": location_code}
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=ITEMCOST_API_HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # API ส่งกลับ dict ที่มี "data" หรือ "value" key
            if isinstance(data, dict):
                items = data.get("data") or data.get("value") or []
            elif isinstance(data, list):
                items = data
            else:
                items = []
            
            # ดึง Unit_Cost จาก item แรก
            if items and len(items) > 0:
                return float(items[0].get("Unit_Cost", 0))
        
        logger.warning(f"Failed to fetch cost for {item_no} at {location_code}: {response.status_code} - {response.text}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error for {item_no}: {e}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing API response for {item_no}: {e}")
        return None


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
            SKU AS sku,
            RE,
            Product_Weight
        FROM Item_Master
        WHERE SKU IN ({placeholders})
    """

    df = pd.read_sql(sql, conn, params=skus)
    conn.close()

    return df


# =====================================================
# CORE: คำนวณ profit จาก Cart
# =====================================================

def compute_profit_from_cart(cart: List[CartLine], location_code: str = ""):
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

    # ✅ FIX: โหลด product_weight เฉพาะ SKU ใน cart
    cart_skus = df_cart["sku"].dropna().astype(str).unique().tolist()
    df_items = load_items_by_skus(cart_skus)

    df = df_cart.merge(df_items, on="sku", how="left")
    
    # ⭐ ดึงต้นทุนจาก API แทนคอลัมน์ RE
    df["cost"] = df["sku"].apply(
        lambda sku: fetch_item_cost_from_api(str(sku), location_code) or 0
    )
    
    # ⭐ ใช้ Product_Weight จาก Item_Master ถ้ามี (ถ้าไม่มีใช้จาก cart)
    df["product_weight"] = pd.to_numeric(
        df.get("Product_Weight"), errors="coerce"
    ).fillna(
        pd.to_numeric(df_cart.get("product_weight", 0), errors="coerce").fillna(0)
    )

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
            is_sold_by_pack = row.get("isSoldByPack", False)  # ⭐ เพิ่ม flag
            
            # ⭐ ถ้าขายยกแพ็ก ไม่คูณ sqft
            if is_sold_by_pack:
                return (row["price"] - cost) * row["qty"]
            
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
def calculate_shipping_from_cart(
    data: ShippingFromCartRequest,
    branch_code: str = Depends(get_branch_code)
):
    # ⭐ ใช้ branch_code จาก JWT token หรือ location_code จาก request
    location_code = data.location_code or branch_code

    profit, has_missing_cost = compute_profit_from_cart(data.cart, location_code)

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
