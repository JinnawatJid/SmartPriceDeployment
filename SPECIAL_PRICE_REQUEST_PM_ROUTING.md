# Special Price Request - PM Routing by Category

## Requirement
เมื่อราคา < SDM ต้องส่งให้ PM แต่ละคนตามCategory สินค้านั้นๆ

## Product Categories Mapping

### SKU Categories (based on first letter)
| Category | SKU Prefix | Description | PM Assignment |
|---|---|---|---|
| G | G* | Glass (กระจก) | PM_Glass |
| A | A* | Aluminium (อลูมิเนียม) | PM_Aluminium |
| C | C* | CLine (ซีไลน์) | PM_CLine |
| Y | Y* | Yipsum (ยิปซั่ม) | PM_Yipsum |
| S | S* | Sealant (ซีลแลนท์) | PM_Sealant |
| E | E* | Equipment (อุปกรณ์) | PM_Equipment |

## Approval Flow

### Current Flow (ราคา >= SDM)
```
Sales → ZM → RM → SDM → Approved
```

### New Flow (ราคา < SDM)
```
Sales → ZM → RM → PM (by Category) → Approved
```

## Implementation Details

### 1. Database Schema Update

#### Table: special_price_requests
Add new columns:
```sql
ALTER TABLE special_price_requests ADD (
    pm_approver_id VARCHAR(50) NULL,
    pm_approver_name VARCHAR(255) NULL,
    pm_category VARCHAR(10) NULL,
    is_below_sdm BIT DEFAULT 0,
    sdm_threshold_price FLOAT NULL
);
```

#### Table: special_price_request_items
Add new columns:
```sql
ALTER TABLE special_price_request_items ADD (
    product_category VARCHAR(10) NULL,
    is_below_sdm BIT DEFAULT 0
);
```

### 2. Backend Logic

#### Step 1: Determine if price is below SDM
```python
# In create_special_price_request()
requested_total = sum(float(item.requested_price) * float(item.quantity) for item in request_data.items)
sdm_threshold = get_sdm_threshold()  # ต้องกำหนดค่า SDM threshold

is_below_sdm = requested_total < sdm_threshold
```

#### Step 2: Extract product categories from items
```python
# Get unique categories from all items
categories = set()
for item in request_data.items:
    category = item.sku[0].upper()  # First letter of SKU
    if category in ['G', 'A', 'C', 'Y', 'S', 'E']:
        categories.add(category)
```

#### Step 3: Route to PM if below SDM
```python
if is_below_sdm:
    # Find PM for each category
    pms_by_category = {}
    for category in categories:
        pm = await find_pm_by_category(category)
        pms_by_category[category] = pm
    
    # Set initial approver to first PM
    first_pm = list(pms_by_category.values())[0]
    initial_status = 'PENDING_PM'
    approver_id = f"PM_{first_pm['category']}"
else:
    # Original flow: route to SDM
    initial_status = 'PENDING_ZM'
    approver_id = f"ZM_{branch_code}"
```

### 3. New Functions in employee_position_mapper.py

```python
async def find_pm_by_category(category: str) -> Optional[Dict]:
    """Find Product Manager by product category"""
    category_map = {
        'G': 'PM_Glass',
        'A': 'PM_Accessories',
        'C': 'PM_Cement',
        'Y': 'PM_Yipsum',
        'S': 'PM_Supplies',
        'E': 'PM_Electronics'
    }
    
    role_name = category_map.get(category)
    if not role_name:
        return None
    
    emp = await query_employee_by_role(role_name, "90HO")
    if emp:
        return {
            "employee_id": emp.get("username"),
            "branch": emp.get("branchCode"),
            "name": emp.get("empName"),
            "role": "PM",
            "category": category,
            "region": "ALL"
        }
    return None

async def find_all_pms_by_categories(categories: list) -> Dict[str, Dict]:
    """Find all PMs for given categories"""
    pms = {}
    for category in categories:
        pm = await find_pm_by_category(category)
        if pm:
            pms[category] = pm
    return pms
```

### 4. Approval Flow Update

#### Current Approval Levels
```
Level 1: ZM (Zone Manager)
Level 2: RM (Regional Manager)
Level 3: SDM (Sales Director Manager)
```

#### New Approval Levels (when price < SDM)
```
Level 1: ZM (Zone Manager)
Level 2: RM (Regional Manager)
Level 3: PM (Product Manager) - by category
```

### 5. Frontend Changes

#### SpecialPriceApproval.jsx
- Show PM approver instead of SDM when price < SDM threshold
- Display product category in approval request
- Show which PM is approving based on category

#### Step6_Summary.jsx (Create Quote)
- Add logic to detect if special price is below SDM
- Show warning if price < SDM (will need PM approval)
- Display which PM will approve

## Configuration

### SDM Threshold Price
Need to define in environment or config:
```python
# backend/config/config_external_api.py
SDM_THRESHOLD_PRICE = float(os.getenv("SDM_THRESHOLD_PRICE", "50000"))  # Default 50,000 THB
```

### PM Role Names (in Auth API)
```
PM_Glass: ผู้จัดการผลิตภัณฑ์ - กระจก
PM_Aluminium: ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม
PM_CLine: ผู้จัดการผลิตภัณฑ์ - ซีไลน์
PM_Yipsum: ผู้จัดการผลิตภัณฑ์ - ยิปซั่ม
PM_Sealant: ผู้จัดการผลิตภัณฑ์ - ซีลแลนท์
PM_Equipment: ผู้จัดการผลิตภัณฑ์ - อุปกรณ์
```

## Database Queries

### Get pending PM approvals by category
```sql
SELECT 
    id, quote_no, customer_code, customer_name,
    pm_category, pm_approver_name,
    original_total, requested_total, discount_percentage,
    created_at
FROM special_price_requests
WHERE status = 'PENDING_PM'
  AND pm_category = ?
ORDER BY created_at DESC
```

### Get approval history with PM
```sql
SELECT 
    r.id, r.quote_no, r.customer_code,
    r.status, r.pm_category, r.pm_approver_name,
    r.created_at, r.updated_at
FROM special_price_requests r
WHERE r.pm_approver_id IS NOT NULL
ORDER BY r.created_at DESC
```

## Testing Checklist

- [ ] Create special price request with price < SDM threshold
- [ ] Verify PM is assigned based on product category
- [ ] Verify approval flow goes to PM instead of SDM
- [ ] Test with multiple categories in same request
- [ ] Verify PM can approve/reject
- [ ] Test with price >= SDM threshold (should go to SDM)
- [ ] Verify approval history shows PM approver
- [ ] Test PM approval notifications

## Files to Update

1. **backend/special_price_request_router.py**
   - Update create_special_price_request() to detect price < SDM
   - Add PM routing logic
   - Update approval flow

2. **backend/employee_position_mapper.py**
   - Add find_pm_by_category()
   - Add find_all_pms_by_categories()

3. **backend/config/config_external_api.py**
   - Add SDM_THRESHOLD_PRICE configuration

4. **frontend/src/pages/SpecialPriceApproval.jsx**
   - Update to show PM approver when applicable
   - Display product category

5. **frontend/src/pages/CreateQuote/Step6_Summary.jsx**
   - Add warning for price < SDM
   - Show which PM will approve

6. **Database**
   - Add new columns to special_price_requests table
   - Add new columns to special_price_request_items table

---

**Status**: Ready for implementation
**Priority**: High
**Estimated Effort**: 2-3 days
