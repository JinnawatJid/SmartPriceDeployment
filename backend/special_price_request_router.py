from fastapi import APIRouter, Depends, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
from auth_dependency import get_employee_info
from config.db_mssql import get_mssql_conn as get_db_connection

router = APIRouter(prefix="/api/special-price-requests", tags=["special-price-requests"])

# Load employees data for routing
def load_employees():
    """Load employees from employees.json"""
    try:
        with open('employees.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('employees', [])
    except Exception as e:
        print(f"Error loading employees.json: {e}")
        return []

EMPLOYEES = load_employees()

# ============ Models ============

class SpecialPriceItem(BaseModel):
    sku: str
    item_name: str
    quantity: float
    unit: str
    normal_price: float
    requested_price: float
    approval_level: Optional[str] = None  # ZM_ONLY, ZM_THEN_RM, REJECTED

class CreateSpecialPriceRequest(BaseModel):
    customer_code: str
    customer_name: str
    customer_type: Optional[str] = None
    items: List[SpecialPriceItem]
    request_reason: Optional[str] = None
    quote_no: Optional[str] = None  # Link to quote

class ApproveRequest(BaseModel):
    pass

class RejectRequest(BaseModel):
    reason: str

# ============ Helper Functions ============

def calculate_totals(items: List[SpecialPriceItem]):
    """Calculate original and requested totals"""
    original_total = sum(item.quantity * item.normal_price for item in items)
    requested_total = sum(item.quantity * item.requested_price for item in items)
    discount_percentage = ((original_total - requested_total) / original_total * 100) if original_total > 0 else 0
    return original_total, requested_total, discount_percentage

def get_next_request_number(conn):
    """Generate next request number"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ISNULL(MAX(CAST(SUBSTRING(request_number, 4, 10) AS INT)), 0) + 1
        FROM special_price_requests
        WHERE request_number LIKE 'SPR%'
    """)
    next_num = cursor.fetchone()[0]
    cursor.close()
    return f"SPR{next_num:06d}"

def log_audit(conn, request_id: int, action: str, old_status: str, new_status: str, 
              action_by: str, action_reason: Optional[str] = None, details: Optional[dict] = None):
    """Log action to audit trail - simplified version without audit table"""
    # Just print to console for now since we don't have audit table
    print(f"[AUDIT] Request {request_id}: {action} | {old_status} → {new_status} | By: {action_by}")
    if action_reason:
        print(f"[AUDIT] Reason: {action_reason}")
    if details:
        print(f"[AUDIT] Details: {details}")

def find_approver(branch_code: str, role: str):
    """Find approver by branch and role (ZM or RM)"""
    for emp in EMPLOYEES:
        if emp.get('branch') == branch_code and emp.get('role') == role:
            return emp
    return None

def find_rm_by_region(region: str):
    """Find Regional Manager by region"""
    for emp in EMPLOYEES:
        if emp.get('region') == region and emp.get('role') == 'RM':
            return emp
    return None

def route_request(conn, request_id, requester_branch: str, requester_region: str, approval_level: str):
    """
    Route request to appropriate approver based on approval level
    If request_id is None, only return routing info without updating database
    
    Args:
        conn: Database connection
        request_id: Request ID (can be None for initial routing)
        requester_branch: Branch code of the requester
        requester_region: Region of the requester
        approval_level: ZM_ONLY or ZM_THEN_RM
    
    Returns:
        tuple: (new_status, approver_id, approver_branch, approver_region)
    """
    cursor = conn.cursor()
    
    if approval_level == 'ZM_ONLY':
        # Single-level approval: Route to ZM in same branch
        zm = find_approver(requester_branch, 'ZM')
        
        if not zm:
            raise HTTPException(
                status_code=500, 
                detail=f"No Zone Manager found for branch {requester_branch}"
            )
        
        # Update request with approver info (only if request_id exists)
        if request_id is not None:
            cursor.execute("""
                UPDATE special_price_requests
                SET approver_employee_id = ?, updated_at = GETDATE()
                WHERE id = ?
            """, (zm['employee_id'], request_id))
            conn.commit()
        
        cursor.close()
        
        return ('SUBMITTED', zm['employee_id'], zm['branch'], zm['region'])
    
    elif approval_level == 'ZM_THEN_RM':
        # Multi-level approval: Route to ZM first
        zm = find_approver(requester_branch, 'ZM')
        
        if not zm:
            raise HTTPException(
                status_code=500,
                detail=f"No Zone Manager found for branch {requester_branch}"
            )
        
        # Update request with ZM info (only if request_id exists)
        if request_id is not None:
            cursor.execute("""
                UPDATE special_price_requests
                SET approver_employee_id = ?, updated_at = GETDATE()
                WHERE id = ?
            """, (zm['employee_id'], request_id))
            conn.commit()
        
        cursor.close()
        
        return ('PENDING_ZM', zm['employee_id'], zm['branch'], zm['region'])
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid approval level: {approval_level}")

