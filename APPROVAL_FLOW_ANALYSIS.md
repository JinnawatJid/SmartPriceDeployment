# Special Price Request - Approval Flow Analysis

## How Status and Approver Work

### Initial Creation

**When creating a special price request:**

```python
# 1. หาผู้อนุมัติจาก API
zm = await find_zm_at_branch(branch_code)  # เช่น ZM ของสาขา 03TS
rm = await find_rm_in_region(region)       # เช่น RM ของภูมิภาค BE
sdm = await find_sdm()                     # SDM ที่ HQ

# 2. กำหนด status และ approver_employee_id เริ่มต้น
initial_status = 'PENDING_ZM'              # เริ่มที่ ZM เสมอ
approver_id = f"ZM_{branch_code}"          # เช่น "ZM_03TS"

# 3. บันทึกลง database
INSERT INTO special_price_requests (
    status,                  # 'PENDING_ZM'
    approver_employee_id,    # 'ZM_03TS'
    ...
)
```

### Key Points

1. **ไม่ได้บันทึกรหัสพนักงานจริง** แต่บันทึก **Position ID**
   - `ZM_03TS` = ZM ของสาขา 03TS
   - `RM_BE` = RM ของภูมิภาค BE
   - `SDM_GLOBAL` = SDM

2. **หา employee_id จริงตอนอนุมัติ**
   - เมื่อ ZM login และเข้ามาอนุมัติ
   - ระบบเช็คว่า ZM นี้เป็น ZM ของสาขาที่ถูกต้องหรือไม่
   - โดยเทียบ `current_branch` กับ `approver_employee_id`

3. **Status Flow**
   ```
   PENDING_ZM → PENDING_RM → PENDING_SDM → APPROVED
   ```

---

## Approval Flow by Level

### Level 1: ZM_ONLY (R1 > price >= W2)

**Create:**
```python
status = 'PENDING_ZM'
approver_employee_id = 'ZM_03TS'
```

**ZM Approves:**
```python
# Check: current_role == 'ZM' and current_branch == '03TS'
new_status = 'APPROVED'
new_approver_id = None
approved_by = current_employee_id  # รหัสพนักงาน ZM จริง
```

---

### Level 2: ZM_THEN_RM (W2 > price >= W1)

**Create:**
```python
status = 'PENDING_ZM'
approver_employee_id = 'ZM_03TS'
```

**ZM Approves:**
```python
# Check: needs_rm = True
new_status = 'PENDING_RM'
new_approver_id = 'RM_BE'  # ภูมิภาคของสาขา
```

**RM Approves:**
```python
# Check: current_role == 'RM' and current_region == 'BE'
new_status = 'APPROVED'
new_approver_id = None
approved_by = current_employee_id  # รหัสพนักงาน RM จริง
```

---

### Level 3: SDM_APPROVAL (W1 > price >= SDM)

**Create:**
```python
status = 'PENDING_ZM'
approver_employee_id = 'ZM_03TS'
```

**ZM Approves:**
```python
# Check: needs_sdm = True
new_status = 'PENDING_RM'
new_approver_id = 'RM_BE'
```

**RM Approves:**
```python
# Check: needs_sdm = True
new_status = 'PENDING_SDM'
new_approver_id = 'SDM_GLOBAL'
```

**SDM Approves:**
```python
# Check: current_role == 'SDM'
new_status = 'APPROVED'
new_approver_id = None
approved_by = current_employee_id  # รหัสพนักงาน SDM จริง
```

---

### Level 4: PM_APPROVAL (price < SDM) - NEW ✅

**Create:**
```python
# 1. หา PM ตามหมวดหมู่สินค้า
product_categories = extract_product_categories(items)  # เช่น {'A'}
pms = await find_all_pms_by_categories(product_categories)
pm_approver = pms['A']  # PM Aluminium

# 2. กำหนด status และ approver
status = 'PENDING_ZM'
approver_employee_id = 'ZM_03TS'

# 3. บันทึก PM info (หลังจากเพิ่มคอลัมน์)
pm_approver_id = pm_approver['employee_id']  # รหัสพนักงาน PM จริง
pm_approver_name = pm_approver['name']
pm_category = 'A'
is_below_sdm = 1
```

**ZM Approves:**
```python
# Check: needs_pm = True (ถ้าราคา < SDM)
new_status = 'PENDING_RM'
new_approver_id = 'RM_BE'
```

**RM Approves:**
```python
# Check: needs_pm = True
new_status = 'PENDING_PM'
new_approver_id = f'PM_{pm_category}'  # เช่น 'PM_A'
```

**PM Approves:**
```python
# Check: current_role == 'PM' and pm_category matches
new_status = 'APPROVED'
new_approver_id = None
approved_by = current_employee_id  # รหัสพนักงาน PM จริง
```

