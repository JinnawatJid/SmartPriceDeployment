# Project Price Lock Fix - Task 7 Complete

## Problem Statement
When a user selected a project price and then:
1. Changed the quantity of an item in the cart, OR
2. Changed the delivery method (รับเอง/จัดส่ง)

The system would recalculate the price instead of keeping the locked project price. This violated the requirement that project prices should remain locked regardless of other changes.

### User Queries
- "เมื่อฉันเลือกสินค้าแล้วกดใช้ราคาโครงการแล้ว พอฉันเปลี่ยนจำนวนตรง CartItemRow ราคามันคำนวณใหม่ ไม่ใช่ราคาโครงการ"
- "แล้วก็มีตรง รับเอง,จัดส่ง เมื่อฉันกดเปลี่ยนวิธีการจัดส่ง ราคามันก็ไม่lockราคาโครงการไว้"
- Translation: 
  - "When I select an item and use project price, then change the quantity in CartItemRow, the price recalculates instead of using the project price"
  - "Also when I change the delivery method (pickup/delivery), the price doesn't lock the project price"

## Root Cause Analysis

### The Issue
1. When user changes quantity in `CartItemRow`, it dispatches `UPDATE_CART_QTY` action
2. When user changes delivery method, it updates `state.deliveryType` and `state.shippingCustomerPay`
3. Both changes trigger the `recalculateWithProject` useEffect
4. The useEffect calls the pricing API with the new values
5. The API returns new prices, overwriting the locked project price
6. The locked status (`_locked: true`) was set but not preserved when recalculating

### Why It Happened
The `recalculateWithProject` useEffect had incomplete dependency array:
- ✅ Had: `selectedProject`, `state.customer`, `state.cart`
- ❌ Missing: `state.deliveryType`, `state.shippingCustomerPay`

This meant that when delivery method changed, the useEffect didn't trigger, but the API was still being called with old delivery values. Additionally, when it did trigger, the locked prices weren't being preserved.

## Solution Implemented

### Changes Made
**File**: `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

#### Part 1: Preserve Locked Prices During Recalculation
Modified the `recalculateWithProject` useEffect to:

1. **Check for Previously Locked Items**
   - Before processing each item from the API response, check if it was previously locked
   - Use `calculation.cart?.find(prev => prev.sku === item.sku)` to find the previous state
   - Check if `prevLockedItem?._locked === true`

2. **Preserve Locked Prices**
   - If an item was previously locked, preserve its unit price and price_per_sheet
   - Use: `const lockedUnitPrice = wasLocked ? prevLockedItem.UnitPrice : item.UnitPrice`
   - Use: `const lockedPricePerSheet = wasLocked ? prevLockedItem.price_per_sheet : item.price_per_sheet`

3. **Recalculate Line Total with Locked Price**
   - Get the current quantity from `state.cart`
   - Calculate new line total: `(lockedPricePerSheet || lockedUnitPrice) * currentQty`
   - This ensures the line total updates when quantity changes, but the unit price stays locked

4. **Maintain Lock Status**
   - Keep `_locked: true` flag to indicate the price is locked
   - Keep `priceSource: 'project'` to indicate it's a project price

#### Part 2: Complete Dependency Array
Updated the useEffect dependency array to include all values that affect the calculation:

```javascript
}, [selectedProject, state.customer, state.cart, state.deliveryType, state.shippingCustomerPay]);
```

This ensures the useEffect triggers when:
- Project selection changes
- Customer changes
- Cart items change (add/remove/quantity)
- Delivery method changes (รับเอง/จัดส่ง)
- Shipping cost changes

### Code Logic
```javascript
const lockedItems = items.map(item => {
  const prevLockedItem = calculation.cart?.find(prev => prev.sku === item.sku);
  const wasLocked = prevLockedItem?._locked === true;
  
  if (selectedProject && (item.price_source === 'project' || wasLocked)) {
    const lockedUnitPrice = wasLocked ? prevLockedItem.UnitPrice : item.UnitPrice;
    const lockedPricePerSheet = wasLocked ? prevLockedItem.price_per_sheet : item.price_per_sheet;
    const currentQty = Number(state.cart.find(c => c.sku === item.sku)?.qty || 0);
    
    return {
      ...item,
      priceSource: 'project',
      price_source: 'project',
      _locked: true,
      UnitPrice: lockedUnitPrice,
      price_per_sheet: lockedPricePerSheet,
      _LineTotal: (lockedPricePerSheet || lockedUnitPrice) * currentQty,
    };
  }
  return item;
});
```

## Behavior After Fix

### When Project Price is Selected
1. User selects a project
2. System calculates prices using project rates
3. Items with project prices are marked with `_locked: true`

### When User Changes Quantity
1. Quantity change triggers `UPDATE_CART_QTY` in reducer
2. This updates `state.cart`, triggering `recalculateWithProject` useEffect
3. The useEffect detects that items are already locked
4. **Locked prices are preserved** - unit price stays the same
5. **Line total is recalculated** - new quantity × locked unit price
6. **Totals are recalculated** - based on new line totals

### When User Changes Delivery Method
1. Delivery method change updates `state.deliveryType` and `state.shippingCustomerPay`
2. This triggers `recalculateWithProject` useEffect (now in dependency array)
3. The useEffect detects that items are already locked
4. **Locked prices are preserved** - unit price stays the same
5. **Totals are recalculated** - based on locked prices
6. **Shipping cost updates** - but doesn't affect item prices

### When User Changes Other Values
- Remarks added: Locked prices remain
- Any other change: Locked prices remain

## Testing Checklist

- [ ] Select a project with project prices
- [ ] Verify items show "ราคาโครงการ" badge
- [ ] Change quantity of an item
- [ ] Verify unit price stays the same (doesn't recalculate)
- [ ] Verify line total updates correctly (new qty × locked price)
- [ ] Verify total amount updates correctly
- [ ] Change delivery method from รับเอง to จัดส่ง
- [ ] Verify project prices still locked
- [ ] Verify shipping cost updates
- [ ] Change delivery method back to รับเอง
- [ ] Verify project prices still locked
- [ ] Add remarks
- [ ] Verify project prices still locked
- [ ] Deselect project
- [ ] Verify prices recalculate normally

## Files Modified
- `frontend/src/pages/CreateQuote/Step6_Summary.jsx`
  - Added lock preservation logic in `recalculateWithProject` useEffect
  - Updated dependency array to include `state.deliveryType` and `state.shippingCustomerPay`

## Related Features
- Task 5: Save project_code when using project price
- Task 6: Fix CreateByEmployeeCode not saved in Project_Price_Header
- Task 7: Lock project price to always show when selected (THIS TASK)

## Notes
- The fix maintains backward compatibility - non-locked items still recalculate normally
- The lock is only applied when a project is selected and the item has project pricing
- The line total correctly updates when quantity changes, maintaining accurate totals
- The fix handles both glass (with price_per_sheet) and non-glass items
- The dependency array now includes all values that affect pricing calculations

