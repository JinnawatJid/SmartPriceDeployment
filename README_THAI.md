# ระบบ Smart Pricing - Manual Login และ Employee Position Mapper

## 🎯 สรุปสั้น ๆ

ระบบพร้อมใช้งานแล้ว! ✅

- ✅ Manual Login ทำงานได้ (เลือก Role และ Branch)
- ✅ Employee Position Mapper ค้นหาพนักงานจาก UXP API ได้
- ✅ ไม่มี Error 404 หรือ 405
- ✅ Special Price Request เป็น Placeholder (ตามที่ขอ)

## 🚀 วิธีใช้งาน Manual Login

### 1. เปิดหน้า Login
```
http://localhost:5173
```

### 2. คลิก "Manual Login"

### 3. กรอกข้อมูล
- **รหัสพนักงาน**: เช่น `21053`
- **Role**: เลือกจาก dropdown (พนักงานขาย, ผู้จัดการสาขา, ฯลฯ)
- **สาขา**: เลือกจาก dropdown (03TS, 90HO, ฯลฯ)

### 4. คลิก "เข้าสู่ระบบ"
ระบบจะ:
- คำนวณ Region จาก Branch อัตโนมัติ
- สร้าง JWT Token พร้อม role และ region
- เก็บ Token ใน Cookie
- Redirect ไป Dashboard

## 🔍 Employee Position Mapper

### วิธีใช้งาน (สำหรับนักพัฒนา)

```python
from employee_position_mapper import (
    find_zm_at_branch,
    find_rm_in_region,
    find_sdm,
    find_pm,
    find_ceo,
    find_sales_at_branch
)

# หา Zone Manager ที่สาขา 03TS
zm = await find_zm_at_branch("03TS")
# → {"employee_id": "21053", "name": "...", "branch": "03TS", "role": "ZM"}

# หา Regional Manager ในภูมิภาค BE
rm = await find_rm_in_region("BE")
# → {"employee_id": "20785", "name": "...", "branch": "90HO", "role": "RM", "region": "BE"}

# หา Sales Director Manager
sdm = await find_sdm()
# → {"employee_id": "...", "name": "...", "role": "SDM"}
```

### ชื่อ Role ที่ใช้ (ต้องตรงกับ UXP)
1. `พนักงานขาย` → Sales
2. `ผู้จัดการสาขา (R1-W2)` → ZM (Zone Manager)
3. `ผู้จัดการภูมิภาค (R1-W2)` → RM (Regional Manager)
4. `ผู้จัดการฝ่ายขาย (W1-SDM)` → SDM (Sales Director Manager)
5. `ผู้จัดการผลิตภัณฑ์ (Below SDM)` → PM (Product Manager)
6. `กรรมการผู้จัดการ` → CEO

## 🌍 Region Mapping

| Region Code | Region Name | Branch Code | Branch Name |
|-------------|-------------|-------------|-------------|
| BE | Bangkok East | 90HO | Head Office |
| N | North | 12CM | Chiang Mai |
| S | South | 13SR | Surat Thani |
| NE | Northeast | 10KK | Khon Kaen |
| C | Central | 21BS | Buriram/Saraburi |

## 📡 API Endpoints

### Login
```
POST /api/login/manual
Body: {
  "employeeCode": "21053",
  "role": "Sales",
  "branchId": "03TS"
}
Response: {
  "token": "...",
  "employee": {
    "id": "21053",
    "name": "...",
    "branchId": "03TS",
    "role": "Sales",
    "region": "BE"
  }
}
```

### Get Roles
```
GET /api/login/roles
Response: {
  "roles": [
    {
      "code": "Sales",
      "displayName": "พนักงานขาย",
      "thaiName": "พนักงานขาย"
    },
    ...
  ]
}
```

### Get Branches
```
GET /api/login/branches
Response: {
  "branches": [
    {
      "code": "03TS",
      "region": "BE",
      "displayName": "03TS (BE)"
    },
    ...
  ]
}
```

### Get My Approvers
```
GET /api/approver-info/my-approvers
Response: {
  "zone_manager": {
    "employee_id": "21053",
    "branch": "03TS",
    "role": "ZM",
    "position_id": "ZM_03TS"
  },
  "regional_manager": {
    "employee_id": "20785",
    "branch": "90HO",
    "role": "RM",
    "region": "BE",
    "position_id": "RM_BE"
  },
  "sales_director_manager": {
    "employee_id": "...",
    "role": "SDM",
    "position_id": "SDM_GLOBAL"
  }
}
```

## ⚙️ การตั้งค่า

### Environment Variables (backend/.env)
```env
# Employee Query API (UXP Auth Service)
EMP_QUERY_API_URL=http://localhost:52683/auth/get-user-by-role
EMP_QUERY_API_KEY=your_api_key_here  # ถ้า API ต้องการ auth
```

## 🔮 Special Price Request (Placeholder)

ตอนนี้เป็น Placeholder ตามที่ขอ:
- `GET /api/special-price-requests/pending/approvals` → คืน `[]`
- `POST /api/special-price-requests` → คืน `501 Not Implemented`
- Dashboard จะแสดงการ์ด "อนุมัติราคาพิเศษ" แต่จะมี 0 รายการ

### เมื่อต้องการพัฒนาต่อ
1. อ่าน `EMPLOYEE_MAPPER_USAGE.md` สำหรับตัวอย่างการใช้งาน
2. ใช้ `employee_position_mapper` เพื่อหาผู้อนุมัติ
3. บันทึก `employee_id` จริงลงฐานข้อมูล (ไม่ใช่แค่ position code)
4. รัน migration: `python backend/run_migration.py`
5. Implement ใน `special_price_request_router.py`

## 📚 เอกสารเพิ่มเติม

| ไฟล์ | คำอธิบาย |
|------|----------|
| `SOLUTION_SUMMARY.md` | สรุปการเปลี่ยนแปลงทั้งหมด (English) |
| `EMPLOYEE_MAPPER_USAGE.md` | ตัวอย่างการใช้งานแบบละเอียด (English) |
| `QUICK_START.md` | คู่มือเริ่มต้นใช้งาน (English) |
| `APPROVER_MAPPING_SOLUTION.md` | เอกสารทางเทคนิค (English) |
| `CURRENT_STATUS.md` | สถานะปัจจุบันของระบบ (English) |
| `สรุประบบ_LOGIN_และ_EMPLOYEE_MAPPER.md` | สรุประบบ (Thai) |
| `VERIFICATION_COMPLETE.md` | ผลการตรวจสอบระบบ (English) |
| `README_THAI.md` | ไฟล์นี้ (Thai) |

## ✅ Checklist

- [x] Manual Login ทำงานได้
- [x] Employee Mapper query API ได้
- [x] Approver Info API ทำงานได้
- [x] Special Price Placeholder ป้องกัน errors
- [x] Dashboard แสดงผลถูกต้อง
- [x] ไม่มี 404 errors
- [x] ไม่มี 405 errors
- [x] เอกสารครบถ้วน

## 🎉 สรุป

ระบบพร้อมใช้งานแล้ว! ทุกอย่างทำงานได้ตามที่ออกแบบไว้ ✅

หากมีคำถามหรือต้องการพัฒนาต่อ ให้อ่านเอกสารใน `EMPLOYEE_MAPPER_USAGE.md`
