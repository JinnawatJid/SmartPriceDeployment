"""Special Price Request Router"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from auth_dependency import get_employee_info
from employee_position_mapper import find_zm_at_branch, find_rm_in_region, find_sdm
from branch_region_mapping import get_region_from_branch
from config.db_mssql import get_mssql_conn
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/special-price-requests", tags=["special-price-requests"])


# === SCHEMAS ===
class SpecialPriceItem(BaseModel):
    sku: str
    item_name: str
    quantity: float
    unit: str
    normal_price: float
    requested_price: float
    approval_level: str


class SpecialPriceRequestCreate(BaseModel):
    quote_no: str
    customer_code: str
    customer_name: str
    customer_type: Optional[str] = None
    items: List[SpecialPriceItem]
    request_reason: str
    valid_from: str
    valid_to: str


# === ENDPOINTS ===
@router.get("/quote/{quote_no:path}")
async def get_special_price_request_by_quote(quote_no: str):
    """Get special price request by quote number"""
    try:
        logger.info(f"Getting special price request for quote: {quote_no}")
        
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # Query special price request by quote_no
        cursor.execute("""
            SELECT * FROM special_price_requests
            WHERE quote_no = ?
            ORDER BY created_at DESC
        """, (quote_no,))
        
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            conn.close()
            # Return null instead of 404 - this is an expected case when no SPR exists yet
            return None
        
        columns = [column[0] for column in cursor.description]
        request_dict = dict(zip(columns, row))
        
        # Query items for this request
        cursor.execute("""
            SELECT * FROM special_price_request_items
            WHERE request_id = ?
            ORDER BY id
        """, (request_dict.get("id"),))
        
        item_rows = cursor.fetchall()
        item_columns = [column[0] for column in cursor.description]
        
        items = []
        for item_row in item_rows:
            item_dict = dict(zip(item_columns, item_row))
            items.append({
                "sku": item_dict.get("sku"),
                "item_name": item_dict.get("item_name"),
                "quantity": item_dict.get("quantity"),
                "unit": item_dict.get("unit"),
                "normal_price": item_dict.get("normal_price"),
                "requested_price": item_dict.get("requested_price"),
                "approval_level": item_dict.get("approval_level"),
            })
        
        result = {
            "id": request_dict.get("id"),
            "quote_no": request_dict.get("quote_no"),
            "status": request_dict.get("status"),
            "request_reason": request_dict.get("request_reason"),
            "original_total": request_dict.get("original_total"),
            "requested_total": request_dict.get("requested_total"),
            "discount_percentage": request_dict.get("discount_percentage"),
            "valid_from": str(request_dict.get("valid_from")) if request_dict.get("valid_from") else None,
            "valid_to": str(request_dict.get("valid_to")) if request_dict.get("valid_to") else None,
            "requester_name": request_dict.get("requester_name"),
            "customer_name": request_dict.get("customer_name"),
            "created_at": str(request_dict.get("created_at")) if request_dict.get("created_at") else None,
            "approved_at": str(request_dict.get("approved_at")) if request_dict.get("approved_at") else None,
            "items": items,
        }
        
        cursor.close()
        conn.close()
        
        logger.info(f"  Found SPR #{request_dict.get('id')} with status: {request_dict.get('status')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting special price request by quote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get special price request: {str(e)}"
        )


@router.get("/pending/approvals")
async def get_pending_approvals(employee_info: dict = Depends(get_employee_info)):
    """Get pending approvals for current user"""
    try:
        current_employee_id = employee_info.get('employee_id')
        current_role = employee_info.get('role', 'Sales')
        current_branch = employee_info.get('branch_code')
        
        logger.info(f"Getting pending approvals for:")
        logger.info(f"  Employee ID: {current_employee_id}")
        logger.info(f"  Role: {current_role}")
        logger.info(f"  Branch: {current_branch}")
        
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        pending_requests = []
        
        # Query based on role
        if current_role == 'ZM':
            # ZM ดูคำขอที่ status = PENDING_ZM และ approver_employee_id = ZM_{branch}
            # เช่น ZM ที่สาขา 03TS จะเห็นคำขอที่ approver_employee_id = "ZM_03TS"
            position_id = f"ZM_{current_branch}"
            logger.info(f"  Looking for requests with approver_employee_id = {position_id} and status = PENDING_ZM")
            
            cursor.execute("""
                SELECT * FROM special_price_requests
                WHERE status = 'PENDING_ZM'
                AND approver_employee_id = ?
                ORDER BY created_at DESC
            """, (position_id,))
            
        elif current_role == 'RM':
            # RM ดูคำขอที่ status = PENDING_RM
            # ต้องเช็คว่า RM คนนี้รับผิดชอบภูมิภาคไหน
            region = employee_info.get('region')
            position_id = f"RM_{region}"
            logger.info(f"  Looking for requests with approver_employee_id = {position_id} and status = PENDING_RM")
            
            cursor.execute("""
                SELECT * FROM special_price_requests
                WHERE status = 'PENDING_RM'
                AND approver_employee_id = ?
                ORDER BY created_at DESC
            """, (position_id,))
            
        elif current_role == 'SDM':
            # SDM ดูคำขอที่ status = PENDING_SDM
            logger.info(f"  Looking for requests with status = PENDING_SDM")
            
            cursor.execute("""
                SELECT * FROM special_price_requests
                WHERE status = 'PENDING_SDM'
                ORDER BY created_at DESC
            """)
            
        else:
            # Sales หรือ role อื่น ๆ ไม่มีสิทธิ์อนุมัติ
            logger.info(f"  Role {current_role} cannot approve requests")
            return []
        
        rows = cursor.fetchall()
        logger.info(f"  Found {len(rows)} pending requests")
        
        # Get column names from cursor description
        columns = [column[0] for column in cursor.description]
        
        for row in rows:
            # Convert row to dict using column names
            row_dict = dict(zip(columns, row))
            
            # Query items for this request
            cursor.execute("""
                SELECT * FROM special_price_request_items
                WHERE request_id = ?
                ORDER BY id
            """, (row_dict.get("id"),))
            
            item_rows = cursor.fetchall()
            item_columns = [column[0] for column in cursor.description]
            
            items = []
            for item_row in item_rows:
                item_dict = dict(zip(item_columns, item_row))
                items.append({
                    "sku": item_dict.get("sku"),
                    "item_name": item_dict.get("item_name"),
                    "quantity": item_dict.get("quantity"),
                    "unit": item_dict.get("unit"),
                    "normal_price": item_dict.get("normal_price"),
                    "requested_price": item_dict.get("requested_price"),
                    "approval_level": item_dict.get("approval_level"),
                    "category": item_dict.get("category"),
                    "is_sold_by_pack": item_dict.get("is_sold_by_pack"),
                    "sqft_sheet": item_dict.get("sqft_sheet"),
                    "product_weight": item_dict.get("product_weight"),
                })
            
            request_data = {
                "id": row_dict.get("id"),
                "quote_no": row_dict.get("quote_no"),
                "request_reason": row_dict.get("request_reason"),
                "original_total": row_dict.get("original_total"),
                "requested_total": row_dict.get("requested_total"),
                "discount_percentage": row_dict.get("discount_percentage"),
                "status": row_dict.get("status"),
                "approver_employee_id": row_dict.get("approver_employee_id"),
                "approved_by": row_dict.get("approved_by"),
                "created_at": str(row_dict.get("created_at")) if row_dict.get("created_at") else None,
                "updated_at": str(row_dict.get("updated_at")) if row_dict.get("updated_at") else None,
                
                # เพิ่มข้อมูลผู้ขอและลูกค้า
                "requester_name": row_dict.get("requester_name"),
                "requester_employee_id": row_dict.get("requester_employee_id"),
                "customer_name": row_dict.get("customer_name"),
                "customer_code": row_dict.get("customer_code"),
                "request_number": row_dict.get("quote_no"),  # ใช้ quote_no เป็น request_number
                
                # เพิ่มวันที่ใช้ราคา
                "valid_from": str(row_dict.get("valid_from")) if row_dict.get("valid_from") else None,
                "valid_to": str(row_dict.get("valid_to")) if row_dict.get("valid_to") else None,
                
                # เพิ่ม items
                "items": items,
            }
            
            logger.info(f"  Request #{row_dict.get('id')}: {row_dict.get('quote_no')} - {row_dict.get('status')} ({len(items)} items)")
            pending_requests.append(request_data)
        
        cursor.close()
        conn.close()
        return pending_requests
        
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pending approvals: {str(e)}"
        )


@router.post("")
async def create_special_price_request(
    request_data: SpecialPriceRequestCreate,
    employee_info: dict = Depends(get_employee_info)
):
    """Create a new special price request"""
    try:
        # 1. ดึงข้อมูลผู้ขอจาก token
        requester_id = employee_info.get('employee_id')
        requester_name = employee_info.get('name', 'Unknown')
        branch_code = employee_info.get('branch_code')
        role = employee_info.get('role', 'Sales')
        
        if not branch_code:
            raise HTTPException(status_code=400, detail="Branch code not found in token")
        
        # 2. คำนวณ region จาก branch
        region = get_region_from_branch(branch_code)
        
        logger.info(f"Creating special price request:")
        logger.info(f"  Requester: {requester_id} ({requester_name})")
        logger.info(f"  Branch: {branch_code}, Region: {region}")
        logger.info(f"  Quote No: {request_data.quote_no}")
        logger.info(f"  Customer: {request_data.customer_code} - {request_data.customer_name}")
        logger.info(f"  Items: {len(request_data.items)}")
        
        # 3. หาผู้อนุมัติโดยใช้ employee_position_mapper
        logger.info("Finding approvers...")
        
        zm = await find_zm_at_branch(branch_code)
        logger.info(f"  ZM: {zm}")
        
        rm = await find_rm_in_region(region)
        logger.info(f"  RM: {rm}")
        
        sdm = await find_sdm()
        logger.info(f"  SDM: {sdm}")
        
        # 4. สร้าง request object (ยังไม่บันทึกลงฐานข้อมูล - ต้องสร้างตารางก่อน)
        special_price_request = {
            "quote_no": request_data.quote_no,
            "requester_id": requester_id,
            "requester_name": requester_name,
            "requester_role": role,
            "branch": branch_code,
            "region": region,
            
            # ข้อมูลลูกค้า
            "customer_code": request_data.customer_code,
            "customer_name": request_data.customer_name,
            "customer_type": request_data.customer_type,
            
            # ข้อมูลสินค้า
            "items": [item.dict() for item in request_data.items],
            "total_items": len(request_data.items),
            
            # เหตุผลและวันที่
            "request_reason": request_data.request_reason,
            "valid_from": request_data.valid_from,
            "valid_to": request_data.valid_to,
            
            # ผู้อนุมัติ (เก็บ employee_id จริง)
            "zm_approver_id": zm['employee_id'] if zm else None,
            "zm_approver_name": zm['name'] if zm else None,
            "zm_approver_branch": zm['branch'] if zm else None,
            
            "rm_approver_id": rm['employee_id'] if rm else None,
            "rm_approver_name": rm['name'] if rm else None,
            "rm_approver_region": rm.get('region') if rm else None,
            
            "sdm_approver_id": sdm['employee_id'] if sdm else None,
            "sdm_approver_name": sdm['name'] if sdm else None,
            
            # สถานะ
            "status": "pending_zm",  # เริ่มที่ ZM
            "created_at": datetime.now().isoformat(),
        }
        
        logger.info("Saving special price request to database...")
        
        # บันทึกลงฐานข้อมูล
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # คำนวณยอดรวม
        original_total = sum(float(item.normal_price) * float(item.quantity) for item in request_data.items)
        requested_total = sum(float(item.requested_price) * float(item.quantity) for item in request_data.items)
        discount_percentage = ((original_total - requested_total) / original_total * 100) if original_total > 0 else 0
        
        # กำหนด status และ approver_employee_id เริ่มต้น
        # เริ่มที่ ZM เสมอ (ไม่ว่าจะต้องผ่านใครบ้าง)
        initial_status = 'PENDING_ZM'
        approver_id = f"ZM_{branch_code}"
        
        # Insert special_price_requests (ใช้เฉพาะคอลัมน์ที่มีในตาราง)
        cursor.execute("""
            INSERT INTO special_price_requests (
                request_number, quote_no, customer_code, customer_name, customer_type,
                requester_name, request_reason, original_total, requested_total, discount_percentage,
                status, approver_employee_id, branch, valid_from, valid_to,
                employee_id, created_at, updated_at
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """, (
            request_data.quote_no,  # request_number
            request_data.quote_no,  # quote_no
            request_data.customer_code,
            request_data.customer_name,
            request_data.customer_type,
            requester_name,
            request_data.request_reason,
            original_total,
            requested_total,
            discount_percentage,
            initial_status,
            approver_id,
            branch_code,
            request_data.valid_from,
            request_data.valid_to,
            requester_id
        ))
        
        request_id = cursor.fetchone()[0]
        logger.info(f"  Created request ID: {request_id}")
        
        # Insert items (ใช้เฉพาะคอลัมน์ที่มีในตาราง)
        for item in request_data.items:
            # คำนวณ original_amount และ requested_amount
            original_amount = float(item.normal_price) * float(item.quantity)
            requested_amount = float(item.requested_price) * float(item.quantity)
            is_below_normal = 1 if item.requested_price < item.normal_price else 0
            
            cursor.execute("""
                INSERT INTO special_price_request_items (
                    request_id, item_code, item_name, quantity, unit,
                    normal_price, requested_price, original_amount, requested_amount,
                    is_below_normal, approval_level, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                request_id,
                item.sku,  # item_code
                item.item_name,
                item.quantity,
                item.unit,
                item.normal_price,
                item.requested_price,
                original_amount,
                requested_amount,
                is_below_normal,
                item.approval_level
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Special price request saved to database successfully")
        logger.info(f"   Request ID: {request_id}")
        logger.info(f"   Status: {initial_status}")
        logger.info(f"   Approver: {approver_id}")
        
        return {
            "success": True,
            "message": "Special price request created successfully",
            "request_id": request_id,
            "quote_no": request_data.quote_no,
            "status": initial_status,
            "approver_employee_id": approver_id
        }
        
    except Exception as e:
        logger.error(f"Error creating special price request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create special price request: {str(e)}"
        )


@router.post("/{request_id}/approve")
async def approve_request(request_id: int, employee_info: dict = Depends(get_employee_info)):
    """Approve a special price request"""
    try:
        current_employee_id = employee_info.get('employee_id')
        current_role = employee_info.get('role', 'Sales')
        current_name = employee_info.get('name', 'Unknown')
        current_branch = employee_info.get('branch_code')
        
        logger.info(f"Approving request #{request_id}")
        logger.info(f"  Approver: {current_employee_id} ({current_name})")
        logger.info(f"  Role: {current_role}")
        logger.info(f"  Branch: {current_branch}")
        
        conn = get_mssql_conn()
        cursor = conn.cursor()
        
        # 1. ดึงข้อมูลคำขอ
        cursor.execute("""
            SELECT * FROM special_price_requests
            WHERE id = ?
        """, (request_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        
        columns = [column[0] for column in cursor.description]
        request = dict(zip(columns, row))
        
        current_status = request.get('status')
        approver_employee_id = request.get('approver_employee_id')
        
        logger.info(f"  Current status: {current_status}")
        logger.info(f"  Approver employee ID: {approver_employee_id}")
        
        # 2. ตรวจสอบสิทธิ์
        if current_role == 'ZM':
            # ZM ต้องเช็คว่าเป็น ZM ของสาขานี้
            expected_position = f"ZM_{current_branch}"
            if current_status != 'PENDING_ZM' and current_status != 'SDM_APPROVAL':
                raise HTTPException(status_code=403, detail="This request is not pending ZM approval")
            if approver_employee_id != expected_position:
                raise HTTPException(status_code=403, detail=f"You are not the assigned approver (expected {approver_employee_id})")
        
        elif current_role == 'RM':
            if current_status != 'PENDING_RM':
                raise HTTPException(status_code=403, detail="This request is not pending RM approval")
            
            # RM ต้องเช็คว่าคำขอมาจากสาขาในภูมิภาคที่ RM ดูแล
            # ดึง region ของคำขอจาก approver_employee_id (เช่น "RM_BE")
            if not approver_employee_id or not approver_employee_id.startswith('RM_'):
                raise HTTPException(status_code=400, detail="Invalid approver employee ID for RM")
            
            request_region = approver_employee_id.split('_')[1]  # "RM_BE" → "BE"
            rm_region = employee_info.get('region')  # Region ของ RM ที่ login
            
            logger.info(f"  Request region: {request_region}")
            logger.info(f"  RM region: {rm_region}")
            
            if request_region != rm_region:
                raise HTTPException(
                    status_code=403, 
                    detail=f"You are RM of region {rm_region}, but this request is from region {request_region}"
                )
        
        elif current_role == 'SDM':
            if current_status != 'PENDING_SDM':
                raise HTTPException(status_code=403, detail="This request is not pending SDM approval")
        
        else:
            raise HTTPException(status_code=403, detail="You do not have permission to approve requests")
        
        # 3. Query items เพื่อดู approval_level
        cursor.execute("""
            SELECT approval_level FROM special_price_request_items
            WHERE request_id = ?
        """, (request_id,))
        
        item_rows = cursor.fetchall()
        approval_levels = [row[0] for row in item_rows]
        
        # ตรวจสอบว่าต้องส่งต่อหรือไม่
        needs_rm = any(level in ['ZM_THEN_RM', 'RM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM'] for level in approval_levels)
        needs_sdm = any(level in ['SDM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM'] for level in approval_levels)
        
        logger.info(f"  Needs RM: {needs_rm}")
        logger.info(f"  Needs SDM: {needs_sdm}")
        
        # 4. กำหนด status ใหม่และ approver ใหม่
        new_status = None
        new_approver_id = None
        
        if current_status in ['PENDING_ZM', 'SDM_APPROVAL']:
            # ZM อนุมัติแล้ว
            if needs_rm or needs_sdm:
                # ส่งต่อ RM
                new_status = 'PENDING_RM'
                region = request.get('requester_region') or employee_info.get('region')
                new_approver_id = f"RM_{region}"
                logger.info(f"  → Forwarding to RM: {new_approver_id}")
            else:
                # อนุมัติเลย (ZM_ONLY)
                new_status = 'APPROVED'
                new_approver_id = None
                logger.info(f"  → Approved by ZM (final)")
        
        elif current_status == 'PENDING_RM':
            # RM อนุมัติแล้ว
            if needs_sdm:
                # ส่งต่อ SDM
                new_status = 'PENDING_SDM'
                new_approver_id = 'SDM_GLOBAL'
                logger.info(f"  → Forwarding to SDM")
            else:
                # อนุมัติเลย
                new_status = 'APPROVED'
                new_approver_id = None
                logger.info(f"  → Approved by RM (final)")
        
        elif current_status == 'PENDING_SDM':
            # SDM อนุมัติแล้ว (ขั้นสุดท้าย)
            new_status = 'APPROVED'
            new_approver_id = None
            logger.info(f"  → Approved by SDM (final)")
        
        # 5. อัปเดตฐานข้อมูล
        update_query = """
            UPDATE special_price_requests
            SET status = ?,
                approver_employee_id = ?,
                approved_by = ?,
                approved_at = GETDATE(),
                updated_at = GETDATE()
            WHERE id = ?
        """
        
        cursor.execute(update_query, (
            new_status,
            new_approver_id,
            current_employee_id,
            request_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Request #{request_id} approved successfully")
        logger.info(f"   New status: {new_status}")
        logger.info(f"   Approved by: {current_employee_id} ({current_name})")
        
        return {
            "success": True,
            "message": "Request approved successfully",
            "new_status": new_status,
            "approved_by": current_employee_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve request: {str(e)}"
        )


@router.post("/{request_id}/reject")
async def reject_request(request_id: int, employee_info: dict = Depends(get_employee_info)):
    """Reject - placeholder"""
    raise HTTPException(status_code=501, detail="Feature under development")
