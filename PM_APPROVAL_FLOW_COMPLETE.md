# PM Approval Flow - Complete Guide

## Scenario: ราคา < SDM

**ตัวอย่าง:**
- สินค้า: A01010010108100000 (อลูมิเนียม)
- SDM: 157 บาท
- ราคาที่ขอ: 155 บาท (< SDM)
- ผู้ขอ: Sales
- ผู้อนุมัติ: ZM (ผู้จัดการสาขา)

---

## Complete Approval Flow

```
Step 1: Sales สร้างคำขอ
  ↓
Step 2: ZM (ผู้จัดการสาขา) อนุมัติ
  ↓
Step 3: RM (ผู้จัดการภูมิภาค) อนุมัติ
  ↓
Step 4: SDM (ผู้จัดการฝ่ายขาย) อนุมัติ
  ↓
Step 5: PM (ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม) อนุมัติ
  ↓
✅ APPROVED
```

---

## Step-by-Step Details

### Step 1: Sales สร้างคำขอ

**Action**: Sales เลือกสินค้าและใส่ราคา 155 บาท (< SDM 157)

**Frontend**: `Step6_Summary.jsx`
```javascript
// Frontend ตรวจสอบว่าราคา < SDM
if (requestedPrice < priceSDM) {
  approval_level = 'PM_APPROVAL';  // ✅ ต้องผ่าน PM
}
```

**Backend**: `special_price_request_router.py` - `create_special_price_request()`
```python
# 1. คำนวณว่าราคา < SDM หรือไม่
requested_total = calculate_request_total(items)
below_sdm = is_price_below_sdm(requested_total)  # True

# 2. หา PM ตาม category
if below_sdm:
    product_categories = extract_product_categories(items)  # {'A'}
    pms = await find_all_pms_by_categories(['A'])
    # PM: ผู้จัดการผลิตภัณฑ์อลูมิเนียม

# 3. บันทึกลง database
status = 'PENDING_ZM'
approver_employee_id = 'ZM_00TR'  # ZM ของสาขา 00TR
```

**Database**:
```sql
special_price_requests:
  id: 1
  quote_no: TRQT-2603/0050
  status: PENDING_ZM
  approver_employee_id: ZM_00TR
  branch: 00TR

special_price_request_items:
  request_id: 1
  item_code: A01010010108100000
  approval_level: PM_APPROVAL  ← สำคัญ!
```

---

### Step 2: ZM (ผู้จัดการสาขา) อนุมัติ

**Who**: ผู้จัดการสาขา 00TR (คุณ)

**Action**: เข้าหน้า "อนุมัติราคาพิเศษ" → เห็นคำขอ → กดอนุมัติ

**Backend**: `approve_request()`
```python
# 1. ตรวจสอบสิทธิ์
current_role = 'ZM'
current_branch = '00TR'
expected_position = 'ZM_00TR'
if approver_employee_id == expected_position:  # ✅ ตรงกัน
    # มีสิทธิ์อนุมัติ

# 2. ตรวจสอบว่าต้องส่งต่อหรือไม่
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)  # True

# 3. ส่งต่อ RM
if needs_pm:
    new_status = 'PENDING_RM'
    region = get_region_from_branch('00TR')  # 'BE'
    new_approver_id = 'RM_BE'
```

**Database After**:
```sql
status: PENDING_RM
approver_employee_id: RM_BE
approved_by: 21748  ← รหัสพนักงาน ZM
```

---

### Step 3: RM (ผู้จัดการภูมิภาค) อนุมัติ

**Who**: RM ภูมิภาค Bangkok East

**Action**: เข้าหน้า "อนุมัติราคาพิเศษ" → เห็นคำขอ → กดอนุมัติ

**Backend**: `approve_request()`
```python
# 1. ตรวจสอบสิทธิ์
current_role = 'RM'
current_region = 'BE'
request_region = 'BE'  # จาก approver_employee_id = 'RM_BE'
if current_region == request_region:  # ✅ ตรงกัน
    # มีสิทธิ์อนุมัติ

# 2. ตรวจสอบว่าต้องส่งต่อหรือไม่
needs_pm = True  # จาก approval_level = 'PM_APPROVAL'

# 3. ส่งต่อ SDM (SDM จะเป็นคนส่งต่อให้ PM)
if needs_pm:
    new_status = 'PENDING_SDM'
    new_approver_id = 'SDM_GLOBAL'
```

**Database After**:
```sql
status: PENDING_SDM
approver_employee_id: SDM_GLOBAL
approved_by: 21750  ← รหัสพนักงาน RM
```

---

### Step 4: SDM (ผู้จัดการฝ่ายขาย) อนุมัติ

**Who**: SDM ที่ HQ

**Action**: เข้าหน้า "อนุมัติราคาพิเศษ" → เห็นคำขอ → กดอนุมัติ

