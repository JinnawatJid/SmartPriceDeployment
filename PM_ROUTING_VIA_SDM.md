# PM Routing - Via SDM

## ✅ FIXED: Circular Logic Issue

### The Problem
The original code had `needs_pm` calculated twice:
1. Once at the top (but not used in ZM section)
2. Again in the RM section (creating redundant logic)

This caused confusion because:
- `needs_sdm` didn't include PM_APPROVAL items
- But PM routing requires going through SDM
- The logic was inconsistent

### The Solution
Calculate `needs_pm` once at the top alongside `needs_rm` and `needs_sdm`:

```python
# Calculate ALL routing needs once
needs_rm = any(level in ['ZM_THEN_RM', 'RM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM', 'PM_APPROVAL'] for level in approval_levels)
needs_sdm = any(level in ['SDM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM'] for level in approval_levels)
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)
```

Then use consistently throughout:

```python
# ZM approval
if needs_rm or needs_sdm or needs_pm:
    # Route to RM
    
# RM approval  
if needs_pm or needs_sdm:
    # Route to SDM (SDM will route to PM if needed)
    
# SDM approval
if needs_pm:
    # Route to PM
```

---

## Approval Flow (Price < SDM)

### Updated Flow ✅
```
Sales → ZM → RM → SDM → PM (by Category) → Approved
```

**Key Point:** SDM ต้องเป็นคนส่งต่อให้ PM

---

## Step-by-Step Flow

### 1. Create Request (Price < SDM)
```python
# Frontend: approval_level = 'PM_APPROVAL'
# Backend:
status = 'PENDING_ZM'
approver_employee_id = 'ZM_03TS'
```

### 2. ZM Approves
```python
# Check: needs_pm or needs_sdm
if needs_pm or needs_sdm:
    new_status = 'PENDING_RM'
    new_approver_id = 'RM_BE'
```

**Database:**
```sql
status = 'PENDING_RM'
approver_employee_id = 'RM_BE'
approved_by = '21748' (ZM)
```

### 3. RM Approves
```python
# Check: needs_pm or needs_sdm
if needs_pm or needs_sdm:
    # ส่งต่อ SDM (ไม่ว่าจะต้อง PM หรือ SDM)
    new_status = 'PENDING_SDM'
    new_approver_id = 'SDM_GLOBAL'
```

**Database:**
```sql
status = 'PENDING_SDM'
approver_employee_id = 'SDM_GLOBAL'
approved_by = '21750' (RM)
```

### 4. SDM Approves
```python
# Check: needs_pm
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)

if needs_pm:
    # ดึง category จาก items
    cursor.execute("""
        SELECT DISTINCT LEFT(item_code, 1) as category
        FROM special_price_request_items
        WHERE request_id = ? AND approval_level = 'PM_APPROVAL'
    """)
    
    pm_category = cursor.fetchone()[0]  # 'A'
    new_status = 'PENDING_PM'
    new_approver_id = f'PM_{pm_category}'  # 'PM_A'
else:
    # อนุมัติเลย (ไม่ต้อง PM)
    new_status = 'APPROVED'
```

**Database:**
```sql
status = 'PENDING_PM'
approver_employee_id = 'PM_A'
approved_by = '21755' (SDM)
```

### 5. PM Approves
```python
# PM อนุมัติเป็นขั้นสุดท้าย
new_status = 'APPROVED'
new_approver_id = None
```

**Database:**
```sql
status = 'APPROVED'
approver_employee_id = NULL
approved_by = '21800' (PM)
```

---

## Approval Levels

| Level | Price Range | Flow |
|---|---|---|
| ZM_ONLY | R1 > price >= W2 | Sales → ZM → Approved |
| ZM_THEN_RM | W2 > price >= W1 | Sales → ZM → RM → Approved |
| SDM_APPROVAL | W1 > price >= SDM | Sales → ZM → RM → SDM → Approved |
| PM_APPROVAL | price < SDM | Sales → ZM → RM → SDM → PM → Approved ✅ |

---

## Code Changes

### File: `backend/special_price_request_router.py`

#### 1. RM Approval Logic ✅
```python
elif current_status == 'PENDING_RM':
    needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)
    
    if needs_pm or needs_sdm:
        # ส่งต่อ SDM (SDM จะเป็นคนส่งต่อให้ PM)
        new_status = 'PENDING_SDM'
        new_approver_id = 'SDM_GLOBAL'
```

