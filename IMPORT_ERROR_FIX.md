# Import Error Fix - SDM_THRESHOLD_PRICE

## Problem
```
ImportError: cannot import name 'SDM_THRESHOLD_PRICE' from 'config.config_external_api'
```

## Root Cause
- `SDM_THRESHOLD_PRICE` ยังไม่ได้ถูกเพิ่มใน `config_external_api.py`
- `special_price_request_router.py` พยายาม import ค่าที่ไม่มีอยู่

## Solution

### 1. Added SDM_THRESHOLD_PRICE to config_external_api.py ✅

**File**: `backend/config/config_external_api.py`

```python
# =========================
# Special Price Request Configuration
# =========================
SDM_THRESHOLD_PRICE = float(os.getenv("SDM_THRESHOLD_PRICE", "50000"))
# ราคาขั้นต่ำที่ต้องส่งให้ SDM อนุมัติ
# ถ้าราคา < SDM_THRESHOLD_PRICE จะส่งให้ PM แทน
```

### 2. Updated Import in special_price_request_router.py ✅

**File**: `backend/special_price_request_router.py`

**Before:**
```python
from config.config_external_api import SDM_THRESHOLD_PRICE
```

**After:**
```python
# Removed direct import, using os.getenv() in helper function instead
```

### 3. Helper Function Uses os.getenv() ✅

**File**: `backend/special_price_request_router.py`

```python
def is_price_below_sdm(requested_total: float) -> bool:
    """Check if requested total is below SDM threshold"""
    sdm_threshold = float(os.getenv("SDM_THRESHOLD_PRICE", "50000"))
    return requested_total < sdm_threshold
```

---

## Configuration

### Environment Variable
```
SDM_THRESHOLD_PRICE=50000  # Default 50,000 THB
```

Add to `.env` file:
```
SDM_THRESHOLD_PRICE=50000
```

---

## Files Updated

1. ✅ `backend/config/config_external_api.py`
   - Added SDM_THRESHOLD_PRICE configuration

2. ✅ `backend/special_price_request_router.py`
   - Removed direct import of SDM_THRESHOLD_PRICE
   - Uses os.getenv() in helper function

---

## Testing

After fix, the application should start without import errors:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

## How It Works

1. **Configuration**: `SDM_THRESHOLD_PRICE` is defined in `config_external_api.py`
2. **Runtime**: Helper function `is_price_below_sdm()` reads from environment
3. **Default**: If not set in environment, defaults to 50,000 THB
4. **Usage**: Called in `create_special_price_request()` to determine routing

---

**Status**: ✅ Fixed
**Last Updated**: March 22, 2026