**Backend**: `approve_request()`
```python
# 1. ตรวจสอบสิทธิ์
current_role = 'SDM'
if current_status == 'PENDING_SDM':  # ✅ ถูกต้อง
    # มีสิทธิ์อนุมัติ

# 2. ตรวจสอบว่าต้องส่งต่อ PM หรือไม่
needs_pm = True  # จาก approval_level = 'PM_APPROVAL'

# 3. ส่งต่อ PM (ดึง category จาก items)
if needs_pm:
    cursor.execute("""
        SELECT DISTINCT LEFT(item_code, 1) as category
        FROM special_price_request_items
        WHERE request_id = ? AND approval_level = 'PM_APPROVAL'
    """)
    pm_category = 'A'  # อลูมิเนียม
    
    new_status = 'PENDING_PM'
    new_approver_id = 'PM_A'
```

**Database After**:
```sql
status: PENDING_PM
approver_employee_id: PM_A
approved_by: 21755  ← รหัสพนักงาน SDM
```

---

### Step 5: PM (ผู้จัดการผลิตภัณฑ์) อนุมัติ

**Who**: PM อลูมิเนียม

**Action**: เข้าหน้า "อนุมัติราคาพิเศษ" → เห็นคำขอ → กดอนุมัติ

**Backend**: `approve_request()`
```python
# 1. ตรวจสอบสิทธิ์
current_role = 'PM'
if current_status == 'PENDING_PM':  # ✅ ถูกต้อง
    # มีสิทธิ์อนุมัติ

# 2. PM อนุมัติเป็นขั้นสุดท้าย
new_status = 'APPROVED'
new_approver_id = None
```

**Database After**:
```sql
status: APPROVED
approver_employee_id: NULL
approved_by: 21800  ← รหัสพนักงาน PM
```

---

## Key Points

### 1. Approval Level Detection

**Frontend** (`Step6_Summary.jsx`):
```javascript
// ตรวจสอบราคาเทียบกับ threshold
if (requestedPrice < priceSDM) {
  approval_level = 'PM_APPROVAL';  // ต้องผ่าน PM
} else if (requestedPrice < priceW1) {
  approval_level = 'SDM_APPROVAL';  // ต้องผ่าน SDM
} else if (requestedPrice < priceW2) {
  approval_level = 'ZM_THEN_RM';  // ต้องผ่าน RM
} else {
  approval_level = 'ZM_ONLY';  // ZM อนุมัติเลย
}
```

### 2. Routing Logic

**Backend** (`special_price_request_router.py`):
```python
# คำนวณ routing needs จาก approval_level
needs_rm = any(level in ['ZM_THEN_RM', 'RM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM', 'PM_APPROVAL'] for level in approval_levels)
needs_sdm = any(level in ['SDM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM'] for level in approval_levels)
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)

# ZM routing
if needs_rm or needs_sdm or needs_pm:
    new_status = 'PENDING_RM'  # ส่งต่อ RM

# RM routing
if needs_pm or needs_sdm:
    new_status = 'PENDING_SDM'  # ส่งต่อ SDM

# SDM routing
if needs_pm:
    new_status = 'PENDING_PM'  # ส่งต่อ PM
    new_approver_id = f'PM_{category}'
```

### 3. PM Category Mapping

```python
category_map = {
    'G': 'ผู้จัดการผลิตภัณฑ์กระจก',
    'A': 'ผู้จัดการผลิตภัณฑ์อลูมิเนียม',  ← สำหรับ A01010010108100000
    'C': 'ผู้จัดการผลิตภัณฑ์โครงคร่าวฝ้าเพดานโครงผนัง',
    'Y': 'ผู้จัดการผลิตภัณฑ์ยิปซัม',
    'S': 'ผู้จัดการผลิตภัณฑ์ซีลแลนท์',
    'E': 'ผู้จัดการผลิตภัณฑ์อุปกรณ์และอื่นๆ'
}
```

---

## Testing Checklist

### As ZM (ผู้จัดการสาขา):

1. ✅ เข้าหน้า "อนุมัติราคาพิเศษ"
2. ✅ เห็นคำขอที่ status = PENDING_ZM และ approver = ZM_00TR
3. ✅ กดอนุมัติ
4. ✅ ระบบส่งต่อไป RM (status = PENDING_RM)
5. ✅ คำขอหายจากหน้าของ ZM

### Expected Flow:

```
ZM อนุมัติ (คุณ)
  ↓
RM อนุมัติ (ผู้จัดการภูมิภาค BE)
  ↓
SDM อนุมัติ (ผู้จัดการฝ่ายขาย)
  ↓
PM อนุมัติ (ผู้จัดการผลิตภัณฑ์อลูมิเนียม)
  ↓
✅ APPROVED
```

---

## Summary

**ใช่ครับ! ถูกต้องแล้ว**

เมื่อคุณ (ZM/ผู้จัดการสาขา) อนุมัติคำขอที่ราคา 155 < SDM 157:
1. ✅ ระบบจะส่งต่อไป RM
2. ✅ RM จะส่งต่อไป SDM
3. ✅ SDM จะส่งต่อไป PM (อลูมิเนียม)
4. ✅ PM อนุมัติเป็นขั้นสุดท้าย

**Flow สมบูรณ์**: Sales → ZM → RM → SDM → PM → Approved

---

**Status**: ✅ Verified
**Your Role**: ZM (ผู้จัดการสาขา 00TR)
**Action**: อนุมัติคำขอ → ระบบจะส่งต่อไป RM โดยอัตโนมัติ
