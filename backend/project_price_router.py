from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from config.db_mssql import get_mssql_conn
import jwt
import os

router = APIRouter(prefix="/api/project-prices", tags=["project-prices"])

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-this")
JWT_ALG = "HS256"

def get_current_user_from_token(authorization: str = Header(None)) -> dict:
    """Extract user info from JWT token"""
    if not authorization:
        return {"username": "anonymous", "id": None}
    
    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return {
            "username": payload.get("username", "unknown"),
            "id": payload.get("id"),
            "branchId": payload.get("branchId")
        }
    except:
        return {"username": "anonymous", "id": None}

class ProjectPriceLine(BaseModel):
    sku: str
    product_name: Optional[str] = None
    unit: Optional[str] = None
    price: float
    quantity: Optional[float] = None

class ProjectPriceCreate(BaseModel):
    project_code: str
    project_name: Optional[str] = None
    customer_code: Optional[str] = None
    customer_name: Optional[str] = None
    branch_code: Optional[str] = None
    price_start_date: str
    price_end_date: str
    request_by: Optional[str] = None
    request_date: Optional[str] = None
    remark: Optional[str] = None
    items: List[ProjectPriceLine]

@router.post("/")
async def create_project_price(project: ProjectPriceCreate, authorization: str = Header(None)):
    """สร้างราคาโครงการใหม่ (Manager เท่านั้น)"""
    current_user = get_current_user_from_token(authorization)
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        print(f"🏗️ [CREATE PROJECT PRICE] Project Code: {project.project_code}")
        
        # สร้าง Project Price Header
        cursor.execute("""
            INSERT INTO Project_Price_Header 
            (project_code, project_name, customer_code, customer_name, branch_code,
             price_start_date, price_end_date, request_by, request_date, status, remark, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, GETDATE(), GETDATE())
        """, (
            project.project_code,
            project.project_name,
            project.customer_code,
            project.customer_name,
            project.branch_code,
            project.price_start_date,
            project.price_end_date,
            project.request_by,
            project.request_date or datetime.now().strftime('%Y-%m-%d'),
            project.remark
        ))
        
        # ดึง ID ที่เพิ่งสร้าง
        cursor.execute("SELECT @@IDENTITY AS id")
        project_id = cursor.fetchone()[0]
        
        print(f"✅ [CREATE PROJECT PRICE] Created project with ID: {project_id}")
        
        # สร้าง Project Price Lines
        for item in project.items:
            cursor.execute("""
                INSERT INTO Project_Price_Line 
                (project_id, sku, product_name, unit, price, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                item.sku,
                item.product_name,
                item.unit,
                item.price,
                item.quantity
            ))
            print(f"  ➕ Added item: {item.sku} - {item.price} {item.unit}")
        
        conn.commit()
        return {"success": True, "project_id": int(project_id)}
    
    except Exception as e:
        print(f"❌ [CREATE PROJECT PRICE] Error: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/")
async def get_project_prices(status: Optional[str] = None, branch: Optional[str] = None):
    """ดึงรายการราคาโครงการทั้งหมด"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM Project_Price_Header WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if branch:
            query += " AND branch_code = ?"
            params.append(branch)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        projects = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        result = []
        for proj in projects:
            # ดึง Project Price Lines
            cursor.execute("""
                SELECT * FROM Project_Price_Line 
                WHERE project_id = ?
            """, (proj['project_id'],))
            line_columns = [column[0] for column in cursor.description]
            lines = [dict(zip(line_columns, row)) for row in cursor.fetchall()]
            
            result.append({
                "project_id": proj['project_id'],
                "project_code": proj['project_code'],
                "project_name": proj['project_name'],
                "customer_code": proj['customer_code'],
                "customer_name": proj['customer_name'],
                "branch_code": proj['branch_code'],
                "price_start_date": str(proj['price_start_date']),
                "price_end_date": str(proj['price_end_date']),
                "request_by": proj['request_by'],
                "request_date": str(proj['request_date']) if proj['request_date'] else None,
                "status": proj['status'],
                "remark": proj['remark'],
                "created_at": str(proj['created_at']),
                "items": lines
            })
        
        return result
    
    finally:
        if conn:
            conn.close()

@router.get("/active-by-customer-sku")
async def get_active_project_price(customerCode: str, sku: str):
    """ดึงราคาโครงการที่ active สำหรับลูกค้าและ SKU"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        print(f"🏗️ [PROJECT PRICE API] Customer: {customerCode}, SKU: {sku}")
        
        query = """
            SELECT 
                ph.project_id, ph.project_code, ph.project_name,
                pl.sku, pl.product_name, pl.unit, pl.price, pl.quantity
            FROM Project_Price_Header ph
            JOIN Project_Price_Line pl ON ph.project_id = pl.project_id
            WHERE ph.status = 'active'
            AND ph.price_start_date <= ?
            AND ph.price_end_date >= ?
            AND ph.customer_code = ?
            AND pl.sku = ?
        """
        
        cursor.execute(query, [today, today, customerCode, sku])
        
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        print(f"📦 [PROJECT PRICE API] Found {len(results)} project prices")
        
        return results
    
    except Exception as e:
        print(f"❌ [PROJECT PRICE API] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()

@router.get("/by-customer")
async def get_projects_by_customer(customerCode: str):
    """ดึงรายการโครงการทั้งหมดของลูกค้า (active เท่านั้น)"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        print(f"🏗️ [PROJECT LIST API] Customer: {customerCode}")
        
        query = """
            SELECT 
                project_id, project_code, project_name,
                price_start_date, price_end_date
            FROM Project_Price_Header
            WHERE status = 'active'
            AND price_start_date <= ?
            AND price_end_date >= ?
            AND customer_code = ?
            ORDER BY project_name
        """
        
        cursor.execute(query, [today, today, customerCode])
        
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # แปลง date เป็น string
        for r in results:
            if r.get('price_start_date'):
                r['price_start_date'] = str(r['price_start_date'])
            if r.get('price_end_date'):
                r['price_end_date'] = str(r['price_end_date'])
        
        print(f"📦 [PROJECT LIST API] Found {len(results)} projects")
        
        return results
    
    except Exception as e:
        print(f"❌ [PROJECT LIST API] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()

@router.get("/project-prices/{project_id}")
async def get_project_prices_by_id(project_id: int):
    """ดึงราคาสินค้าทั้งหมดในโครงการ"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        print(f"🏗️ [PROJECT PRICES API] Project ID: {project_id}")
        
        query = """
            SELECT 
                sku, product_name, unit, price, quantity
            FROM Project_Price_Line
            WHERE project_id = ?
        """
        
        cursor.execute(query, [project_id])
        
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        print(f"📦 [PROJECT PRICES API] Found {len(results)} items")
        
        return results
    
    except Exception as e:
        print(f"❌ [PROJECT PRICES API] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()

@router.put("/{project_id}/status")
async def update_project_status(
    project_id: int, 
    status: str,
    authorization: str = Header(None)
):
    """อัพเดทสถานะราคาโครงการ (active/expired/cancel)"""
    current_user = get_current_user_from_token(authorization)
    if status not in ['active', 'expired', 'cancel']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Project_Price_Header 
            SET status = ?, updated_at = GETDATE()
            WHERE project_id = ?
        """, (status, project_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"success": True}
    
    finally:
        if conn:
            conn.close()

@router.delete("/{project_id}")
async def delete_project_price(project_id: int, authorization: str = Header(None)):
    """ลบราคาโครงการ"""
    current_user = get_current_user_from_token(authorization)
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Project_Price_Line WHERE project_id = ?", (project_id,))
        cursor.execute("DELETE FROM Project_Price_Header WHERE project_id = ?", (project_id,))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"success": True}
    
    finally:
        if conn:
            conn.close()