#### 2. SDM Approval Logic ✅
```python
elif current_status == 'PENDING_SDM':
    needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)
    
    if needs_pm:
        # ดึง category จาก items
        pm_category = get_category_from_items(request_id)
        new_status = 'PENDING_PM'
        new_approver_id = f'PM_{pm_category}'
    else:
        # อนุมัติเลย
        new_status = 'APPROVED'
```

#### 3. PM Approval Logic ✅
```python
elif current_status == 'PENDING_PM':
    # PM อนุมัติเป็นขั้นสุดท้าย
    new_status = 'APPROVED'
    new_approver_id = None
```

---

## Example Scenario

### Product: A01010010108100000 (Aluminium)
- SDM: 157 บาท
- Requested: 155 บาท (< SDM)

### Flow:

**Step 1: Create**
```
status: PENDING_ZM
approver: ZM_03TS
```

**Step 2: ZM Approves**
```
status: PENDING_RM
approver: RM_BE
approved_by: 21748 (ZM)
```

**Step 3: RM Approves**
```
status: PENDING_SDM
approver: SDM_GLOBAL
approved_by: 21750 (RM)
```

**Step 4: SDM Approves**
```
status: PENDING_PM
approver: PM_A (Aluminium)
approved_by: 21755 (SDM)
```

**Step 5: PM Approves**
```
status: APPROVED
approver: NULL
approved_by: 21800 (PM Aluminium)
```

---

## Database Queries

### Check Current Status
```sql
SELECT 
    id, quote_no, status, 
    approver_employee_id,
    approved_by,
    created_at, updated_at
FROM special_price_requests
WHERE quote_no = 'QT-001'
```

### Check Approval History
```sql
SELECT 
    r.quote_no,
    r.status,
    r.approver_employee_id,
    r.approved_by,
    i.item_code,
    i.approval_level
FROM special_price_requests r
JOIN special_price_request_items i ON r.id = i.request_id
WHERE r.quote_no = 'QT-001'
```

### Find Pending PM Approvals
```sql
SELECT 
    id, quote_no, customer_code,
    approver_employee_id,  -- PM_A, PM_G, etc.
    original_total, requested_total,
    created_at
FROM special_price_requests
WHERE status = 'PENDING_PM'
ORDER BY created_at DESC
```

---

## Testing

### Test Case 1: Create Request (Price < SDM)
```
Input:
  - Product: A01010010108100000
  - Price: 155 < SDM 157

Expected:
  - status = 'PENDING_ZM'
  - approver_employee_id = 'ZM_03TS'
  - approval_level = 'PM_APPROVAL'
```

### Test Case 2: ZM → RM
```
Action: ZM approves

Expected:
  - status = 'PENDING_RM'
  - approver_employee_id = 'RM_BE'
```

### Test Case 3: RM → SDM
```
Action: RM approves

Expected:
  - status = 'PENDING_SDM'
  - approver_employee_id = 'SDM_GLOBAL'
```

### Test Case 4: SDM → PM
```
Action: SDM approves

Expected:
  - status = 'PENDING_PM'
  - approver_employee_id = 'PM_A'
  - Category extracted from SKU
```

### Test Case 5: PM → Approved
```
Action: PM approves

Expected:
  - status = 'APPROVED'
  - approver_employee_id = NULL
```

---

## Advantages

1. ✅ **SDM Control** - SDM เห็นและควบคุมทุกคำขอที่ราคา < SDM
2. ✅ **Consistent Flow** - ทุกคำขอที่ต้อง PM ต้องผ่าน SDM ก่อน
3. ✅ **No Database Changes** - ใช้คอลัมน์เดิม
4. ✅ **Clear Hierarchy** - ZM → RM → SDM → PM

---

## Summary

### Key Changes
- RM ส่งต่อ SDM (ไม่ส่งตรงไป PM)
- SDM เป็นคนส่งต่อให้ PM
- PM อนุมัติเป็นขั้นสุดท้าย

### Flow
```
Price < SDM:
  Sales → ZM → RM → SDM → PM (by Category) → Approved
  
Price >= SDM:
  Sales → ZM → RM → SDM → Approved
```

---

**Status**: ✅ Implemented
**Flow**: Sales → ZM → RM → SDM → PM → Approved
**Database**: No changes needed