---

## Database Columns

### special_price_requests

| Column | Type | Description | Example |
|---|---|---|---|
| status | VARCHAR | สถานะปัจจุบัน | 'PENDING_ZM', 'PENDING_RM', 'PENDING_SDM', 'PENDING_PM', 'APPROVED' |
| approver_employee_id | VARCHAR | Position ID ของผู้อนุมัติถัดไป | 'ZM_03TS', 'RM_BE', 'SDM_GLOBAL', 'PM_A' |
| approved_by | VARCHAR | รหัสพนักงานจริงที่อนุมัติ (ตอนอนุมัติ) | '21748', '21750' |
| pm_approver_id | VARCHAR | รหัสพนักงาน PM (ถ้าราคา < SDM) | '21800' |
| pm_approver_name | VARCHAR | ชื่อ PM | 'ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม' |
| pm_category | VARCHAR | หมวดหมู่สินค้า | 'A', 'G', 'C', 'Y', 'S', 'E' |
| is_below_sdm | BIT | Flag ว่าราคา < SDM | 0, 1 |

---

## Position ID Format

### ZM (Zone Manager)
```
Format: ZM_{branch_code}
Examples:
- ZM_03TS (ZM ของสาขา 03TS)
- ZM_00TR (ZM ของสาขา 00TR)
```

### RM (Regional Manager)
```
Format: RM_{region_code}
Examples:
- RM_BE (RM ของภูมิภาค Bangkok East)
- RM_N (RM ของภูมิภาค North)
- RM_S (RM ของภูมิภาค South)
```

### SDM (Sales Director Manager)
```
Format: SDM_GLOBAL
Example:
- SDM_GLOBAL (SDM ที่ HQ)
```

### PM (Product Manager) - NEW ✅
```
Format: PM_{category}
Examples:
- PM_A (PM Aluminium)
- PM_G (PM Glass)
- PM_C (PM CLine)
- PM_Y (PM Yipsum)
- PM_S (PM Sealant)
- PM_E (PM Equipment)
```

---

## Approval Logic

### Check Permission
```python
# 1. ดึงข้อมูลคำขอ
request = get_request(request_id)
current_status = request['status']
approver_employee_id = request['approver_employee_id']

# 2. ดึงข้อมูลผู้อนุมัติจาก token
current_role = employee_info['role']
current_branch = employee_info['branch_code']
current_region = employee_info['region']

# 3. เช็คสิทธิ์
if current_role == 'ZM':
    expected_position = f"ZM_{current_branch}"
    if approver_employee_id != expected_position:
        raise HTTPException(403, "Not assigned approver")

elif current_role == 'RM':
    request_region = approver_employee_id.split('_')[1]  # RM_BE → BE
    if current_region != request_region:
        raise HTTPException(403, "Wrong region")

elif current_role == 'PM':
    request_category = approver_employee_id.split('_')[1]  # PM_A → A
    pm_category = employee_info['category']  # จาก token หรือ lookup
    if request_category != pm_category:
        raise HTTPException(403, "Wrong category")
```

### Determine Next Approver
```python
# ดูจาก approval_level ของ items
approval_levels = get_item_approval_levels(request_id)

needs_rm = any(level in ['ZM_THEN_RM', 'SDM_APPROVAL', 'PM_APPROVAL'] for level in approval_levels)
needs_sdm = any(level == 'SDM_APPROVAL' for level in approval_levels)
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)

if current_status == 'PENDING_ZM':
    if needs_rm or needs_sdm or needs_pm:
        new_status = 'PENDING_RM'
        new_approver_id = f"RM_{region}"
    else:
        new_status = 'APPROVED'

elif current_status == 'PENDING_RM':
    if needs_pm:
        new_status = 'PENDING_PM'
        new_approver_id = f"PM_{pm_category}"
    elif needs_sdm:
        new_status = 'PENDING_SDM'
        new_approver_id = 'SDM_GLOBAL'
    else:
        new_status = 'APPROVED'

elif current_status == 'PENDING_PM':
    new_status = 'APPROVED'

elif current_status == 'PENDING_SDM':
    new_status = 'APPROVED'
```

---

## Summary

### Key Differences for PM Routing

1. **PM info saved at creation** (not at approval time)
   - `pm_approver_id` = รหัสพนักงาน PM จริง (จาก API)
   - `pm_category` = หมวดหมู่สินค้า

2. **Position ID for routing**
   - `approver_employee_id` = 'PM_A' (for routing)
   - `pm_approver_id` = '21800' (actual employee ID)

3. **Approval flow**
   - Sales → ZM → RM → PM (by category) → Approved

4. **Permission check**
   - Check PM's category matches request category
   - Use `pm_category` from database

---

**Status**: Analysis Complete
**Next**: Implement PM approval logic in approve_request()
