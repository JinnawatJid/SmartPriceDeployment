# login.py — ใช้ Employee API
from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt, os, httpx

from config.config_external_api import EMP_API_URL, EMP_API_HEADERS

router = APIRouter(tags=["auth"])

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
@router.post("/login")
async def login(req: LoginRequest, response: Response):
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

    # Set HttpOnly cookie
    is_prod = os.getenv("ENVIRONMENT", "development").lower() == "production"
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600
    )

    return {"token": token, "employee": emp}

@router.get("/auth/me")
async def get_me(request: Request):
    token = request.cookies.get("auth_token")
    if not token:
        # Fallback to Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return {"employee": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/auth/logout")
async def logout(response: Response):
    is_prod = os.getenv("ENVIRONMENT", "development").lower() == "production"
    response.delete_cookie(
        key="auth_token",
        httponly=True,
        secure=is_prod,
        samesite="lax"
    )
    return {"message": "Logged out successfully"}
