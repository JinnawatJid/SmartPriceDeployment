# login.py — ใช้ Employee API
from fastapi import APIRouter, HTTPException, Request, Response
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


# === INIT ROUTE (อ่าน UXP token และสร้าง auth_token) ===
@router.post("/init")
async def init_from_uxp(request: Request, response: Response):
    """
    อ่าน UXP token จาก cookie และสร้าง auth_token cookie ของ Smart Pricing
    """
    # ลองหา UXP token จาก cookie
    uxp_token = None
    possible_names = ['token', 'uxp_token', 'access_token', 'jwt']
    
    for name in possible_names:
        token = request.cookies.get(name)
        if token:
            uxp_token = token
            print(f"✅ Found UXP token in cookie: {name}")
            break
    
    if not uxp_token:
        raise HTTPException(status_code=401, detail="ไม่พบ UXP token - กรุณา login ผ่าน UXP Portal")
    
    try:
        # Decode UXP token
        payload = jwt.decode(uxp_token, options={"verify_signature": False})
        print(f"UXP Token Payload: {payload}")
        
        # ดึงรหัสพนักงาน
        emp_code = (
            payload.get("sub") or 
            payload.get("employeeCode") or 
            payload.get("employee_id") or 
            payload.get("id") or 
            payload.get("empCode")
        )
        
        if not emp_code:
            raise HTTPException(status_code=400, detail="ไม่พบรหัสพนักงานใน UXP token")
        
        # ดึงข้อมูลพนักงานจาก API
        emp = await load_employee(str(emp_code))
        if not emp:
            raise HTTPException(status_code=401, detail=f"ไม่พบข้อมูลพนักงาน: {emp_code}")
        
        # สร้าง auth_token ของ Smart Pricing
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
        
        # สร้าง HttpOnly cookie
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
            samesite="lax",
            max_age=JWT_EXPIRE_HOURS * 3600,
            path="/",
        )
        
        return {"token": token, "employee": emp}
        
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"UXP token ไม่ถูกต้อง: {str(e)}")
    except Exception as e:
        print(f"❌ Error in init_from_uxp: {e}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")


# === LOGIN ROUTE ===
@router.post("")
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

    # สร้าง HttpOnly cookie
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
    )

    return {"token": token, "employee": emp}


# === ME ROUTE ===
@router.get("/me")
async def get_current_user(request: Request):
    """
    ดึงข้อมูลผู้ใช้ปัจจุบันจาก cookie auth_token
    """
    token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="ไม่พบ token")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return {
            "employee": {
                "id": payload.get("sub"),
                "name": payload.get("name"),
                "branchId": payload.get("branchId"),
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token หมดอายุ")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token ไม่ถูกต้อง")


# === LOGOUT ROUTE ===
@router.post("/logout")
async def logout(response: Response):
    """
    Logout - ลบ cookie auth_token
    """
    response.delete_cookie(key="auth_token", path="/")
    return {"message": "ออกจากระบบสำเร็จ"}
