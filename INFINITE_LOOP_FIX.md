# Infinite Loop Fix - Pricing API Calls

## Issue Reported
User reported "มีโค้ดวนซ้ำ" (code running in circles/infinite loop)

From the logs, we saw:
```
POST /api/pricing/calculate - Called TWICE
GET /api/quotation?status=complete - Called MULTIPLE TIMES
```

## Root Cause

### Problem: useEffect Dependency Hell

**File**: `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

There were **2 useEffect hooks** calling `/api/pricing/calculate`:

#### 1. Main Pricing useEffect (Line ~343)
```javascript
useEffect(() => {
  // ... pricing logic ...
  const res = await api.post("/api/pricing/calculate", { ... });
  
  // ⚠️ This dispatch changes state.cart
  dispatch({ type: "APPLY_PRICING_RESULT", payload: { key, priced: pi } });
  
}, [state.status, state.cart, state.customer, state.deliveryType, state.shippingCustomerPay]);
//                  ^^^^^^^^^^^ ← PROBLEM!
```

#### 2. Project Pricing useEffect (Line ~750)
```javascript
useEffect(() => {
  // ... project pricing logic ...
  const calcRes = await api.post("/api/pricing/calculate", { ... });
  
}, [selectedProject, state.customer, state.cart, state.deliveryType, state.shippingCustomerPay]);
//                                    ^^^^^^^^^^^ ← PROBLEM!
```

### The Infinite Loop

```
1. User adds item to cart
   → state.cart changes
   
2. Main useEffect triggers (because state.cart changed)
   → Calls /api/pricing/calculate
   → Receives response
   → dispatch({ type: "APPLY_PRICING_RESULT" })
   → state.cart changes AGAIN (with pricing data)
   
3. Main useEffect triggers AGAIN (because state.cart changed)
   → Calls /api/pricing/calculate AGAIN
   → Infinite loop! 🔄
   
4. Project useEffect ALSO triggers (because state.cart changed)
   → Calls /api/pricing/calculate AGAIN
   → More API calls! 🔄🔄
```

---

## The Fix

### Solution 1: Use `useMemo` for Cart Tracking

Instead of tracking `state.cart` directly (which changes on every update), track a **stable key** that only changes when items/quantities actually change:

```javascript
// ⭐ Track cart items ที่ต้องคำนวณ (ป้องกัน infinite loop)
const cartItemsKey = useMemo(() => {
  if (!state.cart || state.cart.length === 0) return 'empty';
  
  // สร้าง key จาก SKU + qty + needsPricing เท่านั้น
  return state.cart
    .map(it => `${it.sku}:${it.qty}:${it.needsPricing ? '1' : '0'}:${it.priceSource || 'system'}`)
    .sort()
    .join('|');
}, [state.cart]);

useEffect(() => {
  // ... pricing logic ...
}, [state.status, cartItemsKey, state.customer, state.deliveryType, state.shippingCustomerPay]);
//                ^^^^^^^^^^^^ ← Use stable key instead of state.cart
```

**How it works:**
- `cartItemsKey` only changes when SKU, qty, or needsPricing changes
- When `APPLY_PRICING_RESULT` updates cart with pricing data, `cartItemsKey` stays the same
- useEffect doesn't trigger again → No infinite loop! ✅

### Solution 2: Use `useRef` for Project Tracking

For the project useEffect, use `useRef` to track previous project and only trigger when project actually changes:

```javascript
const prevProjectRef = React.useRef(selectedProject);

useEffect(() => {
  // ⭐ ป้องกันการ trigger ซ้ำ: ถ้า project ไม่เปลี่ยน ไม่ต้องคำนวณใหม่
  if (prevProjectRef.current === selectedProject) {
    console.log('❌ [PROJECT CHANGE] Project unchanged, skipping calculation');
    return;
  }
  
  prevProjectRef.current = selectedProject;
  
  // ... project pricing logic ...
}, [selectedProject]); // ⭐ Only trigger when selectedProject changes
```

**How it works:**
- `prevProjectRef` stores the previous project value
- If project hasn't changed, skip the calculation
- Only trigger when `selectedProject` actually changes
- Remove `state.cart` from dependencies → No infinite loop! ✅

---

## Changes Made

### File: `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

**Change 1 - Line ~343**: Add `useMemo` for cart tracking
```javascript
// ⭐ Track cart items ที่ต้องคำนวณ (ป้องกัน infinite loop)
const cartItemsKey = useMemo(() => {
  if (!state.cart || state.cart.length === 0) return 'empty';
  
  return state.cart
    .map(it => `${it.sku}:${it.qty}:${it.needsPricing ? '1' : '0'}:${it.priceSource || 'system'}`)
    .sort()
    .join('|');
}, [state.cart]);
```

**Change 2 - Line ~596**: Update main useEffect dependency
```javascript
}, [state.status, cartItemsKey, state.customer, state.deliveryType, state.shippingCustomerPay]);
//                ^^^^^^^^^^^^ ← Changed from state.cart
```

**Change 3 - Line ~750**: Add `useRef` for project tracking
```javascript
const prevProjectRef = React.useRef(selectedProject);

useEffect(() => {
  // ⭐ ป้องกันการ trigger ซ้ำ
  if (prevProjectRef.current === selectedProject) {
    return;
  }
  
  prevProjectRef.current = selectedProject;
  // ...
```

**Change 4 - Line ~893**: Update project useEffect dependency
```javascript
}, [selectedProject]); // ⭐ Removed state.cart, state.customer, etc.
```

---

## Benefits

1. ✅ **No Infinite Loop**: API calls only when necessary
2. ✅ **Better Performance**: Fewer unnecessary re-renders
3. ✅ **Stable Behavior**: Predictable pricing calculations
4. ✅ **Cleaner Logs**: No duplicate API calls

---

## Testing

### Before Fix (BAD):
```
User adds item:
  → POST /api/pricing/calculate (1st call)
  → POST /api/pricing/calculate (2nd call - duplicate!)
  → POST /api/pricing/calculate (3rd call - project!)
```

### After Fix (GOOD):
```
User adds item:
  → POST /api/pricing/calculate (1st call only)
  
User changes project:
  → POST /api/pricing/calculate (project call only)
```

---

## Summary

Fixed infinite loop by:
1. ✅ Using `useMemo` to create stable cart key (instead of tracking `state.cart` directly)
2. ✅ Using `useRef` to track previous project value
3. ✅ Removing `state.cart` from project useEffect dependencies
4. ✅ Only triggering API calls when actual data changes (not on every state update)

**Result**: Clean, efficient pricing calculations with no duplicate API calls

---

**Status**: ✅ Fixed
**Files Modified**: 
- `frontend/src/pages/CreateQuote/Step6_Summary.jsx`
