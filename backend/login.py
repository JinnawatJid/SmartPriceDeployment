# login.py — ใช้ Employee API
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt, os, httpx

from config.config_external_api import EMP_API_URL, EMP_API_HEADERS

router = APIRouter(prefix="/login", tags=["auth"])

# === CONFIG ===
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-this")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = 12


# === SCHEMA ===
class LoginRequest(BaseModel):
    employeeCode: str


# === HELPER ===
async def load_employee(code: str):
    """
    ดึงข้อมูลพนักงานจาก API
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                EMP_API_URL,
                headers=EMP_API_HEADERS,
            )
            response.raise_for_status()
            data = response.json()
            
            # API ส่งมาเป็น dict with 'data' key
            if isinstance(data, dict) and 'data' in data:
                employees = data['data']
            elif isinstance(data, list):
                employees = data
            else:
                employees = []
            
            # หาพนักงานที่ตรงกับ code
            for emp in employees:
                emp_code = str(emp.get("EmpCode", "")).strip()
                if emp_code.lower() == code.lower():
                    return {
                        "id": emp_code,
                        "name": str(emp.get("EmpName", "")).strip(),
                        "branchId": str(emp.get("EmpBrchCode", "")).strip() or None,
                    }
            
            return None
            
    except Exception as e:
        print(f"❌ Error fetching employee from API: {e}")
        return None


# === LOGIN ROUTE ===
@router.post("")
async def login(req: LoginRequest):
    emp = await load_employee(req.employeeCode)
    if not emp:
        raise HTTPException(status_code=401, detail="รหัสพนักงานไม่ถูกต้อง")

    token = jwt.encode(
        {
            "sub": emp["id"],
            "name": emp["name"],
            "branchId": emp["branchId"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
        },
        JWT_SECRET,
        algorithm=JWT_ALG,
    )

    return {"token": token, "employee": emp}
