# Product Categories Mapping

## Product Categories (6 Categories)

| Code | SKU Prefix | English Name | Thai Name | PM Role |
|---|---|---|---|---|
| G | G* | Glass | กระจก | ผู้จัดการผลิตภัณฑ์ - กระจก |
| A | A* | Aluminium | อลูมิเนียม | ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม |
| C | C* | CLine | ซีไลน์ | ผู้จัดการผลิตภัณฑ์ - ซีไลน์ |
| Y | Y* | Yipsum | ยิปซั่ม | ผู้จัดการผลิตภัณฑ์ - ยิปซั่ม |
| S | S* | Sealant | ซีลแลนท์ | ผู้จัดการผลิตภัณฑ์ - ซีลแลนท์ |
| E | E* | Equipment | อุปกรณ์ | ผู้จัดการผลิตภัณฑ์ - อุปกรณ์ |

---

## Category Details

### G - Glass (กระจก)
- **SKU Examples**: G001, G002, G010010100000300
- **Products**: Window glass, tempered glass, laminated glass, etc.
- **PM Role**: ผู้จัดการผลิตภัณฑ์ - กระจก

### A - Aluminium (อลูมิเนียม)
- **SKU Examples**: A001, A002, A100
- **Products**: Aluminium frames, profiles, accessories
- **PM Role**: ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม

### C - CLine (ซีไลน์)
- **SKU Examples**: C001, C002, C100
- **Products**: CLine products (specific product line)
- **PM Role**: ผู้จัดการผลิตภัณฑ์ - ซีไลน์

### Y - Yipsum (ยิปซั่ม)
- **SKU Examples**: Y001, Y002, Y100
- **Products**: Gypsum boards, drywall, plasterboard
- **PM Role**: ผู้จัดการผลิตภัณฑ์ - ยิปซั่ม

### S - Sealant (ซีลแลนท์)
- **SKU Examples**: S001, S002, S100
- **Products**: Sealants, caulks, adhesives
- **PM Role**: ผู้จัดการผลิตภัณฑ์ - ซีลแลนท์

### E - Equipment (อุปกรณ์)
- **SKU Examples**: E001, E002, E100
- **Products**: Tools, equipment, machinery
- **PM Role**: ผู้จัดการผลิตภัณฑ์ - อุปกรณ์

---

## Implementation

### Backend - employee_position_mapper.py

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

### Backend - items.py

```python
def get_item_categories():
    conn = get_mssql_conn()
    cursor = conn.cursor()

    # ⭐ แบ่งประเภทตามอักษรตัวแรกของ SKU
    cursor.execute("""
        SELECT
            LEFT(SKU, 1) AS name,
            COUNT(*) AS count
        FROM Item_Master
        WHERE LEFT(SKU, 1) IN ('G', 'A', 'C', 'Y', 'S', 'E')
          AND Blocked = 0
        GROUP BY LEFT(SKU, 1)
        ORDER BY LEFT(SKU, 1)
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{"name": r[0], "count": r[1]} for r in rows]
```

---

## Special Price Request Routing

### When Price < SDM Threshold

**Flow:**
1. Extract product categories from items (first letter of SKU)
2. Find PM for each category
3. Route to first PM (if multiple categories)
4. PM approves/rejects

**Example:**
- Request with items: G001, G002, A001
- Categories: {G, A}
- PM Assigned: PM_Glass (first category)
- Status: PENDING_PM

---

## Database Queries

### Get items by category
```sql
SELECT 
    SKU, Description, Product_Group, Product_Sub_Group
FROM Item_Master
WHERE LEFT(SKU, 1) = 'G'  -- Glass
  AND Blocked = 0
ORDER BY SKU
```

### Get category distribution
```sql
SELECT 
    LEFT(SKU, 1) AS Category,
    COUNT(*) AS ItemCount
FROM Item_Master
WHERE Blocked = 0
GROUP BY LEFT(SKU, 1)
ORDER BY Category
```

### Get pending PM approvals by category
```sql
SELECT 
    id, quote_no, customer_code, pm_category,
    pm_approver_name, original_total, requested_total,
    created_at
FROM special_price_requests
WHERE status = 'PENDING_PM'
  AND pm_category = 'G'  -- Glass
ORDER BY created_at DESC
```

---

## Files Updated

1. ✅ `backend/employee_position_mapper.py`
   - Updated category_map with correct names

2. ✅ `backend/special_price_request_router.py`
   - Uses correct category mapping

3. ✅ `SPECIAL_PRICE_REQUEST_PM_ROUTING.md`
   - Updated with correct category names

4. ✅ `SPECIAL_PRICE_REQUEST_PM_IMPLEMENTATION.md`
   - Updated with correct category names

---

## Testing

### Test Case 1: Glass Product
```json
{
  "items": [
    {
      "sku": "G001",
      "item_name": "กระจกใส",
      "requested_price": 400
    }
  ]
}
```
**Expected**: pm_category = "G", pm_approver_name = "ผู้จัดการผลิตภัณฑ์ - กระจก"

### Test Case 2: Multiple Categories
```json
{
  "items": [
    {"sku": "G001", "requested_price": 400},
    {"sku": "A001", "requested_price": 300},
    {"sku": "S001", "requested_price": 200}
  ]
}
```
**Expected**: pm_category = "G" (first), categories = {G, A, S}

### Test Case 3: Aluminium Product
```json
{
  "items": [
    {
      "sku": "A100",
      "item_name": "อลูมิเนียมโปรไฟล์",
      "requested_price": 500
    }
  ]
}
```
**Expected**: pm_category = "A", pm_approver_name = "ผู้จัดการผลิตภัณฑ์ - อลูมิเนียม"

---

**Last Updated**: March 22, 2026
**Status**: Ready for production ✅
