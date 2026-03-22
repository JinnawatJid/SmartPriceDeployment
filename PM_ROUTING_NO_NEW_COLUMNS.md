# PM Routing - Using Existing Columns Only

## Solution
ใช้คอลัมน์เดิมเหมือนระดับอื่นๆ ไม่ต้องสร้างคอลัมน์ใหม่

---

## How It Works

### 1. Create Special Price Request (Price < SDM)

**Backend Logic:**
```python
# หา PM ตามหมวดหมู่สินค้า
pm_approver = await find_pm_by_category('A')  # PM Aluminium

# Log PM info (ไม่บันทึกลง database)
logger.info(f"PM Category: {pm_approver['category']}")  # 'A'
logger.info(f"PM Name: {pm_approver['name']}")
logger.info(f"Will route to: PM_{pm_approver['category']}")  # 'PM_A'

# บันทึกเหมือนระดับอื่น
status = 'PENDING_ZM'
approver_employee_id = 'ZM_03TS'
```

**Database:**
```sql
INSERT INTO special_price_requests (
    status,                  -- 'PENDING_ZM'
    approver_employee_id,    -- 'ZM_03TS'
    ...
)
```

---

### 2. ZM Approves

**Logic:**
```python
# เช็คว่ามี PM_APPROVAL level หรือไม่
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)

if needs_pm:
    new_status = 'PENDING_RM'
    new_approver_id = 'RM_BE'
else:
    new_status = 'APPROVED'
```

**Database:**
```sql
UPDATE special_price_requests
SET status = 'PENDING_RM',
    approver_employee_id = 'RM_BE',
    approved_by = '21748',  -- ZM employee ID
    ...
```

---

### 3. RM Approves

**Logic:**
```python
# เช็คว่ามี PM_APPROVAL level หรือไม่
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
```

**Database:**
```sql
UPDATE special_price_requests
SET status = 'PENDING_PM',
    approver_employee_id = 'PM_A',  -- Position ID
    approved_by = '21750',  -- RM employee ID
    ...
```

---

### 4. PM Approves

**Permission Check:**
```python
if current_role == 'PM':
    if current_status != 'PENDING_PM':
        raise HTTPException(403, "Not pending PM approval")
    
    # เช็ค category
    request_category = approver_employee_id.split('_')[1]  # 'PM_A' → 'A'
    logger.info(f"PM approval for category: {request_category}")
```

**Logic:**
```python
# PM อนุมัติเป็นขั้นสุดท้าย
new_status = 'APPROVED'
new_approver_id = None
```

**Database:**
```sql
UPDATE special_price_requests
SET status = 'APPROVED',
    approver_employee_id = NULL,
    approved_by = '21800',  -- PM employee ID
    ...
```

---

## Approval Flow

### Complete Flow (Price < SDM)

```
1. Create:
   status = 'PENDING_ZM'
   approver_employee_id = 'ZM_03TS'

2. ZM Approves:
   status = 'PENDING_RM'
   approver_employee_id = 'RM_BE'
   approved_by = '21748' (ZM)

3. RM Approves:
   status = 'PENDING_PM'
   approver_employee_id = 'PM_A'  ← Position ID based on category
   approved_by = '21750' (RM)

4. PM Approves:
   status = 'APPROVED'
   approver_employee_id = NULL
   approved_by = '21800' (PM)
```

---

## Position ID Format

| Role | Format | Example | Description |
|---|---|---|---|
| ZM | ZM_{branch} | ZM_03TS | ZM ของสาขา 03TS |
| RM | RM_{region} | RM_BE | RM ของภูมิภาค BE |
| SDM | SDM_GLOBAL | SDM_GLOBAL | SDM ที่ HQ |
| PM | PM_{category} | PM_A | PM Aluminium |

---

## Category Detection

**From SKU First Letter:**
```python
# A01010010108100000 → 'A' (Aluminium)
category = item.sku[0].upper()

# Query from database
SELECT DISTINCT LEFT(item_code, 1) as category
FROM special_price_request_items
WHERE request_id = ? AND approval_level = 'PM_APPROVAL'
```

**Category Mapping:**
- G = Glass (กระจก)
- A = Aluminium (อลูมิเนียม)
- C = CLine (ซีไลน์)
- Y = Yipsum (ยิปซั่ม)
- S = Sealant (ซีลแลนท์)
- E = Equipment (อุปกรณ์)

---

## Changes Made

### File: `backend/special_price_request_router.py`

#### 1. Create Request ✅
- ไม่บันทึกคอลัมน์ PM
- Log PM info สำหรับ debugging
- ใช้คอลัมน์เดิม: status, approver_employee_id

#### 2. RM Approval Logic ✅
```python
elif current_status == 'PENDING_RM':
    needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)
    
    if needs_pm:
        # ดึง category จาก items
        pm_category = get_category_from_items(request_id)
        new_status = 'PENDING_PM'
        new_approver_id = f'PM_{pm_category}'
```

#### 3. PM Permission Check ✅
```python
elif current_role == 'PM':
    if current_status != 'PENDING_PM':
        raise HTTPException(403)
    
    request_category = approver_employee_id.split('_')[1]
    logger.info(f"PM approval for category: {request_category}")
```

#### 4. PM Approval Logic ✅
```python
elif current_status == 'PENDING_PM':
    new_status = 'APPROVED'
    new_approver_id = None
```

---

## Database Schema (No Changes Needed)

### special_price_requests
```sql
status VARCHAR(50)                    -- 'PENDING_ZM', 'PENDING_RM', 'PENDING_PM', 'PENDING_SDM', 'APPROVED'
approver_employee_id VARCHAR(50)      -- 'ZM_03TS', 'RM_BE', 'PM_A', 'SDM_GLOBAL'
approved_by VARCHAR(50)               -- รหัสพนักงานจริงที่อนุมัติ
```

### special_price_request_items
```sql
item_code VARCHAR(50)                 -- SKU (ตัวอักษรแรกคือ category)
approval_level VARCHAR(50)            -- 'ZM_ONLY', 'ZM_THEN_RM', 'SDM_APPROVAL', 'PM_APPROVAL'
```

---

## Testing

### Test Case 1: Create Request (Price < SDM)
```
Product: A01010010108100000
Price: 155 < SDM 157
Expected:
  - status = 'PENDING_ZM'
  - approver_employee_id = 'ZM_03TS'
  - Log shows PM info
```

### Test Case 2: ZM Approves
```
Expected:
  - status = 'PENDING_RM'
  - approver_employee_id = 'RM_BE'
  - approved_by = ZM employee ID
```

### Test Case 3: RM Approves
```
Expected:
  - status = 'PENDING_PM'
  - approver_employee_id = 'PM_A'
  - approved_by = RM employee ID
```

### Test Case 4: PM Approves
```
Expected:
  - status = 'APPROVED'
  - approver_employee_id = NULL
  - approved_by = PM employee ID
```

---

## Advantages

1. ✅ **No Database Migration** - ใช้คอลัมน์เดิม
2. ✅ **Consistent Pattern** - เหมือนระดับอื่นๆ
3. ✅ **Simple Logic** - ไม่ซับซ้อน
4. ✅ **Easy to Maintain** - ไม่ต้องจัดการคอลัมน์เพิ่ม

---

**Status**: ✅ Implemented
**Database Changes**: None required
**Testing**: Ready
