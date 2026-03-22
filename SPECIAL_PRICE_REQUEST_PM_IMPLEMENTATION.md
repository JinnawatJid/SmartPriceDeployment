# Special Price Request - PM Routing Implementation

## Summary
เพิ่มลอจิกการส่งคำขอราคาพิเศษให้ PM แต่ละคนตามหมวดหมู่สินค้า เมื่อราคา < SDM threshold

## Changes Made

### 1. Backend - employee_position_mapper.py ✅

#### New Functions Added:

**find_pm_by_category(category: str)**
- ค้นหา Product Manager ตามหมวดหมู่สินค้า
- รองรับ 6 หมวดหมู่: G, A, C, Y, S, E
- ส่งคืน PM employee info หรือ None

**find_all_pms_by_categories(categories: list)**
- ค้นหา PM สำหรับหลายหมวดหมู่พร้อมกัน
- ส่งคืน Dictionary mapping category → PM info

#### PM Role Names (Auth API)
```
PM_Glass: ผู้จัดการผลิตภัณฑ์ - กระจก
PM_Aluminium: ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม
PM_CLine: ผู้จัดการผลิตภัณฑ์ - ซีไลน์
PM_Yipsum: ผู้จัดการผลิตภัณฑ์ - ยิปซั่ม
PM_Sealant: ผู้จัดการผลิตภัณฑ์ - ซีลแลนท์
PM_Equipment: ผู้จัดการผลิตภัณฑ์ - อุปกรณ์
```

---

### 2. Backend - special_price_request_router.py ✅

#### New Imports
```python
from employee_position_mapper import (
    find_pm_by_category, find_all_pms_by_categories
)
from config.config_external_api import SDM_THRESHOLD_PRICE
import os
```

#### New Helper Functions

**extract_product_categories(items: List[SpecialPriceItem]) → set**
- ดึงหมวดหมู่สินค้าจากรายการ (ตัวอักษรแรกของ SKU)
- ส่งคืน set ของหมวดหมู่ที่ถูกต้อง

**calculate_request_total(items: List[SpecialPriceItem]) → float**
- คำนวณยอดรวมของคำขอ

**is_price_below_sdm(requested_total: float) → bool**
- ตรวจสอบว่าราคา < SDM threshold
- ใช้ค่า SDM_THRESHOLD_PRICE จาก environment

#### Updated create_special_price_request()

**Logic Flow:**
1. คำนวณยอดรวมและตรวจสอบว่า < SDM
2. ถ้า < SDM:
   - ดึงหมวดหมู่สินค้า
   - ค้นหา PM สำหรับแต่ละหมวดหมู่
   - ใช้ PM ตัวแรกเป็น approver
3. ถ้า >= SDM:
   - ใช้ SDM เป็น approver (เดิม)

**New Database Columns:**
- `pm_approver_id`: ID ของ PM
- `pm_approver_name`: ชื่อของ PM
- `pm_category`: หมวดหมู่สินค้า
- `is_below_sdm`: Flag ว่าราคา < SDM หรือไม่

**New Item Columns:**
- `product_category`: หมวดหมู่สินค้า
- `is_below_sdm`: Flag ว่าราคา < SDM หรือไม่

---

## Database Schema Updates Required

### Table: special_price_requests

```sql
ALTER TABLE special_price_requests ADD (
    pm_approver_id VARCHAR(50) NULL,
    pm_approver_name VARCHAR(255) NULL,
    pm_category VARCHAR(10) NULL,
    is_below_sdm BIT DEFAULT 0
);
```

### Table: special_price_request_items

```sql
ALTER TABLE special_price_request_items ADD (
    product_category VARCHAR(10) NULL,
    is_below_sdm BIT DEFAULT 0
);
```

---

## Configuration

### Environment Variable
```
SDM_THRESHOLD_PRICE=50000  # Default 50,000 THB
```

### Add to config_external_api.py
```python
SDM_THRESHOLD_PRICE = float(os.getenv("SDM_THRESHOLD_PRICE", "50000"))
```

---

## Product Categories

| Category | SKU Prefix | Description |
|---|---|---|
| G | G* | Glass (กระจก) |
| A | A* | Aluminium (อลูมิเนียม) |
| C | C* | CLine (ซีไลน์) |
| Y | Y* | Yipsum (ยิปซั่ม) |
| S | S* | Sealant (ซีลแลนท์) |
| E | E* | Equipment (อุปกรณ์) |

---

## Approval Flow

### Scenario 1: Price >= SDM Threshold
```
Sales → ZM → RM → SDM → Approved
```

### Scenario 2: Price < SDM Threshold
```
Sales → ZM → RM → PM (by Category) → Approved
```

---

## Example Usage

### Request with Price < SDM
```json
{
  "quote_no": "QT-001",
  "customer_code": "CUST001",
  "customer_name": "บริษัท ABC",
  "items": [
    {
      "sku": "G001",
      "item_name": "กระจกใส",
      "quantity": 100,
      "unit": "แผ่น",
      "normal_price": 500,
      "requested_price": 400,
      "approval_level": "PM"
    }
  ],
  "request_reason": "ลูกค้าใหญ่",
  "valid_from": "2026-03-22",
  "valid_to": "2026-04-22"
}
```

**Result:**
- `requested_total` = 40,000 (< 50,000)
- `is_below_sdm` = true
- `pm_category` = "G"
- `pm_approver_name` = "ผู้จัดการผลิตภัณฑ์ - กระจก"
- `status` = "PENDING_ZM" (เริ่มต้น)

---

## Files Updated

1. ✅ `backend/employee_position_mapper.py`
   - Added `find_pm_by_category()`
   - Added `find_all_pms_by_categories()`

2. ✅ `backend/special_price_request_router.py`
   - Updated imports
   - Added helper functions
   - Updated `create_special_price_request()`
   - Added PM routing logic
   - Updated INSERT statements

---

## Testing Checklist

- [ ] Create special price request with price < SDM
- [ ] Verify PM is assigned based on product category
- [ ] Verify approval flow goes to PM
- [ ] Test with multiple categories
- [ ] Verify PM can approve/reject
- [ ] Test with price >= SDM (should go to SDM)
- [ ] Verify database columns are populated correctly
- [ ] Check logs for PM assignment

---

## Next Steps

1. **Database Migration**
   - Run ALTER TABLE statements
   - Verify columns are created

2. **Environment Configuration**
   - Set SDM_THRESHOLD_PRICE in .env

3. **Auth API Configuration**
   - Verify PM role names exist in Auth API
   - Test PM lookup

4. **Frontend Updates**
   - Update SpecialPriceApproval.jsx to show PM
   - Update Step6_Summary.jsx to show PM warning

5. **Testing**
   - Create test requests with different categories
   - Verify approval flow
   - Test PM approval/rejection

---

**Status**: Backend implementation complete ✅
**Frontend**: Pending
**Database**: Pending
**Testing**: Pending

**Last Updated**: March 22, 2026
