# employees.py — ใช้ SQLite 100%
from pathlib import Path
from typing import Any, Dict, Optional, List
import math
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from db_sqlite import get_conn   # ← ใช้ SQLite

router = APIRouter(prefix="/employees", tags=["employees"])


# ============================
#  Schema ของ Employees (SQLite)
# ============================
# No.
# First Name
# Last Name
# Job Title
# Company Phone No.
# Branch Code
# Department Code
# Search Name
# Comment
# Petty Cash
# Advance
# ============================


def load_employees_sqlite() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM "Employees"', conn)
    conn.close()

    # --- CLEAN BLOCK (แก้เฉพาะส่วนนี้) ---
    # ป้องกันไม่ให้ NaN / None กลายเป็น "None" หรือ "nan"
    for col in df.columns:
        df[col] = (
            df[col]
            .replace(["nan", "None"], pd.NA)   # ลบค่า nan/None (string) ให้กลับเป็น NaN
            .fillna("")                         # แปลง NaN -> ""
            .astype(str)
            .str.strip()
        )
    # ----------------------------------------

    # empCode = No.
    df["empCode"] = df["No."]

    # --- EMPNAME BLOCK (แก้เฉพาะส่วนนี้) ---
    # ใช้เฉพาะ First Name 100% และล้าง None/nan ให้หมด
    df["empName"] = (
        df["First Name"]
        .replace(["nan", "None"], "")   # ลบ "nan"/"None" ถ้าหลงเหลือ
        .fillna("")
        .astype(str)
        .str.strip()
    )
    # -----------------------------------------

    df["branchCode"] = df["Branch Code"]

    # keep only 3 fields (same as old API)
    df = df[["empCode", "empName", "branchCode"]]

    df = df[df["empCode"] != ""].reset_index(drop=True)
    return df


class EmployeeOut(BaseModel):
    id: str
    name: str
    branchId: Optional[str] = None


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class EmployeesResponse(BaseModel):
    meta: PageMeta
    data: List[EmployeeOut]


# =============================
#  GET /employees
# =============================
@router.get("", response_model=EmployeesResponse)
def list_employees(
    q: Optional[str] = Query(None, description="ค้นหาจากรหัสหรือชื่อพนักงาน"),
    branch: Optional[str] = Query(None, description="กรองตามรหัสสาขา"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    df = load_employees_sqlite()

    # search
    if q:
        key = q.strip().lower()
        df = df[
            df["empCode"].str.lower().str.contains(key) |
            df["empName"].str.lower().str.contains(key)
        ]

    # branch filter
    if branch:
        df = df[df["branchCode"].astype(str).str.lower() == branch.lower()]

    total = len(df)
    pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size
    df_page = df.iloc[start:end].copy()

    data = [
        {"id": r["empCode"], "name": r["empName"], "branchId": r["branchCode"] or None}
        for _, r in df_page.iterrows()
    ]

    return EmployeesResponse(
        meta=PageMeta(page=page, page_size=page_size, total=total, pages=pages),
        data=data,
    )


# =============================
#  GET /employees/{code}
# =============================
@router.get("/{code}", response_model=EmployeeOut)
def get_employee(code: str):
    df = load_employees_sqlite()
    row = df[df["empCode"].str.lower() == code.lower()]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"ไม่พบพนักงานรหัส {code}")

    r = row.iloc[0].to_dict()

    return {
        "id": r["empCode"],
        "name": r["empName"],
        "branchId": r["branchCode"] or None
    }
