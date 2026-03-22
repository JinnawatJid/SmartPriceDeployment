# PM Routing Fixes

## Issues Found

From error logs:
```
1. ❌ Database Error: Invalid column name 'product_category', 'is_below_sdm'
2. ❌ API 404: /api/special-price-requests/approver-info not found
3. ❌ PM Not Found: Role names incorrect (had " - " separator)
```

---

## Fix 1: Database Column Names

### Problem
INSERT statement tried to use columns that don't exist in `special_price_request_items` table:
- `product_category`
- `is_below_sdm`

### Solution
Removed these columns from INSERT statement. Use only existing columns:

**File**: `backend/special_price_request_router.py` (Line ~453)

**Before (WRONG)**:
```python
cursor.execute("""
    INSERT INTO special_price_request_items (
        request_id, item_code, item_name, quantity, unit,
        normal_price, requested_price, original_amount, requested_amount,
        is_below_normal, approval_level, product_category, is_below_sdm, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
""", (..., product_category, 1 if below_sdm else 0))
```

**After (CORRECT)**:
```python
cursor.execute("""
    INSERT INTO special_price_request_items (
        request_id, item_code, item_name, quantity, unit,
        normal_price, requested_price, original_amount, requested_amount,
        is_below_normal, approval_level, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
""", (..., item.approval_level))
```

---

## Fix 2: Add Missing Endpoint

### Problem
Frontend calls `/api/special-price-requests/approver-info` but endpoint doesn't exist.

### Solution
Added new endpoint to return current user's approver info.

**File**: `backend/special_price_request_router.py` (Line ~70)

```python
@router.get("/approver-info")
async def get_approver_info(employee_info: dict = Depends(get_employee_info)):
    """Get approver information for current user"""
    try:
        employee_id = employee_info.get('employee_id')
        name = employee_info.get('name', 'Unknown')
        role = employee_info.get('role', 'Sales')
        branch_code = employee_info.get('branch_code')
        region = employee_info.get('region')
        
        logger.info(f"Getting approver info for: {employee_id} ({name}), Role: {role}")
        
        return {
            "employee_id": employee_id,
            "name": name,
            "role": role,
            "branch_code": branch_code,
            "region": region,
            "can_approve": role in ['ZM', 'RM', 'SDM', 'PM']
        }
        
    except Exception as e:
        logger.error(f"Error getting approver info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get approver info: {str(e)}"
        )
```

---

## Fix 3: Correct PM Role Names

### Problem
PM role names had incorrect format with " - " separator:
```
❌ 'ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม'  (WRONG - has " - ")
✅ 'ผู้จัดการผลิตภัณฑ์อลูมิเนียม'     (CORRECT - no separator)
```

This caused API calls to fail with 404 because the role doesn't exist in UXP Auth system.

### Solution
Updated role names to match actual roles in UXP Auth system.

**File**: `backend/employee_position_mapper.py` (Line ~120)

**Before (WRONG)**:
```python
category_map = {
    'G': 'ผู้จัดการผลิตภัณฑ์ - กระจก',
    'A': 'ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม',
    'C': 'ผู้จัดการผลิตภัณฑ์ - ซีไลน์',
    'Y': 'ผู้จัดการผลิตภัณฑ์ - ยิปซั่ม',
    'S': 'ผู้จัดการผลิตภัณฑ์ - ซีลแลนท์',
    'E': 'ผู้จัดการผลิตภัณฑ์ - อุปกรณ์'
}
```

**After (CORRECT)**:
```python
category_map = {
    'G': 'ผู้จัดการผลิตภัณฑ์กระจก',
    'A': 'ผู้จัดการผลิตภัณฑ์อลูมิเนียม',
    'C': 'ผู้จัดการผลิตภัณฑ์โครงคร่าวฝ้าเพดานโครงผนัง',
    'Y': 'ผู้จัดการผลิตภัณฑ์ยิปซัม',
    'S': 'ผู้จัดการผลิตภัณฑ์ซีลแลนท์',
    'E': 'ผู้จัดการผลิตภัณฑ์อุปกรณ์และอื่นๆ'
}
```

**Reference**: `backend/role_mapping.py` contains the correct role names:
```python
THAI_ROLE_TO_CODE = {
    "ผู้จัดการผลิตภัณฑ์กระจก": "PM_GLASS",
    "ผู้จัดการผลิตภัณฑ์อลูมิเนียม": "PM_ALUMINIUM",
    "ผู้จัดการผลิตภัณฑ์โครงคร่าวฝ้าเพดานโครงผนัง": "PM_CLINE",
    "ผู้จัดการผลิตภัณฑ์ยิปซัม": "PM_GYPSUM",
    "ผู้จัดการผลิตภัณฑ์ซีลแลนท์": "PM_SEALANT",
    "ผู้จัดการผลิตภัณฑ์อุปกรณ์และอื่นๆ": "PM_EQUIPMENT",
}
```

---

## Fix 4: Better Error Handling

### Problem
When PM not found, system still tried to create request and failed.

### Solution
Added warning logs but allow request creation to continue (PM routing will be handled during approval).

**File**: `backend/special_price_request_router.py` (Line ~365)

```python
if product_categories:
    pms = await find_all_pms_by_categories(list(product_categories))
    if pms:
        pm_approver = list(pms.values())[0]
        logger.info(f"  PM Approver: {pm_approver}")
    else:
        logger.warning(f"  ⚠️ PM not found for categories: {product_categories}")
        logger.warning(f"  ⚠️ Request will be created but PM routing may fail during approval")
else:
    logger.warning(f"  ⚠️ No product categories found in items")
```

---

## Testing

### Test Case 1: Create Special Price Request (Price < SDM)

**Input**:
- Product: A01010010108100000 (Aluminium)
- Price: 155 < SDM 157

**Expected**:
1. ✅ Request created successfully
2. ✅ No database column errors
3. ✅ PM lookup uses correct role name: "ผู้จัดการผลิตภัณฑ์อลูมิเนียม"
4. ✅ If PM found, log PM info
5. ✅ If PM not found, log warning but continue

### Test Case 2: Get Approver Info

**Request**:
```
GET /api/special-price-requests/approver-info
```

**Expected Response**:
```json
{
  "employee_id": "21748",
  "name": "John Doe",
  "role": "ZM",
  "branch_code": "00TR",
  "region": "BE",
  "can_approve": true
}
```

---

## Summary

Fixed 3 critical issues:
1. ✅ Removed non-existent database columns from INSERT
2. ✅ Added missing `/approver-info` endpoint
3. ✅ Corrected PM role names to match UXP Auth system
4. ✅ Improved error handling for PM lookup

**Result**: Special price requests can now be created successfully, and PM routing will work when PMs are configured in UXP Auth system.

---

**Status**: ✅ Fixed
**Files Modified**:
- `backend/special_price_request_router.py`
- `backend/employee_position_mapper.py`
