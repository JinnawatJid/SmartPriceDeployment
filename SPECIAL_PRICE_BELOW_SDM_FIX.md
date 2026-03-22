# Special Price Below SDM - Fix

## Problem
ผู้ใช้ใส่ราคา 155 บาท ซึ่งต่ำกว่า SDM (157 บาท) แต่ระบบไม่เปิดให้กดขอราคาพิเศษได้

## Root Cause
ระบบเดิมถือว่าราคา < SDM เป็น "REJECTED" (ราคาต่ำเกินไป) และไม่อนุญาตให้ขออนุมัติ

## Solution
เปลี่ยนลอจิกให้ราคา < SDM ส่งให้ PM (Product Manager) อนุมัติแทนที่จะ reject

---

## Changes Made

### File: `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

#### 1. Updated Price Check Logic ✅

**Before:**
```javascript
} else {
  // ราคา < SDM = ❌ REJECTED (ราคาต่ำเกินไป)
  console.log(`   ❌ REJECTED: ราคาต่ำกว่า SDM (${requestedPrice.toFixed(2)} < ${sdmPrice.toFixed(2)})`);
  belowR1Items.push({
    ...
    approval_level: 'REJECTED', // ต่ำกว่า SDM
  });
}
```

**After:**
```javascript
} else {
  // ราคา < SDM = ต้องอนุมัติจาก PM (Product Manager) ตามหมวดหมู่สินค้า
  console.log(`   ⚠️⚠️⚠️⚠️ PM_APPROVAL: ต้องอนุมัติจาก PM (${requestedPrice.toFixed(2)} < ${sdmPrice.toFixed(2)})`);
  belowR1Items.push({
    ...
    approval_level: 'PM_APPROVAL', // ต่ำกว่า SDM ต้องให้ PM อนุมัติ
  });
}
```

#### 2. Updated Summary Logging ✅

**Before:**
```javascript
const rejected = belowR1Items.filter(i => i.approval_level === 'REJECTED').length;
console.log(`   ❌ REJECTED: ${rejected} รายการ`);
```

**After:**
```javascript
const pmApproval = belowR1Items.filter(i => i.approval_level === 'PM_APPROVAL').length;
console.log(`   ⚠️⚠️⚠️⚠️ PM_APPROVAL: ${pmApproval} รายการ (ราคา < SDM)`);
```

#### 3. Updated Approvable Items Filter ✅

**Before:**
```javascript
const approvableItems = itemsBelowR1.filter(item => item.approval_level !== 'REJECTED');
const rejectedItems = itemsBelowR1.filter(item => item.approval_level === 'REJECTED');
```

**After:**
```javascript
const approvableItems = itemsBelowR1;
const rejectedItems = []; // ไม่มีรายการที่ reject แล้ว เพราะราคา < SDM จะส่งให้ PM
```

---

## Approval Levels

### Updated Approval Flow

| Price Range | Approval Level | Approvers | Description |
|---|---|---|---|
| >= R1 | ✅ OK | None | ราคาปกติ ไม่ต้องขออนุมัติ |
| R1 > price >= W2 | ZM_ONLY | ZM | ส่วนลดน้อย |
| W2 > price >= W1 | ZM_THEN_RM | ZM → RM | ส่วนลดปานกลาง |
| W1 > price >= SDM | SDM_APPROVAL | ZM → RM → SDM | ส่วนลดมาก |
| price < SDM | PM_APPROVAL | ZM → RM → PM (by Category) | ส่วนลดมากที่สุด ✅ NEW |

---

## Example

### Product: A01010010108100000
- R2: 171 บาท
- R1: 166 บาท
- W2: 162 บาท
- W1: 159 บาท
- SDM: 157 บาท

### Requested Price: 155 บาท

**Before:**
- approval_level: "REJECTED"
- Status: ❌ ไม่สามารถขออนุมัติได้
- Button: Disabled

**After:**
- approval_level: "PM_APPROVAL"
- Status: ⚠️⚠️⚠️⚠️ ต้องอนุมัติจาก PM
- Button: Enabled ✅
- Flow: Sales → ZM → RM → PM (Aluminium)

---

## Testing

### Test Case 1: Price < SDM
```
Product: A01010010108100000
SDM: 157
Requested: 155
Expected: approval_level = "PM_APPROVAL", button enabled
```

### Test Case 2: Price = SDM
```
Product: A01010010108100000
SDM: 157
Requested: 157
Expected: approval_level = "SDM_APPROVAL", button enabled
```

### Test Case 3: Price > SDM
```
Product: A01010010108100000
SDM: 157
Requested: 158
Expected: approval_level = "SDM_APPROVAL", button enabled
```

---

## Backend Integration

The backend already supports PM routing (implemented in previous changes):
- `backend/special_price_request_router.py` - PM routing logic
- `backend/employee_position_mapper.py` - PM lookup by category
- Database columns: `pm_approver_id`, `pm_approver_name`, `pm_category`

---

## User Experience

### Before
1. User enters price 155 (< SDM 157)
2. System shows: "ไม่สามารถขออนุมัติได้ (1 รายการนอกช่วง)"
3. Button disabled ❌

### After
1. User enters price 155 (< SDM 157)
2. System shows: "ขอราคาพิเศษ"
3. Button enabled ✅
4. Request routed to PM (Aluminium category)

---

**Status**: ✅ Fixed
**Last Updated**: March 22, 2026
**Impact**: Users can now request special prices below SDM threshold
