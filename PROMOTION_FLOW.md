# Promotion System Flow Documentation

## Overview
This document explains how the promotion system works, specifically focusing on customer-based promotions.

---

## Customer-Based Promotion Flow

### 1. Database Structure

**Promotion_Header Table:**
- `Id` - Primary key
- `PromotionCode` - Auto-generated (PROMO-YYYYMMDD-XXXX)
- `PromotionName` - Name of promotion
- `BranchCode` - Comma-separated branch codes
- `StartDate` - Start date
- `EndDate` - End date
- `Status` - 'active' or 'inactive'
- `CreatedBy` - Username who created
- `CreatedAt`, `UpdatedAt` - Timestamps

**Promotion_Customers Table:**
- `Id` - Primary key
- `PromotionId` - Foreign key to Promotion_Header
- `CustomerCode` - Customer code (e.g., '08015AY')
- `PromotionText` - Promotion description text
- `CreatedAt` - Timestamp

### 2. Backend API Endpoint

**Endpoint:** `GET /api/promotions/active-by-customer?customerCode={code}`

**Location:** `backend/promotion_router.py`

**Query Logic:**
```sql
SELECT 
    ph.Id, ph.PromotionName, ph.BranchCode, ph.StartDate, ph.EndDate,
    pc.PromotionText
FROM Promotion_Header ph
JOIN Promotion_Customers pc ON ph.Id = pc.PromotionId
WHERE ph.Status = 'active'
AND ph.StartDate <= TODAY
AND ph.EndDate >= TODAY
AND pc.CustomerCode = ?
```

**Returns:**
```json
[
  {
    "promotion_id": 1,
    "promotion_name": "โปรโมชั่นพิเศษ",
    "promotion_text": "ลดพิเศษ 10%",
    "branch": "001,002",
    "start_date": "2026-02-01",
    "end_date": "2026-03-31"
  }
]
```

### 3. Frontend Component

**Component:** `CustomerPromotionBanner.jsx`

**Location:** `frontend/src/components/wizard/CustomerPromotionBanner.jsx`

**Props:**
- `customerCode` (string) - Customer code to fetch promotions for

**Behavior:**
- Fetches promotions when `customerCode` changes
- Shows loading state while fetching
- Displays promotions in a banner with dismiss button
- Returns `null` if no promotions found

### 4. Integration in Step6_Summary

**Location:** `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

**Current Implementation (Line 1472-1478):**
```jsx
{state.customer?.code ? (
  <div className="mt-3">
    <CustomerPromotionBanner customerCode={state.customer.code} />
  </div>
) : (
  <div className="mt-3 text-xs text-gray-500">
    (ยังไม่ได้เลือกลูกค้า - ไม่มีโปรโมชั่นพิเศษ)
  </div>
)}
```

---

## ISSUE IDENTIFIED

### Problem
The customer object structure uses `id` field for customer code, but the code is checking for `code` field.

**Customer Object Structure (from CustomerSearchSection):**
```javascript
{
  id: "08015AY",        // ← This is the customer code
  name: "ชื่อลูกค้า",
  phone: "0812345678",
  // ... other fields
}
```

**Current Code (WRONG):**
```jsx
state.customer?.code  // ← This is undefined!
```

**Should Be:**
```jsx
state.customer?.id    // ← This contains the customer code
```

### Solution

Change line 1472 in `Step6_Summary.jsx` from:
```jsx
{state.customer?.code ? (
```

To:
```jsx
{state.customer?.id ? (
```

And change line 1473 from:
```jsx
<CustomerPromotionBanner customerCode={state.customer.code} />
```

To:
```jsx
<CustomerPromotionBanner customerCode={state.customer.id} />
```

---

## Testing Steps

### 1. Verify Data in Database
```sql
-- Check if customer has promotions
SELECT * FROM Promotion_Customers WHERE CustomerCode = '08015AY'

-- Check promotion details
SELECT ph.*, pc.PromotionText
FROM Promotion_Header ph
JOIN Promotion_Customers pc ON ph.Id = pc.PromotionId
WHERE pc.CustomerCode = '08015AY'
AND ph.Status = 'active'
AND ph.StartDate <= GETDATE()
AND ph.EndDate >= GETDATE()
```

### 2. Test Frontend Flow
1. Open Create Quote page
2. Search and select customer with code '08015AY'
3. Check Browser Console for logs:
   - `👤 [STEP6] Customer changed:` - Should show customer object with `id` field
   - `🔍 [CUSTOMER PROMO] Starting fetch for customerCode:` - Should show customer code
   - `📡 [CUSTOMER PROMO] Fetching from:` - Should show API URL
   - `✅ [CUSTOMER PROMO] Response received:` - Should show promotion data

### 3. Test Backend API
Check Terminal/Backend logs for:
- `👤 [CUSTOMER PROMO API] Searching for customer:` - Should show customer code
- `📦 [CUSTOMER PROMO API] Found X customer promotions` - Should show count
- `✅ [CUSTOMER PROMO API] Result:` - Should show promotion array

### 4. Verify Banner Display
- Banner should appear below customer search section
- Should show promotion name and text
- Should have dismiss button (X)
- Should show end date

---

## Additional Notes

### Customer Code Resolution
The system uses a helper function `getCustomerCode()` in some places:

```javascript
const getCustomerCode = (customer) => {
  return customer?.id || customer?.code || "";
};
```

This function handles both `id` and `code` fields for backward compatibility.

### Logging
Extensive logging is added for debugging:
- Frontend: CustomerPromotionBanner.jsx
- Backend: promotion_router.py (active-by-customer endpoint)

All logs are prefixed with emojis for easy identification:
- 👤 Customer-related
- 🔍 Search/Query
- 📡 API calls
- ✅ Success
- ❌ Error
- 📦 Data/Results

---

## Related Files

### Backend
- `backend/promotion_router.py` - API endpoints
- `backend/config/db_mssql.py` - Database connection

### Frontend
- `frontend/src/components/wizard/CustomerPromotionBanner.jsx` - Banner component
- `frontend/src/pages/CreateQuote/Step6_Summary.jsx` - Integration point
- `frontend/src/components/wizard/CustomerSearchSection.jsx` - Customer selection
- `frontend/src/services/api.js` - API client

### Database
- `Promotion_Header` table
- `Promotion_Customers` table
- `Promotion_Items` table

---

## Future Enhancements

1. Add customer promotion preview in customer search dropdown
2. Show promotion count badge on customer card
3. Add promotion filtering by branch
4. Add promotion expiry warnings
5. Support multiple promotion texts per customer
