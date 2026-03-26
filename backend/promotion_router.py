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

# ⭐ Helper function to normalize customer type
def normalize_customer_type(gen_bus: str) -> str:
    """
    Normalize customer type. If not in R,W,I,P, treat as R.
    """
    valid_types = {'R', 'W', 'I', 'P'}
    if not gen_bus:
        return None
    
    normalized = gen_bus.strip().upper()
    if normalized not in valid_types:
        return 'R'
    return normalized

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
    branches: List[str]
    start_date: str
    end_date: str
    selection_type: str  # items | filter | customer
    promotion_text: Optional[str] = None
    items: List[PromotionItem]
    filter_criteria: Optional[dict] = None
    customer_codes: Optional[List[str]] = []  # Deprecated: kept for backward compatibility
    gen_bus: Optional[str] = None  # ⭐ New: comma-separated customer types (R,W,I,P)

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
            (PromotionCode, PromotionName, BranchCode, StartDate, EndDate, Status, CreatedBy, CreatedAt, UpdatedAt, gen_bus)
            VALUES (?, ?, ?, ?, ?, 'active', ?, GETDATE(), GETDATE(), ?)
        """, (
            promo_code,
            promotion.promotion_name,
            branches_str,
            promotion.start_date,
            promotion.end_date,
            current_user.get('username', 'unknown'),
            promotion.gen_bus  # ⭐ บันทึก gen_bus (comma-separated customer types)
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
        
        # บันทึกรหัสลูกค้า (ถ้ามี)
        if promotion.customer_codes:
            for customer_code in promotion.customer_codes:
                cursor.execute("""
                    INSERT INTO Promotion_Customers (PromotionId, CustomerCode, PromotionText, CreatedAt)
                    VALUES (?, ?, ?, GETDATE())
                """, (promotion_id, customer_code, promotion.promotion_text or ''))
                print(f"  👤 Added customer: {customer_code}")
        
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

@router.post("/get-skus-by-filter")
async def get_skus_by_filter(filter_criteria: dict):
    """ดึง SKU ตามเงื่อนไข filter ที่เลือก"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # สร้าง WHERE clause ตาม filter
        where_clauses = []
        params = []
        
        # Category (ตัวอักษรแรกของ SKU)
        if filter_criteria.get('categories'):
            category_map = {
                'Glass': 'G',
                'Aluminum': 'A',
                'Sealant': 'S',
                'Gypsum': 'Y',
                'C-Line': 'C',
                'Accessories': 'E'
            }
            category_codes = [category_map.get(cat, cat) for cat in filter_criteria['categories']]
            placeholders = ','.join('?' * len(category_codes))
            where_clauses.append(f"LEFT(SKU, 1) IN ({placeholders})")
            params.extend(category_codes)
        
        # Brand - ใช้ SUBSTRING ตามตำแหน่งใน SKU
        if filter_criteria.get('brands'):
            brand_conditions = []
            for brand in filter_criteria['brands']:
                # Glass (G): position 2-3 (2 digits)
                # Aluminum (A), C-Line (C), Sealant (S), Gypsum (Y): position 2-3 (2 digits)
                # Accessories (E): position 2-4 (3 digits)
                brand_conditions.append(
                    f"(LEFT(SKU, 1) IN ('G', 'A', 'C', 'S', 'Y') AND SUBSTRING(SKU, 2, 2) = ?) OR "
                    f"(LEFT(SKU, 1) = 'E' AND SUBSTRING(SKU, 2, 3) = ?)"
                )
                params.append(brand.zfill(2))
                params.append(brand.zfill(3))
            
            if brand_conditions:
                where_clauses.append(f"({' OR '.join(brand_conditions)})")
        
        # Group/Type - ใช้ SUBSTRING ตามตำแหน่งใน SKU
        if filter_criteria.get('groups'):
            group_conditions = []
            for group in filter_criteria['groups']:
                # Glass (G): position 4-5 (2 digits) - Type
                # Aluminum (A), C-Line (C): position 4-5 (2 digits)
                # Sealant (S), Gypsum (Y): position 4-5 (2 digits)
                # Accessories (E): position 5-6 (2 digits)
                group_conditions.append(
                    f"(LEFT(SKU, 1) IN ('G', 'A', 'C', 'S', 'Y') AND SUBSTRING(SKU, 4, 2) = ?) OR "
                    f"(LEFT(SKU, 1) = 'E' AND SUBSTRING(SKU, 5, 2) = ?)"
                )
                params.append(group.zfill(2))
                params.append(group.zfill(2))
            
            if group_conditions:
                where_clauses.append(f"({' OR '.join(group_conditions)})")
        
        # SubGroup - ใช้ SUBSTRING ตามตำแหน่งใน SKU
        if filter_criteria.get('subGroups'):
            subgroup_conditions = []
            for subgroup in filter_criteria['subGroups']:
                # Glass (G): position 6-8 (3 digits)
                # Aluminum (A), C-Line (C), Sealant (S): position 6-8 (3 digits)
                # Gypsum (Y): position 6-7 (2 digits)
                # Accessories (E): position 7-8 (2 digits)
                subgroup_conditions.append(
                    f"(LEFT(SKU, 1) IN ('G', 'A', 'C', 'S') AND SUBSTRING(SKU, 6, 3) = ?) OR "
                    f"(LEFT(SKU, 1) = 'Y' AND SUBSTRING(SKU, 6, 2) = ?) OR "
                    f"(LEFT(SKU, 1) = 'E' AND SUBSTRING(SKU, 7, 2) = ?)"
                )
                params.append(subgroup.zfill(3))
                params.append(subgroup.zfill(2))
                params.append(subgroup.zfill(2))
            
            if subgroup_conditions:
                where_clauses.append(f"({' OR '.join(subgroup_conditions)})")
        
        # Color - ใช้ SUBSTRING ตามตำแหน่งใน SKU
        if filter_criteria.get('colors'):
            color_conditions = []
            for color in filter_criteria['colors']:
                # Glass (G): position 9-10 (2 digits)
                # Aluminum (A), C-Line (C): position 9-10 (2 digits)
                # Sealant (S): position 9-10 (2 digits)
                # Gypsum (Y): position 8-10 (3 digits)
                # Accessories (E): position 9-10 (2 digits)
                color_conditions.append(
                    f"(LEFT(SKU, 1) IN ('G', 'A', 'C', 'S', 'E') AND SUBSTRING(SKU, 9, 2) = ?) OR "
                    f"(LEFT(SKU, 1) = 'Y' AND SUBSTRING(SKU, 8, 3) = ?)"
                )
                params.append(color.zfill(2))
                params.append(color.zfill(3))
            
            if color_conditions:
                where_clauses.append(f"({' OR '.join(color_conditions)})")
        
        # Thickness - ใช้ SUBSTRING ตามตำแหน่งใน SKU
        if filter_criteria.get('thicknesses'):
            thickness_conditions = []
            for thickness in filter_criteria['thicknesses']:
                # Glass (G): position 11-12 (2 digits)
                # Aluminum (A), C-Line (C): position 11-12 (2 digits)
                # Gypsum (Y): position 11-12 (2 digits)
                thickness_conditions.append(
                    f"LEFT(SKU, 1) IN ('G', 'A', 'C', 'Y') AND SUBSTRING(SKU, 11, 2) = ?"
                )
                params.append(thickness.zfill(2))
            
            if thickness_conditions:
                where_clauses.append(f"({' OR '.join(thickness_conditions)})")
        
        if not where_clauses:
            return {"skus": []}
        
        query = f"""
            SELECT SKU, Description 
            FROM Item_Master 
            WHERE {' AND '.join(where_clauses)}
            ORDER BY SKU
        """
        
        print(f"🔍 [GET SKUs] Query: {query}")
        print(f"🔍 [GET SKUs] Params: {params}")
        
        cursor.execute(query, params)
        skus = [{"sku": row[0], "description": row[1]} for row in cursor.fetchall()]
        
        print(f"✅ [GET SKUs] Found {len(skus)} SKUs")
        
        return {"skus": skus}
    
    except Exception as e:
        print(f"❌ [GET SKUs] Error: {str(e)}")
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
            # ดึง Promotion Items
            cursor.execute("""
                SELECT Id, SKU, PromotionText, CreatedAt 
                FROM Promotion_Items 
                WHERE PromotionId = ?
            """, (promo['Id'],))
            item_columns = [column[0] for column in cursor.description]
            items = [dict(zip(item_columns, row)) for row in cursor.fetchall()]
            
            # ดึง Promotion Customers
            cursor.execute("""
                SELECT Id, CustomerCode, PromotionText, CreatedAt 
                FROM Promotion_Customers 
                WHERE PromotionId = ?
            """, (promo['Id'],))
            customer_columns = [column[0] for column in cursor.description]
            customers = [dict(zip(customer_columns, row)) for row in cursor.fetchall()]
            
            result.append({
                "id": promo['Id'],
                "promotion_name": promo['PromotionName'],
                "branch": promo['BranchCode'],
                "start_date": str(promo['StartDate']),
                "end_date": str(promo['EndDate']),
                "status": promo['Status'],
                "created_by": promo['CreatedBy'] or '',
                "created_at": str(promo['CreatedAt']),
                "items": items,
                "customers": customers
            })
        
        return result
    
    finally:
        if conn:
            conn.close()