def forward_to_rm(conn, request_id: int, zm_region: str):
    """
    Forward request from ZM to RM in the same region
    Update the approver info in the main request record
    
    Args:
        conn: Database connection
        request_id: Request ID
        zm_region: Region of the Zone Manager who approved
    
    Returns:
        tuple: (approver_id, approver_branch, approver_region)
    """
    cursor = conn.cursor()
    
    # Find RM in the same region
    rm = find_rm_by_region(zm_region)
    
    if not rm:
        raise HTTPException(
            status_code=500,
            detail=f"No Regional Manager found for region {zm_region}"
        )
    
    # Update request with RM info (ไม่มี approver_branch, approver_region ในตาราง)
    cursor.execute("""
        UPDATE special_price_requests
        SET approver_employee_id = ?, updated_at = GETDATE()
        WHERE id = ?
    """, (rm['employee_id'], request_id))
    
    conn.commit()
    cursor.close()
    
    return (rm['employee_id'], rm['branch'], rm['region'])

# ============ Endpoints ============

@router.post("")
async def create_special_price_request(
    req: CreateSpecialPriceRequest,
    employee_info: dict = Depends(get_employee_info)
):
    """Create and submit a new special price request (no DRAFT status)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validate required fields
        if not req.customer_code or not req.items:
            raise HTTPException(status_code=400, detail="Customer code and items are required")
        
        # Calculate totals
        original_total, requested_total, discount_percentage = calculate_totals(req.items)
        
        # Generate request number
        request_number = get_next_request_number(conn)
        
        # Determine approval level from items
        approval_level = 'ZM_ONLY'  # Default
        for item in req.items:
            if item.approval_level == 'ZM_THEN_RM':
                approval_level = 'ZM_THEN_RM'
                break
            elif item.approval_level == 'REJECTED':
                raise HTTPException(
                    status_code=400,
                    detail=f"Item {item.sku} has price outside acceptable range"
                )
        
        # Get requester's branch and region
        requester_branch = employee_info.get('branch_code')
        requester_region = None
        
        # Find region
        for emp in EMPLOYEES:
            if emp.get('employee_id') == employee_info.get('employee_id'):
                requester_region = emp.get('region')
                break
        
        if not requester_region:
            for emp in EMPLOYEES:
                if emp.get('branch') == requester_branch:
                    requester_region = emp.get('region')
                    break
        
        if not requester_region:
            branch_num = requester_branch[:2] if requester_branch else "00"
            if branch_num in ["00", "01", "03", "04", "06", "15", "24", "90"]:
                requester_region = "BE"
            elif branch_num in ["11", "12", "17", "23"]:
                requester_region = "N"
            elif branch_num in ["13", "14", "16"]:
                requester_region = "S"
            elif branch_num in ["08", "09", "10", "18", "20"]:
                requester_region = "NE"
            elif branch_num in ["05", "07", "19", "21", "25"]:
                requester_region = "C"
            else:
                requester_region = "BE"
        
        # Route to get approver and initial status
        new_status, approver_id, approver_branch, approver_region = route_request(
            conn, None, requester_branch, requester_region, approval_level
        )
        
        # Insert main request with routed status (not DRAFT)
        cursor.execute("""
            INSERT INTO special_price_requests 
            (request_number, quote_no, customer_code, customer_name, customer_type, 
             requester_name, request_reason, original_total, requested_total, 
             discount_percentage, status, branch, approver_employee_id, 
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """, (
            request_number,
            req.quote_no,
            req.customer_code,
            req.customer_name,
            req.customer_type,
            employee_info.get('name', 'Unknown'),
            req.request_reason,
            original_total,
            requested_total,
            discount_percentage,
            new_status,  # Use routed status instead of DRAFT
            employee_info.get('branch_code'),
            approver_id
        ))
        
        conn.commit()
        
        # Get the inserted request ID
        cursor.execute("SELECT @@IDENTITY")
        request_id = cursor.fetchone()[0]
        
        # Insert items
        for item in req.items:
            item_original = item.quantity * item.normal_price
            item_requested = item.quantity * item.requested_price
            
            cursor.execute("""
                INSERT INTO special_price_request_items
                (request_id, item_code, item_name, quantity, unit, normal_price, 
                 requested_price, original_amount, requested_amount, is_below_normal, 
                 approval_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                request_id,
                item.sku,
                item.item_name,
                item.quantity,
                item.unit,
                item.normal_price,
                item.requested_price,
                item_original,
                item_requested,
                1 if item.requested_price < item.normal_price else 0,
                item.approval_level or 'ZM_ONLY'
            ))
        
        conn.commit()
        
        # Log audit
        log_audit(conn, request_id, 'CREATED_AND_SUBMITTED', None, new_status, 
                 employee_info.get('employee_id'), 
                 details={
                     'items_count': len(req.items),
                     'approval_level': approval_level,
                     'routed_to': approver_id
                 })
        
        cursor.close()
        conn.close()
        
        return {
            "id": request_id,
            "request_number": request_number,
            "status": new_status,
            "message": "สร้างและส่งใบขอราคาพิเศษสำเร็จ"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_special_price_requests(
    status: Optional[str] = Query(None),
    employee_info: dict = Depends(get_employee_info)
):
    """List special price requests with role-based filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        role = employee_info.get('role', 'Sales')
        employee_id = employee_info.get('employee_id')
        branch_code = employee_info.get('branch_code')
        
        # Build query based on role
        if role == 'Sales':
            # Sales employees see only their own requests
            query = "SELECT * FROM special_price_requests WHERE employee_id = ?"
            params = [employee_id]
        elif role == 'Branch Manager':
            # Branch managers see requests from their branch
            query = "SELECT * FROM special_price_requests WHERE branch = ?"
            params = [branch_code]
        elif role == 'Regional Manager':
            # Regional managers see requests from their region
            query = """
                SELECT spr.* FROM special_price_requests spr
                JOIN employees e ON spr.employee_id = e.employee_id
                WHERE e.region = (SELECT region FROM employees WHERE employee_id = ?)
            """
            params = [employee_id]
        else:
            query = "SELECT * FROM special_price_requests WHERE 1=0"
            params = []
        
        # Add status filter if provided
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        requests = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Fetch items for each request
        for req in requests:
            cursor.execute(
                "SELECT * FROM special_price_request_items WHERE request_id = ?",
                [req['id']]
            )
            item_columns = [description[0] for description in cursor.description]
            req['items'] = [dict(zip(item_columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return requests
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{request_id}")
async def get_special_price_request(
    request_id: int,
    employee_info: dict = Depends(get_employee_info)
):
    """Get specific special price request details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM special_price_requests WHERE id = ?", [request_id])
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        
        request = dict(zip(columns, row))
        
        # Fetch items
        cursor.execute(
            "SELECT * FROM special_price_request_items WHERE request_id = ?",
            [request_id]
        )
        item_columns = [description[0] for description in cursor.description]
        request['items'] = [dict(zip(item_columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return request
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{request_id}")
async def update_special_price_request(
    request_id: int,
    req: CreateSpecialPriceRequest,
    employee_info: dict = Depends(get_employee_info)
):
    """Update a Draft special price request"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if request exists and is in Draft status
        cursor.execute(
            "SELECT status, employee_id FROM special_price_requests WHERE id = ?",
            [request_id]
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        
        status, original_employee = row
        
        if status != 'DRAFT':
            raise HTTPException(status_code=400, detail="Can only edit Draft requests")
        
        if original_employee != employee_info.get('employee_id'):
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Calculate totals
        original_total, requested_total, discount_percentage = calculate_totals(req.items)
        
        # Update main request
        cursor.execute("""
            UPDATE special_price_requests
            SET customer_code = ?, customer_name = ?, customer_type = ?,
                original_total = ?, requested_total = ?, discount_percentage = ?,
                request_reason = ?, updated_at = GETDATE()
            WHERE id = ?
        """, (
            req.customer_code,
            req.customer_name,
            req.customer_type,
            original_total,
            requested_total,
            discount_percentage,
            req.request_reason,
            request_id
        ))
        
        # Delete old items
        cursor.execute("DELETE FROM special_price_request_items WHERE request_id = ?", [request_id])
        
        # Insert new items (รองรับ approval_level column)
        for item in req.items:
            item_original = item.quantity * item.normal_price
            item_requested = item.quantity * item.requested_price
            
            cursor.execute("""
                INSERT INTO special_price_request_items
                (request_id, item_code, item_name, quantity, unit, normal_price,
                 requested_price, original_amount, requested_amount, is_below_normal, 
                 approval_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                request_id,
                item.sku,
                item.item_name,
                item.quantity,
                item.unit,
                item.normal_price,
                item.requested_price,
                item_original,
                item_requested,
                1 if item.requested_price < item.normal_price else 0,
                item.approval_level or 'ZM_ONLY'
            ))
        
        conn.commit()
        
        # Log audit
        log_audit(conn, request_id, 'MODIFIED', 'DRAFT', 'DRAFT',
                 employee_info.get('employee_id'), details={'items_count': len(req.items)})
        
        cursor.close()
        conn.close()
        
        return {"message": "อัปเดตใบขอราคาพิเศษสำเร็จ"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{request_id}/submit")
async def submit_special_price_request(
    request_id: int,
    employee_info: dict = Depends(get_employee_info)
):
    """Submit request for approval with automatic routing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute(
            "SELECT * FROM special_price_requests WHERE id = ?",
            [request_id]
        )
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        
        request = dict(zip(columns, row))
        
        if request['status'] != 'DRAFT':
            raise HTTPException(status_code=400, detail="Only Draft requests can be submitted")
        
        # Get request items to determine approval level
        cursor.execute(
            "SELECT * FROM special_price_request_items WHERE request_id = ?",
            [request_id]
        )
        item_columns = [description[0] for description in cursor.description]
        items = [dict(zip(item_columns, row)) for row in cursor.fetchall()]
        
        if not items:
            raise HTTPException(status_code=400, detail="Request has no items")
        
        # Determine overall approval level (use the highest level required)
        approval_level = 'ZM_ONLY'  # Default to single-level
        
        for item in items:
            # Check if any item requires multi-level approval
            # This should be determined by the frontend based on price thresholds
            # For now, we'll check if the item has approval_level field
            item_approval = item.get('approval_level', 'ZM_ONLY')
            
            if item_approval == 'ZM_THEN_RM':
                approval_level = 'ZM_THEN_RM'
                break  # If any item needs multi-level, the whole request needs it
            elif item_approval == 'REJECTED':
                raise HTTPException(
                    status_code=400,
                    detail=f"Item {item['item_code']} has price outside acceptable range"
                )
        
        # Get requester's branch and region
        requester_branch = employee_info.get('branch_code')
        
        # Find requester's region from branch (ค้นหาจาก ZM/RM ที่อยู่ branch เดียวกัน)
        requester_region = None
        
        # ลองหาจาก employee_id ก่อน
        for emp in EMPLOYEES:
            if emp.get('employee_id') == employee_info.get('employee_id'):
                requester_region = emp.get('region')
                break
        
        # ถ้าไม่เจอ (Sales ไม่ได้อยู่ใน list) ให้หาจาก branch
        if not requester_region:
            for emp in EMPLOYEES:
                if emp.get('branch') == requester_branch:
                    requester_region = emp.get('region')
                    break
        
        if not requester_region:
            # ถ้ายังไม่เจอ ให้ใช้ default region ตาม branch code
            # BE = Bangkok Extended (00-06, 15, 24, 90)
            # N = North (11-12, 17, 23)
            # S = South (13-14, 16)
            # NE = Northeast (08-10, 18, 20-21)
            # C = Central (05, 07, 19, 21, 25)
            branch_num = requester_branch[:2] if requester_branch else "00"
            
            if branch_num in ["00", "01", "03", "04", "06", "15", "24", "90"]:
                requester_region = "BE"
            elif branch_num in ["11", "12", "17", "23"]:
                requester_region = "N"
            elif branch_num in ["13", "14", "16"]:
                requester_region = "S"
            elif branch_num in ["08", "09", "10", "18", "20"]:
                requester_region = "NE"
            elif branch_num in ["05", "07", "19", "21", "25"]:
                requester_region = "C"
            else:
                requester_region = "BE"  # default
        
        print(f"[ROUTING] Requester: employee_id={employee_info.get('employee_id')}, branch={requester_branch}, region={requester_region}")
        
        # Route the request
        new_status, approver_id, approver_branch, approver_region = route_request(
            conn, request_id, requester_branch, requester_region, approval_level
        )
        
        # Update request status (ไม่มี approval_level column ในตาราง)
        cursor.execute("""
            UPDATE special_price_requests
            SET status = ?, updated_at = GETDATE()
            WHERE id = ?
        """, (new_status, request_id))
        
        conn.commit()
        
        # Log audit
        log_audit(conn, request_id, 'SUBMITTED', 'DRAFT', new_status,
                 employee_info.get('employee_id'), 
                 details={
                     'approval_level': approval_level,
                     'routed_to': approver_id,
                     'approver_branch': approver_branch,
                     'approver_region': approver_region
                 })
        
        cursor.close()
        conn.close()
        
        return {
            "id": request_id,
            "status": new_status,
            "approval_level": approval_level,
            "routed_to": approver_id,
            "message": "ส่งใบขอราคาพิเศษสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{request_id}/approve")
async def approve_special_price_request(
    request_id: int,
    employee_info: dict = Depends(get_employee_info)
):
    """Approve a special price request with role-based routing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get request
        cursor.execute(
            "SELECT * FROM special_price_requests WHERE id = ?",
            [request_id]
        )
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        
        request = dict(zip(columns, row))
        old_status = request['status']
        
        # Get approval level from items (highest level required)
        cursor.execute("""
            SELECT approval_level 
            FROM special_price_request_items 
            WHERE request_id = ?
        """, [request_id])
        
        item_approval_levels = [row[0] for row in cursor.fetchall()]
        
        # Determine overall approval level (ZM_THEN_RM takes precedence)
        if 'ZM_THEN_RM' in item_approval_levels:
            approval_level = 'ZM_THEN_RM'
        elif 'ZM_ONLY' in item_approval_levels:
            approval_level = 'ZM_ONLY'
        else:
            approval_level = 'ZM_ONLY'  # Default
        
        print(f"[APPROVE] Request {request_id}: status={old_status}, approval_level={approval_level}, item_levels={item_approval_levels}")
        
        # Get approver's role and region from employees.json
        approver_id = employee_info.get('employee_id')
        approver_role = None
        approver_region = None
        
        print(f"[APPROVE] Looking up employee_id: {approver_id}")
        
        for emp in EMPLOYEES:
            if emp.get('employee_id') == approver_id:
                approver_role = emp.get('role')
                approver_region = emp.get('region')
                print(f"[APPROVE] Found employee: role={approver_role}, region={approver_region}")
                break
        
        if not approver_role:
            print(f"[APPROVE] Employee {approver_id} not found in employees.json")
            raise HTTPException(
                status_code=403,
                detail="Employee not found in approver list"
            )
        
        # Verify approver is authorized
        if approver_role not in ['ZM', 'RM']:
            print(f"[APPROVE] Employee {approver_id} has role {approver_role}, not ZM or RM")
            raise HTTPException(
                status_code=403,
                detail="Only Zone Managers and Regional Managers can approve requests"
            )
        
        # Verify approver matches the routed approver
        print(f"[APPROVE] Checking authorization: request.approver_employee_id={request.get('approver_employee_id')}, approver_id={approver_id}")
        if request.get('approver_employee_id') != approver_id:
            raise HTTPException(
                status_code=403,
                detail=f"You are not authorized to approve this request. This request is assigned to employee {request.get('approver_employee_id')}"
            )
        
        # Determine new status based on approval level and current status
        new_status = None
        
        if approval_level == 'ZM_ONLY':
            # Single-level approval: ZM approves → APPROVED
            if approver_role != 'ZM':
                raise HTTPException(
                    status_code=403,
                    detail="Only Zone Manager can approve this request"
                )
            new_status = 'APPROVED'
            
        elif approval_level == 'ZM_THEN_RM':
            # Multi-level approval
            if old_status in ['SUBMITTED', 'PENDING_ZM']:
                # ZM approval → forward to RM
                if approver_role != 'ZM':
                    raise HTTPException(
                        status_code=403,
                        detail="Only Zone Manager can approve at this stage"
                    )
                
                print(f"[APPROVE] ZM approving, forwarding to RM in region {approver_region}")
                
                # Forward to RM in same region
                rm_id, rm_branch, rm_region = forward_to_rm(conn, request_id, approver_region)
                
                print(f"[APPROVE] Forwarded to RM: {rm_id} ({rm_branch}, {rm_region})")
                
                new_status = 'PENDING_RM'
                
                # Update request status
                cursor.execute("""
                    UPDATE special_price_requests
                    SET status = ?, approver_employee_id = ?, updated_at = GETDATE()
                    WHERE id = ?
                """, (new_status, rm_id, request_id))
                
                conn.commit()
                
                # Log audit
                log_audit(conn, request_id, 'ZM_APPROVED', old_status, new_status,
                         approver_id, 
                         details={
                             'forwarded_to': rm_id,
                             'rm_branch': rm_branch,
                             'rm_region': rm_region
                         })
                
                cursor.close()
                conn.close()
                
                return {
                    "id": request_id,
                    "status": new_status,
                    "message": "อนุมัติและส่งต่อไปยัง Regional Manager สำเร็จ",
                    "forwarded_to": rm_id
                }
                
            elif old_status == 'PENDING_RM':
                # RM approval → APPROVED
                if approver_role != 'RM':
                    raise HTTPException(
                        status_code=403,
                        detail="Only Regional Manager can approve at this stage"
                    )
                new_status = 'APPROVED'
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot approve request in status: {old_status}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid approval level: {approval_level}"
            )
        
        # Update request status
        cursor.execute("""
            UPDATE special_price_requests
            SET status = ?, approved_by = ?, approved_at = GETDATE(), updated_at = GETDATE()
            WHERE id = ?
        """, (new_status, employee_info.get('name'), request_id))
        
        conn.commit()
        
        # Log audit
        log_audit(conn, request_id, 'APPROVED', old_status, new_status, approver_id)
        
        cursor.close()
        conn.close()
        
        return {
            "id": request_id,
            "status": new_status,
            "message": "อนุมัติใบขอราคาพิเศษสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in approve: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{request_id}/reject")
async def reject_special_price_request(
    request_id: int,
    req: RejectRequest,
    employee_info: dict = Depends(get_employee_info)
):
    """Reject a special price request"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get request
        cursor.execute(
            "SELECT * FROM special_price_requests WHERE id = ?",
            [request_id]
        )
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Request not found")
        
        request = dict(zip(columns, row))
        old_status = request['status']
        
        if old_status not in ['SUBMITTED', 'PENDING_ZM']:
            raise HTTPException(status_code=400, detail="Request cannot be rejected in current status")
        
        # Update status to REJECTED
        new_status = 'REJECTED'
        cursor.execute("""
            UPDATE special_price_requests
            SET status = ?, rejection_reason = ?, approver_employee_id = ?, approved_by = ?, 
                approved_at = GETDATE(), updated_at = GETDATE()
            WHERE id = ?
        """, (new_status, req.reason, employee_info.get('employee_id'), 
              employee_info.get('name'), request_id))
        
        conn.commit()
        
        # Log audit
        log_audit(conn, request_id, 'REJECTED', old_status, new_status,
                 employee_info.get('employee_id'), req.reason)
        
        cursor.close()
        conn.close()
        
        return {
            "id": request_id,
            "status": new_status,
            "message": "ปฏิเสธใบขอราคาพิเศษสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending/approvals")
async def get_pending_approvals(
    employee_info: dict = Depends(get_employee_info)
):
    """Get pending approvals for current user (ZM or RM)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        employee_id = employee_info.get('employee_id')
        
        print(f"[PENDING APPROVALS] Checking for employee_id: {employee_id}")
        
        # ดึงรายการที่ส่งมาให้ employee นี้อนุมัติ
        # โดยดูจาก approver_employee_id และ status
        query = """
            SELECT * FROM special_price_requests
            WHERE approver_employee_id = ? 
            AND status IN ('SUBMITTED', 'PENDING_ZM', 'PENDING_RM')
            ORDER BY created_at DESC
        """
        params = [employee_id]
        
        print(f"[PENDING APPROVALS] Query: {query}")
        print(f"[PENDING APPROVALS] Params: {params}")
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        requests = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        print(f"[PENDING APPROVALS] Found {len(requests)} requests for employee {employee_id}")
        
        if len(requests) > 0:
            print(f"[PENDING APPROVALS] First request: {requests[0].get('request_number')} - Status: {requests[0].get('status')}")
        
        # Fetch items for each request
        for req in requests:
            cursor.execute(
                "SELECT * FROM special_price_request_items WHERE request_id = ?",
                [req['id']]
            )
            item_columns = [description[0] for description in cursor.description]
            req['items'] = [dict(zip(item_columns, row)) for row in cursor.fetchall()]
            
            print(f"[PENDING APPROVALS] Request {req['id']} has {len(req['items'])} items")
            if len(req['items']) > 0:
                print(f"[PENDING APPROVALS] First item approval_level: {req['items'][0].get('approval_level')}")
        
        cursor.close()
        conn.close()
        
        return requests
        
    except Exception as e:
        print(f"[PENDING APPROVALS ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/approver-info")
async def get_approver_info(
    employee_info: dict = Depends(get_employee_info)
):
    """Get approver information (ZM and RM) for the current user's branch"""
    try:
        branch_code = employee_info.get('branch_code')
        employee_id = employee_info.get('employee_id')
        
        if not branch_code:
            raise HTTPException(
                status_code=400,
                detail="Branch code not found in employee information"
            )
        
        # Find employee's region from EMPLOYEES data
        employee_region = None
        for emp in EMPLOYEES:
            if emp.get('employee_id') == employee_id:
                employee_region = emp.get('region')
                break
        
        # Find ZM for the branch
        zm = find_approver(branch_code, 'ZM')
        
        if not zm:
            # If no ZM found for exact branch, try to find by region
            if employee_region:
                for emp in EMPLOYEES:
                    if emp.get('region') == employee_region and emp.get('role') == 'ZM':
                        zm = emp
                        break
        
        if not zm:
            raise HTTPException(
                status_code=404,
                detail=f"No Zone Manager found for branch {branch_code}"
            )
        
        # Find RM for the region
        rm = find_rm_by_region(zm.get('region'))
        
        return {
            "zone_manager": {
                "employee_id": zm.get('employee_id'),
                "branch": zm.get('branch'),
                "region": zm.get('region'),
                "role": zm.get('role')
            },
            "regional_manager": {
                "employee_id": rm.get('employee_id') if rm else None,
                "branch": rm.get('branch') if rm else None,
                "region": rm.get('region') if rm else None,
                "role": rm.get('role') if rm else None
            } if rm else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_approver_info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quote/{quote_no:path}")
async def get_special_price_request_by_quote(
    quote_no: str,
    employee_info: dict = Depends(get_employee_info)
):
    """Get special price request by quote number (using path parameter with :path to accept slashes)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"[BY-QUOTE] Looking for quote_no: {quote_no}")
        
        cursor.execute("""
            SELECT * FROM special_price_requests 
            WHERE quote_no = ?
            ORDER BY created_at DESC
        """, [quote_no])
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        if not rows:
            cursor.close()
            conn.close()
            return []
        
        requests = []
        for row in rows:
            request = dict(zip(columns, row))
            
            # Fetch items
            cursor.execute(
                "SELECT * FROM special_price_request_items WHERE request_id = ?",
                [request['id']]
            )
            item_columns = [description[0] for description in cursor.description]
            request['items'] = [dict(zip(item_columns, item_row)) for item_row in cursor.fetchall()]
            
            # Get approver info
            approver_id = request.get('approver_employee_id')
            if approver_id:
                approver_info = None
                for emp in EMPLOYEES:
                    if emp.get('employee_id') == approver_id:
                        approver_info = emp
                        break
                request['approver_info'] = approver_info
            
            requests.append(request)
        
        cursor.close()
        conn.close()
        
        return requests
        
    except Exception as e:
        print(f"Error in get_special_price_request_by_quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))
