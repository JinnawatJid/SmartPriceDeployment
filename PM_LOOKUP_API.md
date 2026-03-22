# PM Lookup API

## New Endpoint: Get PM by Categories

### Endpoint
```
GET /api/special-price-requests/pm-by-categories?categories=A,G,C
```

### Purpose
ตรวจสอบว่า PM แต่ละ product category คือใครก่อนสร้าง special price request

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| categories | string | Yes | Comma-separated list of product categories | "A,G,C" |

### Product Categories

| Code | Category | PM Role Name |
|------|----------|--------------|
| G | กระจก (Glass) | ผู้จัดการผลิตภัณฑ์กระจก |
| A | อลูมิเนียม (Aluminium) | ผู้จัดการผลิตภัณฑ์อลูมิเนียม |
| C | ซีไลน์ (CLine) | ผู้จัดการผลิตภัณฑ์โครงคร่าวฝ้าเพดานโครงผนัง |
| Y | ยิปซั่ม (Yipsum) | ผู้จัดการผลิตภัณฑ์ยิปซัม |
| S | ซีลแลนท์ (Sealant) | ผู้จัดการผลิตภัณฑ์ซีลแลนท์ |
| E | อุปกรณ์ (Equipment) | ผู้จัดการผลิตภัณฑ์อุปกรณ์และอื่นๆ |

---

## Request Example

### Single Category
```bash
GET /api/special-price-requests/pm-by-categories?categories=A
```

### Multiple Categories
```bash
GET /api/special-price-requests/pm-by-categories?categories=A,G,C
```

---

## Response Format

### Success Response (PM Found)

```json
{
  "A": {
    "employee_id": "21800",
    "name": "สมชาย ใจดี",
    "role": "PM",
    "category": "A",
    "found": true
  },
  "G": {
    "employee_id": "21801",
    "name": "สมหญิง รักงาน",
    "role": "PM",
    "category": "G",
    "found": true
  }
}
```

### Success Response (PM Not Found)

```json
{
  "A": {
    "employee_id": null,
    "name": null,
    "role": null,
    "category": "A",
    "found": false
  }
}
```

### Error Response

```json
{
  "detail": "No categories provided"
}
```

---

## Usage in Frontend

### Example: Check PM before creating request

```javascript
// 1. Extract categories from cart items
const categories = [...new Set(
  cartItems
    .filter(item => item.approval_level === 'PM_APPROVAL')
    .map(item => item.sku[0].toUpperCase())
)];

// 2. Call API to get PM info
const response = await api.get('/api/special-price-requests/pm-by-categories', {
  params: { categories: categories.join(',') }
});

// 3. Check if all PMs are found
const allPmsFound = Object.values(response.data).every(pm => pm.found);

if (!allPmsFound) {
  const missingCategories = Object.entries(response.data)
    .filter(([_, pm]) => !pm.found)
    .map(([category, _]) => category);
  
  alert(`ไม่พบ PM สำหรับหมวดหมู่: ${missingCategories.join(', ')}`);
  return;
}

// 4. Show PM info to user
console.log('PMs who will approve:', response.data);

// 5. Create special price request
await api.post('/api/special-price-requests', requestData);
```

---

## Use Cases

### 1. Pre-validation (Frontend)
ตรวจสอบก่อนสร้าง request ว่ามี PM หรือไม่:

```javascript
// Before creating request
const pmCheck = await api.get('/api/special-price-requests/pm-by-categories', {
  params: { categories: 'A' }
});

if (!pmCheck.data.A.found) {
  alert('ไม่พบ PM สำหรับสินค้าอลูมิเนียม กรุณาติดต่อผู้ดูแลระบบ');
  return;
}

// Show PM info
alert(`คำขอนี้จะต้องผ่านการอนุมัติจาก: ${pmCheck.data.A.name}`);
```

### 2. Display PM Info (Frontend)
แสดงข้อมูล PM ในหน้าสรุปก่อนส่งคำขอ:

