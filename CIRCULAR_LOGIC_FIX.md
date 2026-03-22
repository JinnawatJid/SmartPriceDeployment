# Circular Logic Fix - PM Approval Flow

## Issue Reported
User reported "มีโค้ด circle" (circular logic in code) - TWICE

## Root Cause

### Problem 1: Redundant needs_pm calculation in RM section ✅ FIXED
The `needs_pm` was calculated inside RM approval block instead of at the top with other routing checks.

### Problem 2: Duplicate needs_pm calculation in SDM section ✅ FIXED
The `needs_pm` was calculated AGAIN in the SDM approval block, even though it was already calculated at the top.

**Original Code (WRONG):**
```python
# Line ~615: Calculate once
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)

# Line ~658: Calculate AGAIN (redundant!)
elif current_status == 'PENDING_SDM':
    needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)  # ← ซ้ำ!
```

This created:
1. **Redundant computation** - Same calculation done twice
2. **Code duplication** - Harder to maintain
3. **Potential bugs** - If logic changes, must update in multiple places

---

## The Fix

### All Changes Made

**File**: `backend/special_price_request_router.py`

**Change 1 - Line ~615**: Calculate ALL routing needs ONCE at the top:

```python
# ตรวจสอบว่าต้องส่งต่อหรือไม่
needs_rm = any(level in ['ZM_THEN_RM', 'RM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM', 'PM_APPROVAL'] for level in approval_levels)
needs_sdm = any(level in ['SDM', 'SDM_APPROVAL', 'ZM_THEN_RM_THEN_SDM'] for level in approval_levels)
needs_pm = any(level == 'PM_APPROVAL' for level in approval_levels)  # ✅ Calculate once

logger.info(f"  Needs RM: {needs_rm}")
logger.info(f"  Needs SDM: {needs_sdm}")
logger.info(f"  Needs PM: {needs_pm}")
```

**Change 2 - Line ~625**: ZM approval uses needs_pm:

```python
if current_status in ['PENDING_ZM', 'SDM_APPROVAL']:
    if needs_rm or needs_sdm or needs_pm:  # ✅ Uses needs_pm from top
        new_status = 'PENDING_RM'
```

**Change 3 - Line ~645**: RM approval uses needs_pm:

```python
elif current_status == 'PENDING_RM':
    if needs_pm or needs_sdm:  # ✅ Uses needs_pm from top
        new_status = 'PENDING_SDM'
```

**Change 4 - Line ~658**: SDM approval uses needs_pm (NO recalculation):

```python
elif current_status == 'PENDING_SDM':
    # เช็คว่าต้องส่ง PM หรือไม่ (ใช้ needs_pm ที่คำนวณไว้แล้ว)
    if needs_pm:  # ✅ Uses needs_pm from top (NO recalculation)
        # ส่งต่อ PM
```

---

## Benefits

1. ✅ **No Circular Logic**: All routing needs calculated ONCE at the top
2. ✅ **No Duplication**: Same variables used throughout
3. ✅ **DRY Principle**: Don't Repeat Yourself
4. ✅ **Maintainable**: Change logic in one place only
5. ✅ **Clear Flow**: Easy to understand approval routing

---

## Approval Flow (Verified)

### Price < SDM (PM_APPROVAL)

```
Create Request:
  status = PENDING_ZM
  approver = ZM_03TS
  needs_pm = True (calculated once)
  
ZM Approves:
  Check: needs_pm = True → Route to RM
  status = PENDING_RM
  approver = RM_BE
  
RM Approves:
  Check: needs_pm = True → Route to SDM
  status = PENDING_SDM
  approver = SDM_GLOBAL
  
SDM Approves:
  Check: needs_pm = True → Route to PM
  status = PENDING_PM
  approver = PM_A (by category)
  
PM Approves:
  status = APPROVED
  approver = NULL
```

---

## Code Quality Improvements

### Before (BAD - Circular):
```python
# Top of function
needs_rm = any(...)
needs_sdm = any(...)
# needs_pm NOT calculated here

# RM section
elif current_status == 'PENDING_RM':
    needs_pm = any(...)  # ← Calculate here

# SDM section  
elif current_status == 'PENDING_SDM':
    needs_pm = any(...)  # ← Calculate AGAIN!
```

### After (GOOD - Clean):
```python
# Top of function - Calculate ALL once
needs_rm = any(...)
needs_sdm = any(...)
needs_pm = any(...)  # ✅ Calculate once

# RM section
elif current_status == 'PENDING_RM':
    if needs_pm or needs_sdm:  # ✅ Use from top

# SDM section  
elif current_status == 'PENDING_SDM':
    if needs_pm:  # ✅ Use from top (no recalculation)
```

---

## Summary

Fixed circular/redundant logic by:
1. ✅ Calculating `needs_pm` ONCE at the top (not in RM section)
2. ✅ Removing duplicate `needs_pm` calculation in SDM section
3. ✅ Adding 'PM_APPROVAL' to `needs_rm` check
4. ✅ Using consistent variables throughout the function

**Result**: Clean, maintainable code with no duplication

The approval flow now works correctly:
**Sales → ZM → RM → SDM → PM (by Category) → Approved**

---

**Status**: ✅ Fixed (All circular logic removed)
**Files Modified**: 
- `backend/special_price_request_router.py`
- `PM_ROUTING_VIA_SDM.md`
- `CIRCULAR_LOGIC_FIX.md`

