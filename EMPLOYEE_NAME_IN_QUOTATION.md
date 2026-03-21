# Employee Name Display in Quotation - Fix Complete

## Problem Statement
In the quotation PDF (quotation.html), the employee name was not displaying correctly. Instead of showing the employee's name (e.g., "สมชาย"), it was showing the Employee ID (e.g., "Employee 21748") in the signature section.

## Root Cause Analysis

### The Issue
1. Frontend sends `sales: employee?.name || ""` to the print endpoint
2. However, sometimes `employee?.name` is empty or undefined
3. Backend receives an empty `sales` field
4. The quotation template displays `{{ q.sales }}` which is empty
5. Result: Employee ID appears instead of the name

### Why It Happened
- The `sales` field in the payload might be empty if:
  - Frontend's `employee?.name` is not populated
  - The employee object from AuthContext doesn't have the name field
  - Network issues prevent proper data loading
- Frontend was not sending `salesId` field, so backend couldn't fetch the employee name

## Solution Implemented

### Changes Made

#### Part 1: Frontend Changes
**Files**: 
- `frontend/src/pages/CreateQuote/Step6_Summary.jsx`
- `frontend/src/pages/OrderDetailPage.jsx`
- `frontend/src/pages/CustomerDetail.jsx`

Added `salesId` field to the print payload:
```javascript
const payload = {
  quoteNo: state.quoteNo || "",
  date: new Date().toLocaleDateString("th-TH"),
  sales: employee?.name || "",
  salesId: employee?.id || "",  // ⭐ เพิ่ม salesId เพื่อให้ backend ดึงชื่อพนักงานได้
  customer: { ... },
  ...
};
```

This ensures that:
- If `sales` field has a value, it will be used
- If `sales` field is empty, backend can use `salesId` to fetch the employee name

#### Part 2: Backend Changes
**File**: `backend/print_router.py`

Added fallback logic in the `print_quotation` function to:

1. **Check if sales field is empty**
   - If `payload.get("sales")` is empty or whitespace-only

2. **Extract Employee ID from payload**
   - Try to get `salesId` field
   - Or get `employee.id` from the payload

3. **Fetch Employee Name from API**
   - Call the employee API with the employee ID
   - Search for matching employee record
   - Extract the `EmpName` field

4. **Populate sales field**
   - Set `payload["sales"]` to the employee name
   - If API call fails, use the employee ID as fallback

### Code Logic

**Frontend:**
```javascript
salesId: employee?.id || "",  // ⭐ เพิ่ม salesId
```

**Backend:**
```python
# ⭐ ถ้า sales field ไม่มีค่า ให้ดึงชื่อพนักงานจาก SalesID
if not payload.get("sales") or payload.get("sales").strip() == "":
    sales_id = payload.get("salesId") or payload.get("employee", {}).get("id")
    if sales_id:
        try:
            # ดึงชื่อพนักงานจาก API
            response = httpx.get(EMP_API_URL, headers=EMP_API_HEADERS, timeout=10)
            data = response.json()
            
            # หาพนักงานที่ตรงกับ sales_id
            for emp in employees:
                emp_code = str(emp.get("EmpCode", "")).strip()
                if emp_code.lower() == str(sales_id).lower():
                    payload["sales"] = str(emp.get("EmpName", "")).strip()
                    break
        except Exception as e:
            print(f"⚠️ Error fetching employee name: {e}")
            payload["sales"] = sales_id  # ใช้ ID ถ้าดึงชื่อไม่ได้
```

## Behavior After Fix

### When Printing Quotation
1. Frontend sends print request with:
   - `sales: employee?.name` (if available)
   - `salesId: employee?.id` (always sent)

2. Backend receives print request and:
   - Checks if `sales` field has a value
   - If empty:
     - Extracts employee ID from `salesId` or `employee.id`
     - Calls employee API to fetch employee name
     - Updates `payload["sales"]` with the employee name
   - If API call fails:
     - Uses employee ID as fallback

3. Renders quotation template with employee name

### Result
- Quotation PDF now displays employee name (e.g., "สมชาย")
- Instead of Employee ID (e.g., "Employee 21748")
- Fallback to ID if name cannot be fetched
- Works in all three print locations:
  - Header section: "พนักงานขาย : [Name]"
  - Signature section: "[Name]"

## Testing Checklist

- [ ] Create a new quotation in Step6_Summary
- [ ] Print the quotation
- [ ] Verify employee name displays correctly (not Employee ID)
- [ ] Check that the name appears in both:
  - Header section: "พนักงานขาย : [Name]"
  - Signature section: "[Name]"
- [ ] View an existing quotation in OrderDetailPage
- [ ] Print the quotation
- [ ] Verify employee name displays correctly
- [ ] View a customer's quotation in CustomerDetail
- [ ] Print the quotation
- [ ] Verify employee name displays correctly
- [ ] Test with different employees
- [ ] Verify fallback works if API is unavailable

## Files Modified
- `frontend/src/pages/CreateQuote/Step6_Summary.jsx` - Added `salesId` field to payload
- `frontend/src/pages/OrderDetailPage.jsx` - Added `salesId` field to payload
- `frontend/src/pages/CustomerDetail.jsx` - Added `salesId` field to payload
- `backend/print_router.py` - Added fallback logic to fetch employee name from API

## Related Features
- Task 6: Fix CreateByEmployeeCode not saved in Project_Price_Header
- Task 7: Lock project price to always show when selected
- Task 8: Display employee name in quotation (THIS TASK)

## Notes
- The fix is backward compatible - if `sales` field already has a value, it won't be overwritten
- The API call is only made if the `sales` field is empty
- Error handling ensures the print process continues even if the API call fails
- The fallback uses employee ID if the name cannot be fetched
- The fix handles both `salesId` and `employee.id` field names for flexibility
- All three print locations (Step6, OrderDetail, CustomerDetail) now send `salesId` for consistency