```javascript
// In Step6_Summary.jsx
const [pmInfo, setPmInfo] = useState(null);

useEffect(() => {
  const loadPmInfo = async () => {
    const categories = extractCategories(itemsBelowSDM);
    if (categories.length > 0) {
      const response = await api.get('/api/special-price-requests/pm-by-categories', {
        params: { categories: categories.join(',') }
      });
      setPmInfo(response.data);
    }
  };
  
  loadPmInfo();
}, [itemsBelowSDM]);

// Display in UI
{pmInfo && (
  <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
    <p className="font-semibold">คำขอนี้จะต้องผ่านการอนุมัติจาก PM:</p>
    {Object.entries(pmInfo).map(([category, pm]) => (
      <p key={category}>
        {pm.found ? (
          `✅ ${getCategoryName(category)}: ${pm.name}`
        ) : (
          `❌ ${getCategoryName(category)}: ไม่พบ PM`
        )}
      </p>
    ))}
  </div>
)}
```

### 3. Approval Flow Display
แสดง flow การอนุมัติที่สมบูรณ์:

```javascript
const getApprovalFlow = (items, pmInfo) => {
  const needsPM = items.some(item => item.approval_level === 'PM_APPROVAL');
  
  if (needsPM && pmInfo) {
    const pmNames = Object.values(pmInfo)
      .filter(pm => pm.found)
      .map(pm => pm.name)
      .join(', ');
    
    return `Sales → ZM → RM → SDM → PM (${pmNames}) → Approved`;
  }
  
  // ... other flows
};
```

---

## Backend Implementation

### File: `backend/special_price_request_router.py`

```python
@router.get("/pm-by-categories")
async def get_pm_by_categories(categories: str):
    """Get PM information for given product categories"""
    try:
        category_list = [c.strip().upper() for c in categories.split(',') if c.strip()]
        
        if not category_list:
            raise HTTPException(status_code=400, detail="No categories provided")
        
        logger.info(f"Getting PMs for categories: {category_list}")
        
        # Call employee_position_mapper
        pms = await find_all_pms_by_categories(category_list)
        
        # Format response
        result = {}
        for category in category_list:
            pm = pms.get(category)
            if pm:
                result[category] = {
                    "employee_id": pm['employee_id'],
                    "name": pm['name'],
                    "role": pm['role'],
                    "category": pm['category'],
                    "found": True
                }
            else:
                result[category] = {
                    "employee_id": None,
                    "name": None,
                    "role": None,
                    "category": category,
                    "found": False
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting PMs by categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Testing

### Test Case 1: Single Category (Found)

**Request:**
```bash
GET /api/special-price-requests/pm-by-categories?categories=A
```

**Expected Response:**
```json
{
  "A": {
    "employee_id": "21800",
    "name": "สมชาย ใจดี",
    "role": "PM",
    "category": "A",
    "found": true
  }
}
```

### Test Case 2: Multiple Categories (Mixed)

**Request:**
```bash
GET /api/special-price-requests/pm-by-categories?categories=A,G,X
```

**Expected Response:**
```json
{
  "A": {
    "employee_id": "21800",
    "name": "สมชาย ใจดี",
    "role": "PM",
    "category": "A",
    "found": true
  },
  "G": {
    "employee_id": "21801",
    "name": "สมหญิง รักงาน",
    "role": "PM",
    "category": "G",
    "found": true
  },
  "X": {
    "employee_id": null,
    "name": null,
    "role": null,
    "category": "X",
    "found": false
  }
}
```

### Test Case 3: No Categories

**Request:**
```bash
GET /api/special-price-requests/pm-by-categories?categories=
```

**Expected Response:**
```json
{
  "detail": "No categories provided"
}
```

---

## Benefits

1. ✅ **Pre-validation**: ตรวจสอบก่อนสร้าง request ว่ามี PM หรือไม่
2. ✅ **User Feedback**: แสดงข้อมูล PM ให้ user เห็นก่อนส่งคำขอ
3. ✅ **Error Prevention**: ป้องกันการสร้าง request ที่ไม่สามารถอนุมัติได้
4. ✅ **Transparency**: User รู้ว่าคำขอจะต้องผ่านใครบ้าง

---

## Summary

**New Endpoint**: `GET /api/special-price-requests/pm-by-categories`

**Purpose**: ตรวจสอบว่า PM แต่ละ product category คือใคร

**Usage**: 
- Frontend เรียกก่อนสร้าง request
- แสดงข้อมูล PM ให้ user เห็น
- Validate ว่ามี PM ครบหรือไม่

**Response**: Dictionary mapping category → PM info (with `found` flag)

---

**Status**: ✅ Implemented
**File**: `backend/special_price_request_router.py`