@router.get("/active-by-customer")
async def get_active_promotions_by_customer(customerCode: str):
    """ดึง Promotion ที่ active สำหรับลูกค้า (ตรวจสอบทั้ง gen_bus และ customer_codes)"""
    conn = None
    
    try:
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        print(f"👤 [CUSTOMER PROMO API] ========================================")
        print(f"👤 [CUSTOMER PROMO API] Searching for customer: '{customerCode}'")
        print(f"📅 [CUSTOMER PROMO API] Today: {today}")
        
        # ⭐ Step 1: ดึง gen_bus ของลูกค้าจากตาราง Customer
        cursor.execute("""
            SELECT gen_bus FROM Customer WHERE customer_code = ?
        """, (customerCode,))
        
        customer_row = cursor.fetchone()
        customer_gen_bus = customer_row[0] if customer_row and customer_row[0] else None
        
        print(f"👤 [CUSTOMER PROMO API] Customer gen_bus from DB: '{customer_gen_bus}'")
        
        # ⭐ Normalize customer_gen_bus: ถ้าไม่ใช่ R,W,I,P ให้ถือว่าเป็น R
        customer_gen_bus = normalize_customer_type(customer_gen_bus)
        
        print(f"👤 [CUSTOMER PROMO API] Normalized customer gen_bus: '{customer_gen_bus}'")
        
        # ⭐ Step 2: ค้นหา Promotion ที่ตรงกับ gen_bus ของลูกค้า
        promotions = []
        
        if customer_gen_bus:
            # ค้นหา Promotion ที่มี gen_bus ตรงกับลูกค้า
            query = """
                SELECT 
                    Id, PromotionName, BranchCode, StartDate, EndDate, gen_bus
                FROM Promotion_Header
                WHERE Status = 'active'
                AND StartDate <= ?
                AND EndDate >= ?
                AND gen_bus IS NOT NULL
                AND gen_bus != ''
            """
            
            print(f"📝 [CUSTOMER PROMO API] Query: {query}")
            print(f"📝 [CUSTOMER PROMO API] Params: [{today}, {today}]")
            
            cursor.execute(query, [today, today])
            
            columns = [column[0] for column in cursor.description]
            all_promotions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            print(f"📦 [CUSTOMER PROMO API] Found {len(all_promotions)} active promotions with gen_bus")
            
            # กรองเฉพาะ Promotion ที่มี customer_gen_bus ใน gen_bus field
            for promo in all_promotions:
                promo_gen_bus = promo.get('gen_bus', '') or ''
                promo_types = [normalize_customer_type(t) for t in promo_gen_bus.split(',') if t.strip()]
                promo_types = [t for t in promo_types if t]  # Remove None values
                
                print(f"  🔍 Promo '{promo['PromotionName']}' has types: {promo_types}")
                
                if customer_gen_bus in promo_types:
                    print(f"  ✅ Match! Customer type '{customer_gen_bus}' found in promotion")
                    promotions.append(promo)
                else:
                    print(f"  ❌ No match. Customer type '{customer_gen_bus}' not in {promo_types}")
        
        # ⭐ Step 3: ค้นหา Promotion แบบเก่าที่ระบุ customer_code โดยตรง (backward compatibility)
        query_old = """
            SELECT 
                ph.Id, ph.PromotionName, ph.BranchCode, ph.StartDate, ph.EndDate,
                pc.PromotionText
            FROM Promotion_Header ph
            JOIN Promotion_Customers pc ON ph.Id = pc.PromotionId
            WHERE ph.Status = 'active'
            AND ph.StartDate <= ?
            AND ph.EndDate >= ?
            AND pc.CustomerCode = ?
        """
        
        print(f"📝 [CUSTOMER PROMO API] Old query: {query_old}")
        print(f"📝 [CUSTOMER PROMO API] Params: [{today}, {today}, '{customerCode}']")
        
        cursor.execute(query_old, [today, today, customerCode])
        
        columns = [column[0] for column in cursor.description]
        old_promotions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        print(f"📦 [CUSTOMER PROMO API] Found {len(old_promotions)} customer-specific promotions")
        
        # รวม promotions ทั้งสองแบบ
        result = []
        
        # เพิ่ม gen_bus based promotions
        for promo in promotions:
            result.append({
                "promotion_id": promo['Id'],
                "promotion_name": promo['PromotionName'],
                "promotion_text": f"โปรโมชั่นสำหรับลูกค้าประเภท {customer_gen_bus}",
                "branch": promo['BranchCode'],
                "start_date": str(promo['StartDate']),
                "end_date": str(promo['EndDate'])
            })
        
        # เพิ่ม customer-specific promotions
        for promo in old_promotions:
            result.append({
                "promotion_id": promo['Id'],
                "promotion_name": promo['PromotionName'],
                "promotion_text": promo['PromotionText'],
                "branch": promo['BranchCode'],
                "start_date": str(promo['StartDate']),
                "end_date": str(promo['EndDate'])
            })
        
        print(f"✅ [CUSTOMER PROMO API] Returning {len(result)} promotions total")
        print(f"✅ [CUSTOMER PROMO API] Result: {result}")
        print(f"👤 [CUSTOMER PROMO API] ========================================")
        
        return result
    
    except Exception as e:
        print(f"❌ [CUSTOMER PROMO API] Error: {str(e)}")
        import traceback
        print(f"❌ [CUSTOMER PROMO API] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    
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
