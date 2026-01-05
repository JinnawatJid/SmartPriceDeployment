# login.py — เวอร์ชัน SQLite 100%
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import jwt, os, pandas as pd

from employees import load_employees_sqlite   # ← ใช้ SQLite แทน Excel

router = APIRouter(prefix="/login", tags=["auth"])

# === CONFIG ===
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-this")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = 12


# === SCHEMA ===
class LoginRequest(BaseModel):
    employeeCode: str


# === HELPER ===
def load_employee(code: str):
    df = load_employees_sqlite()  # ← SQLite dataframe จาก employees.py

    row = df[df["empCode"].astype(str).str.lower() == code.lower()]
    if row.empty:
        return None

    r = row.iloc[0]
    return {
        "id": str(r["empCode"]).strip(),
        "name": str(r["empName"]).strip(),
        "branchId": str(r["branchCode"]).strip() if pd.notna(r["branchCode"]) else None,
    }


# === LOGIN ROUTE ===
@router.post("")
def login(req: LoginRequest):
    emp = load_employee(req.employeeCode)
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
