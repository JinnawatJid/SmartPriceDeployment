from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from config.db_mssql import get_mssql_conn
import jwt
import os

router = APIRouter(prefix="/api/promotions", tags=["promotions"])

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

DB_PATH = "backend/config/data/Quetung.db"

class PromotionItem(BaseModel):
    sku: str
    promotion_text: str

class PromotionCreate(BaseModel):
    promotion_name: str
    branches: List[str]  # เปลี่ยนเป็น List
    start_date: str
    end_date: str
    items: List[PromotionItem]

class PromotionResponse(BaseModel):
    id: int
    promotion_name: str
    branch: str
    start_date: str
    end_date: str
    status: str
    created_by: str
    created_at: str
    items: List[dict]

@router.post("/", response_model=dict)
async def create_promotion(promotion: PromotionCreate, authorization: str = Header(None)):
    """สร้าง Promotion ใหม่ (Manager เท่านั้น)"""
    current_user = get_current_user_from_token(authorization)
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # แปลง branches array เป็น string (comma-separated)
        branches_str = ','.join(promotion.branches)
        
        # สร้าง PromotionCode อัตโนมัติ (format: PROMO-YYYYMMDD-XXXX)
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        
        # หา running number สำหรับวันนี้
        cursor.execute("""
            SELECT COUNT(*) FROM Promotion_Header 
            WHERE PromotionCode LIKE ?
        """, (f'PROMO-{today}-%',))
        
        count = cursor.fetchone()[0]
        promo_code = f'PROMO-{today}-{str(count + 1).zfill(4)}'
        
        print(f"🎫 [CREATE PROMO] Generated PromotionCode: {promo_code}")
        
        # สร้าง Promotion Header
        cursor.execute("""
            INSERT INTO Promotion_Header 
            (PromotionCode, PromotionName, BranchCode, StartDate, EndDate, Status, CreatedBy, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, 'active', ?, GETDATE(), GETDATE())
        """, (
            promo_code,
            promotion.promotion_name,
            branches_str,
            promotion.start_date,
            promotion.end_date,
            current_user.get('username', 'unknown')
        ))
        
        # ดึง ID ที่เพิ่งสร้าง
        cursor.execute("SELECT @@IDENTITY AS id")
        promotion_id = cursor.fetchone()[0]
        
        print(f"✅ [CREATE PROMO] Created promotion with ID: {promotion_id}")
        
        # สร้าง Promotion Items
        for item in promotion.items:
            cursor.execute("""
                INSERT INTO Promotion_Items (PromotionId, SKU, PromotionText, CreatedAt)
                VALUES (?, ?, ?, GETDATE())
            """, (promotion_id, item.sku, item.promotion_text))
            print(f"  ➕ Added item: {item.sku}")
        
        conn.commit()
        return {"success": True, "promotion_id": int(promotion_id), "promotion_code": promo_code}
    
    except Exception as e:
        print(f"❌ [CREATE PROMO] Error: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@router.get("/", response_model=List[PromotionResponse])
async def get_promotions(status: Optional[str] = None, branch: Optional[str] = None):
    """ดึงรายการ Promotion ทั้งหมด"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM Promotion_Header WHERE 1=1"
        params = []
        
        if status:
            query += " AND Status = ?"
            params.append(status)
        
        if branch:
            query += " AND BranchCode LIKE ?"
            params.append(f"%{branch}%")
        
        query += " ORDER BY CreatedAt DESC"
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        promotions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        result = []
        for promo in promotions:
            cursor.execute("""
                SELECT Id, SKU, PromotionText, CreatedAt 
                FROM Promotion_Items 
                WHERE PromotionId = ?
            """, (promo['Id'],))
            item_columns = [column[0] for column in cursor.description]
            items = [dict(zip(item_columns, row)) for row in cursor.fetchall()]
            
            result.append({
                "id": promo['Id'],
                "promotion_name": promo['PromotionName'],
                "branch": promo['BranchCode'],
                "start_date": str(promo['StartDate']),
                "end_date": str(promo['EndDate']),
                "status": promo['Status'],
                "created_by": promo['CreatedBy'] or '',
                "created_at": str(promo['CreatedAt']),
                "items": items
            })
        
        return result
    
    finally:
        if conn:
            conn.close()

@router.get("/active-by-skus")
async def get_active_promotions_by_skus(skus: str):
    """ดึง Promotion ที่ active ตาม SKU ที่ระบุ (comma-separated)"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        sku_list = [s.strip() for s in skus.split(',')]
        today = datetime.now().date().isoformat()
        
        print(f"🔍 [PROMO API] Searching for SKUs: {sku_list}")
        print(f"📅 [PROMO API] Today: {today}")
        
        placeholders = ','.join('?' * len(sku_list))
        
        query = f"""
            SELECT 
                ph.Id, ph.PromotionName, ph.BranchCode, ph.StartDate, ph.EndDate,
                pi.SKU, pi.PromotionText
            FROM Promotion_Header ph
            JOIN Promotion_Items pi ON ph.Id = pi.PromotionId
            WHERE ph.Status = 'active'
            AND ph.StartDate <= ?
            AND ph.EndDate >= ?
            AND pi.SKU IN ({placeholders})
        """
        
        print(f"📝 [PROMO API] Query: {query}")
        print(f"📝 [PROMO API] Params: {[today, today] + sku_list}")
        
        cursor.execute(query, [today, today] + sku_list)
        
        columns = [column[0] for column in cursor.description]
        promotions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        print(f"📦 [PROMO API] Found {len(promotions)} promotion records")
        print(f"📦 [PROMO API] Raw promotions: {promotions}")
        
        # จัดกลุ่มตาม SKU
        result = {}
        for promo in promotions:
            sku = promo['SKU']
            if sku not in result:
                result[sku] = []
            
            result[sku].append({
                "promotion_id": promo['Id'],
                "promotion_name": promo['PromotionName'],
                "promotion_text": promo['PromotionText'],
                "branch": promo['BranchCode']
            })
        
        print(f"✅ [PROMO API] Result: {result}")
        
        return result
    
    except Exception as e:
        print(f"❌ [PROMO API] Error: {str(e)}")
        raise
    
    finally:
        if conn:
            conn.close()

@router.put("/{promotion_id}/status")
async def update_promotion_status(
    promotion_id: int, 
    status: str,
    authorization: str = Header(None)
):
    """อัพเดทสถานะ Promotion (active/inactive)"""
    current_user = get_current_user_from_token(authorization)
    if status not in ['active', 'inactive']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Promotion_Header 
            SET Status = ?, UpdatedAt = GETDATE()
            WHERE Id = ?
        """, (status, promotion_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Promotion not found")
        
        return {"success": True}
    
    finally:
        if conn:
            conn.close()

@router.delete("/{promotion_id}")
async def delete_promotion(promotion_id: int, authorization: str = Header(None)):
    """ลบ Promotion"""
    current_user = get_current_user_from_token(authorization)
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Promotion_Items WHERE PromotionId = ?", (promotion_id,))
        cursor.execute("DELETE FROM Promotion_Header WHERE Id = ?", (promotion_id,))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Promotion not found")
        
        return {"success": True}
    
    finally:
        if conn:
            conn.close()
