# backend/shipping.py
from fastapi import APIRouter
from pydantic import BaseModel

# ✅ ประกาศ router (ไม่ใช่ FastAPI เดี่ยว)
router = APIRouter(prefix="/api/shipping", tags=["shipping"])

# === ตารางค่าประเภทรถ ===
VEHICLE_CONFIG = {
    "PICKUP": {"fuel_rate": 10, "avg_speed": 50, "fix_cost_per_hour": 36},
    "4 ล้อใหญ่": {"fuel_rate": 9.5, "avg_speed": 45, "fix_cost_per_hour": 46},
    "6 ล้อจิ๋ว ": {"fuel_rate": 9.0, "avg_speed": 45, "fix_cost_per_hour": 58},
    "6 ล้อเล็ก": {"fuel_rate": 7.0, "avg_speed": 45, "fix_cost_per_hour": 74},
    "6 ล้อใหญ่": {"fuel_rate": 5.0, "avg_speed": 45, "fix_cost_per_hour": 90},
    "10 ล้อ": {"fuel_rate": 4.5, "avg_speed": 40, "fix_cost_per_hour": 148},
}

# === Request Model ===
class ShippingRequest(BaseModel):
    vehicle_type: str
    distance_km: float
    unload_hours: float
    staff_count: int
    profit: float

# === API หลัก: คำนวณค่าขนส่ง ===
@router.post("/calculate")
def calculate_shipping(data: ShippingRequest):
    cfg = VEHICLE_CONFIG.get(data.vehicle_type.upper())
    if not cfg:
        return {"error": f"Unknown vehicle type: {data.vehicle_type}"}

    fuel_rate = cfg["fuel_rate"]
    avg_speed = cfg["avg_speed"]
    fix_cost = cfg["fix_cost_per_hour"]

    travel_hours = data.distance_km / avg_speed
    fuel_cost = (data.distance_km / fuel_rate) * 32
    fix_cost_total = (travel_hours + data.unload_hours) * fix_cost
    labor_cost = (72 + 55 * data.staff_count) * (travel_hours + data.unload_hours)
    shipping_cost = fuel_cost + fix_cost_total + labor_cost

    cap = data.profit * 0.05
    company_pay = min(shipping_cost, cap)
    customer_pay = max(0, shipping_cost - company_pay)
    
    print("\n=== SHIPPING DEBUG ===")
    print(f"Vehicle Type : {data.vehicle_type}")
    print(f"Distance (km): {data.distance_km}")
    print(f"Unload Hours : {data.unload_hours}")
    print(f"Staff Count  : {data.staff_count}")
    print(f"Profit Input : {data.profit}")
    print("--- Calculation ---")
    print(f"Travel Hours : {travel_hours}")
    print(f"Fuel Cost    : {fuel_cost}")
    print(f"Fix Cost     : {fix_cost_total}")
    print(f"Labor Cost   : {labor_cost}")
    print(f"Shipping Cost: {shipping_cost}")
    print(f"Cap (5%)     : {cap}")
    print(f"Company Pay  : {company_pay}")
    print(f"Customer Pay : {customer_pay}")

    return {
        "vehicle_type": data.vehicle_type.upper(),
        "travel_hours": round(travel_hours, 2),
        "fuel_cost": round(fuel_cost, 2),
        "fix_cost": round(fix_cost_total, 2),
        "labor_cost": round(labor_cost, 2),
        "shipping_cost": round(shipping_cost, 2),
        "shipping_cap": round(cap, 2),
        "company_pay": round(company_pay, 2),
        "customer_pay": round(customer_pay, 2),
    }
