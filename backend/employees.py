# employees.py — ดึงข้อมูลจาก API แทน SQLite
from typing import Any, Dict, Optional, List
import math
import httpx
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from config.config_external_api import EMP_API_URL, EMP_API_HEADERS

router = APIRouter(prefix="/employees", tags=["employees"])


# ============================
#  Schema ของ Employees (API)
# ============================
# EmpCode
# EmpName
# EmpPost
# EmpBrchCode
# ============================


async def fetch_employees_from_api(
    q: Optional[str] = None,
    branch: Optional[str] = None,
) -> List[Dict]:
    """
    ดึงข้อมูล Employee จาก External API
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
            
            # กรองข้อมูลตาม query และ branch
            filtered = []
            for emp in employees:
                emp_code = str(emp.get("EmpCode", "")).strip()
                emp_name = str(emp.get("EmpName", "")).strip()
                emp_branch = str(emp.get("EmpBrchCode", "")).strip()
                
                # ข้าม record ที่ไม่มี EmpCode
                if not emp_code:
                    continue
                
                # กรองตาม branch
                if branch and emp_branch.lower() != branch.lower():
                    continue
                
                # กรองตาม search query
                if q:
                    key = q.strip().lower()
                    if key not in emp_code.lower() and key not in emp_name.lower():
                        continue
                
                filtered.append({
                    "empCode": emp_code,
                    "empName": emp_name,
                    "empPost": str(emp.get("EmpPost", "")).strip(),
                    "branchCode": emp_branch,
                })
            
            return filtered
            
    except httpx.HTTPError as e:
        print(f"❌ Error fetching employees from API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ไม่สามารถดึงข้อมูลพนักงานจาก API ได้: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"เกิดข้อผิดพลาด: {str(e)}"
        )


class EmployeeOut(BaseModel):
    id: str
    name: str
    post: Optional[str] = None
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
async def list_employees(
    q: Optional[str] = Query(None, description="ค้นหาจากรหัสหรือชื่อพนักงาน"),
    branch: Optional[str] = Query(None, description="กรองตามรหัสสาขา"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    """
    ดึงรายการพนักงานจาก External API
    """
    # ดึงข้อมูลจาก API
    employees = await fetch_employees_from_api(q=q, branch=branch)
    
    # Pagination
    total = len(employees)
    pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size
    page_data = employees[start:end]
    
    data = [
        {
            "id": emp["empCode"],
            "name": emp["empName"],
            "post": emp["empPost"] or None,
            "branchId": emp["branchCode"] or None,
        }
        for emp in page_data
    ]
    
    return EmployeesResponse(
        meta=PageMeta(page=page, page_size=page_size, total=total, pages=pages),
        data=data,
    )


# =============================
#  GET /employees/{code}
# =============================
@router.get("/{code}", response_model=EmployeeOut)
async def get_employee(code: str):
    """
    ดึงข้อมูลพนักงานตามรหัส
    """
    # ดึงข้อมูลทั้งหมดจาก API
    employees = await fetch_employees_from_api()
    
    # หาพนักงานที่ตรงกับ code
    for emp in employees:
        if emp["empCode"].lower() == code.lower():
            return {
                "id": emp["empCode"],
                "name": emp["empName"],
                "post": emp["empPost"] or None,
                "branchId": emp["branchCode"] or None,
            }
    
    raise HTTPException(
        status_code=404,
        detail=f"ไม่พบพนักงานรหัส {code}"
    )
