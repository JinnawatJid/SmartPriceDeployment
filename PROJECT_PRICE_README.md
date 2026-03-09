# Project Price Management System

## ภาพรวม
ระบบจัดการราคาโครงการ (Project Price Management) เป็นระบบที่ให้ Manager บันทึกราคาพิเศษสำหรับโครงการต่างๆ โดยราคาเหล่านี้จะมีผลเฉพาะกับลูกค้าและสินค้าที่ระบุ และมีระยะเวลาการใช้งานที่กำหนด

---

## โครงสร้างฐานข้อมูล

### 1. Project_Price_Header
ตารางหลักเก็บข้อมูลโครงการ

| Column | Type | Description |
|--------|------|-------------|
| project_id | INT (PK, Identity) | รหัสโครงการ (Auto increment) |
| project_code | NVARCHAR(50) | รหัสโครงการที่กำหนดเอง (เช่น PROJ-2026-001) |
| project_name | NVARCHAR(255) | ชื่อโครงการ |
| customer_code | NVARCHAR(50) | รหัสลูกค้า |
| customer_name | NVARCHAR(255) | ชื่อลูกค้า |
| branch_code | NVARCHAR(10) | รหัสสาขาที่ขอราคา |
| price_start_date | DATE | วันที่เริ่มใช้ราคา |
| price_end_date | DATE | วันที่สิ้นสุดการใช้ราคา |
| request_by | NVARCHAR(100) | ชื่อผู้ขอ |
| request_date | DATETIME | วันที่ขอ |
| status | NVARCHAR(20) | สถานะ (active/expired/cancel) |
| remark | NVARCHAR(500) | หมายเหตุ |
| created_at | DATETIME | วันที่สร้าง |
| updated_at | DATETIME | วันที่แก้ไขล่าสุด |

### 2. Project_Price_Line
ตารางรายการสินค้าในโครงการ

| Column | Type | Description |
|--------|------|-------------|
| line_id | INT (PK, Identity) | รหัสรายการ |
| project_id | INT (FK) | รหัสโครงการ (อ้างอิง Project_Price_Header) |
| sku | NVARCHAR(50) | รหัสสินค้า |
| product_name | NVARCHAR(255) | ชื่อสินค้า |
| brand | NVARCHAR(100) | ยี่ห้อ (เช่น AGC, Guardian) |
| thickness | NVARCHAR(50) | ความหนา (เช่น 5mm, 6mm) |
| unit | NVARCHAR(50) | หน่วย (ตารางฟุต, ชิ้น, เมตร) |
| price | DECIMAL(18,4) | ราคาโครงการ |
| quantity | DECIMAL(18,2) | จำนวนที่ตกลง (optional) |

---

## Backend API Endpoints

### Base URL: `/api/project-prices`

### 1. สร้างราคาโครงการใหม่
```
POST /api/project-prices/
```

**Request Body:**
```json
{
  "project_code": "PROJ-2026-001",
  "project_name": "โครงการคอนโด ABC",
  "customer_code": "08015AY",
  "customer_name": "บริษัท ABC จำกัด",
  "branch_code": "001",
  "price_start_date": "2026-03-01",
  "price_end_date": "2026-12-31",
  "request_by": "คุณสมชาย",
  "request_date": "2026-02-25",
  "remark": "โครงการพิเศษ",
  "items": [
    {
      "sku": "G010101010101",
      "product_name": "กระจกใส AGC 6mm",
      "brand": "AGC",
      "thickness": "6mm",
      "unit": "ตารางฟุต",
      "price": 20.25,
      "quantity": 115000
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "project_id": 1
}
```

### 2. ดึงรายการราคาโครงการทั้งหมด
```
GET /api/project-prices/
GET /api/project-prices/?status=active
GET /api/project-prices/?branch=001
```

**Response:**
```json
[
  {
    "project_id": 1,
    "project_code": "PROJ-2026-001",
    "project_name": "โครงการคอนโด ABC",
    "customer_code": "08015AY",
    "customer_name": "บริษัท ABC จำกัด",
    "branch_code": "001",
    "price_start_date": "2026-03-01",
    "price_end_date": "2026-12-31",
    "request_by": "คุณสมชาย",
    "request_date": "2026-02-25",
    "status": "active",
    "remark": "โครงการพิเศษ",
    "created_at": "2026-02-25 10:30:00",
    "items": [
      {
        "line_id": 1,
        "project_id": 1,
        "sku": "G010101010101",
        "product_name": "กระจกใส AGC 6mm",
        "brand": "AGC",
        "thickness": "6mm",
        "unit": "ตารางฟุต",
        "price": 20.25,
        "quantity": 115000
      }
    ]
  }
]
```

### 3. ดึงราคาโครงการตามลูกค้าและ SKU
```
GET /api/project-prices/active-by-customer-sku?customerCode=08015AY&sku=G010101010101
```

**Response:**
```json
[
  {
    "project_id": 1,
    "project_code": "PROJ-2026-001",
    "project_name": "โครงการคอนโด ABC",
    "sku": "G010101010101",
    "product_name": "กระจกใส AGC 6mm",
    "brand": "AGC",
    "thickness": "6mm",
    "unit": "ตารางฟุต",
    "price": 20.25,
    "quantity": 115000
  }
]
```

### 4. อัพเดทสถานะโครงการ
```
PUT /api/project-prices/{project_id}/status?status=expired
```

**Response:**
```json
{
  "success": true
}
```

### 5. ลบโครงการ
```
DELETE /api/project-prices/{project_id}
```

**Response:**
```json
{
  "success": true
}
```

---

## Frontend Components

### 1. ProjectPriceManagement.jsx
หน้าจัดการราคาโครงการหลัก

**Location:** `frontend/src/pages/ProjectPriceManagement.jsx`

**Features:**
- แสดงรายการโครงการทั้งหมด
- ฟอร์มเพิ่มโครงการใหม่
- แก้ไขสถานะโครงการ (active/expired/cancel)
- ลบโครงการ
- แสดงรายละเอียดสินค้าในแต่ละโครงการ

**Form Fields:**
- รหัสโครงการ (required)
- ชื่อโครงการ
- รหัสลูกค้า
- ชื่อลูกค้า
- สาขา (dropdown)
- วันที่เริ่มใช้ราคา (required)
- วันที่สิ้นสุด (required)
- ผู้ขอ
- วันที่ขอ (default: วันนี้)
- หมายเหตุ

**Item Fields:**
- SKU
- ชื่อสินค้า
- Brand
- ความหนา
- หน่วย
- ราคา (required)
- จำนวน

**การเพิ่มสินค้า:**
1. **เพิ่มทีละรายการ** - กรอกข้อมูลสินค้าทีละรายการ
2. **เลือกตาม Filter** - เลือกสินค้าหลายรายการพร้อมกันตาม Filter:
   - เลือกประเภทสินค้า (Categories)
   - เลือก Brand, Group, SubGroup, Color, Thickness
   - ระบบจะแสดงจำนวนสินค้าที่ตรงกับเงื่อนไข
   - คลิก "เพิ่มสินค้า" เพื่อเพิ่มทั้งหมดพร้อมกัน

### 2. UpdatePrice.jsx
หน้าหลักที่มี Tabs

**Tabs:**
1. อัปเดตราคา (Update Price) - อัปโหลด Excel
2. จัดการโปรโมชั่น - ระบบโปรโมชั่น
3. ราคาโครงการ - ระบบราคาโครงการ (ใหม่)

---

## การใช้งาน

### สำหรับ Manager

1. **เข้าหน้า Update Price**
   - ไปที่เมนู "Update Data (Manager)"

2. **เลือก Tab "ราคาโครงการ"**
   - คลิกที่ Tab "ราคาโครงการ"

3. **เพิ่มโครงการใหม่**
   - คลิกปุ่ม "เพิ่มราคาโครงการ"
   - กรอกข้อมูลโครงการ:
     - รหัสโครงการ (เช่น PROJ-2026-001)
     - ชื่อโครงการ
     - รหัสลูกค้า และชื่อลูกค้า
     - เลือกสาขา
     - กำหนดวันที่เริ่มต้น-สิ้นสุด
     - ระบุผู้ขอและวันที่ขอ

4. **เพิ่มรายการสินค้า**
   - **วิธีที่ 1: เพิ่มทีละรายการ**
     - คลิก "เพิ่มทีละรายการ"
     - กรอกข้อมูลสินค้า:
       - SKU (เช่น G010101010101)
       - ชื่อสินค้า (เช่น กระจกใส AGC 6mm)
       - Brand (เช่น AGC)
       - ความหนา (เช่น 6mm)
       - หน่วย (เช่น ตารางฟุต)
       - ราคา (เช่น 20.25)
       - จำนวน (เช่น 115000)
   
   - **วิธีที่ 2: เลือกตาม Filter (แนะนำสำหรับสินค้าหลายรายการ)**
     - คลิก "เลือกตาม Filter"
     - เลือกประเภทสินค้า (Glass, Aluminum, ฯลฯ)
     - เลือก Filter เพิ่มเติม (Brand, Group, Color, Thickness)
     - ระบบจะแสดงรายการสินค้าที่ตรงกับเงื่อนไข
     - **กรอกราคาและจำนวนเพียงครั้งเดียว** (ใช้กับสินค้าทั้งหมด)
       - Brand (เช่น AGC)
       - ความหนา (เช่น 6mm)
       - หน่วย (เช่น ตารางฟุต)
       - ราคา (required, เช่น 20.25)
       - จำนวน (optional, เช่น 115000)
     - คลิก "เพิ่มสินค้า" เพื่อเพิ่มทั้งหมดพร้อมกัน

5. **บันทึก**
   - คลิก "บันทึก"
   - ระบบจะบันทึกข้อมูลและแสดงในรายการ

6. **จัดการโครงการ**
   - เปลี่ยนสถานะ: เลือกจาก dropdown (Active/Expired/Cancel)
   - ลบโครงการ: คลิกไอคอนถังขยะ

---

## ตัวอย่างการใช้งาน

### กรณีที่ 1: โครงการคอนโด
```
รหัสโครงการ: CONDO-2026-001
ชื่อโครงการ: โครงการคอนโด Luxury Tower
ลูกค้า: 08015AY - บริษัท ABC จำกัด
สาขา: 001
ระยะเวลา: 01/03/2026 - 31/12/2026
ผู้ขอ: คุณสมชาย
วันที่ขอ: 25/02/2026

รายการสินค้า:
1. G010101010101 - กระจกใส AGC 6mm - 20.25 บาท/ตรฟ (115,000 ตรฟ)
2. A020202020202 - อลูมิเนียม YKK - 150.00 บาท/เมตร (50,000 เมตร)
```

### กรณีที่ 2: โครงการโรงงาน
```
รหัสโครงการ: FACTORY-2026-002
ชื่อโครงการ: โครงการโรงงาน XYZ
ลูกค้า: 12345AB - บริษัท XYZ จำกัด
สาขา: 002
ระยะเวลา: 15/03/2026 - 30/06/2026
ผู้ขอ: คุณสมหญิง
วันที่ขอ: 01/03/2026

รายการสินค้า:
1. G020303030303 - กระจกสะท้อนแสง Guardian 8mm - 35.50 บาท/ตรฟ (80,000 ตรฟ)
```

---

## Integration กับระบบอื่น

### 1. ระบบใบเสนอราคา (Quote System)
เมื่อสร้างใบเสนอราคา ระบบจะตรวจสอบว่ามีราคาโครงการหรือไม่:

```javascript
// ตรวจสอบราคาโครงการ
const projectPrice = await api.get('/api/project-prices/active-by-customer-sku', {
  params: {
    customerCode: customer.code,
    sku: item.sku
  }
});

if (projectPrice.data.length > 0) {
  // ใช้ราคาโครงการ
  item.price = projectPrice.data[0].price;
  item.priceSource = 'project';
  item.projectCode = projectPrice.data[0].project_code;
}
```

### 2. ระบบคำนวณราคา (Pricing Engine)
ลำดับความสำคัญของราคา:
1. ราคาโครงการ (Project Price) - สูงสุด
2. ราคาพิเศษที่อนุมัติแล้ว (Approved Special Price)
3. ราคาโปรโมชั่น (Promotion Price)
4. ราคาตามระดับลูกค้า (Customer Level Price)
5. ราคามาตรฐาน (Standard Price)

---

## สิทธิ์การใช้งาน

- **Manager เท่านั้น** สามารถ:
  - เพิ่มราคาโครงการ
  - แก้ไขสถานะโครงการ
  - ลบโครงการ

- **Sales** สามารถ:
  - ดูรายการโครงการ
  - ระบบจะใช้ราคาโครงการอัตโนมัติเมื่อสร้างใบเสนอราคา

---

## หมายเหตุสำคัญ

1. **ราคาโครงการมีผลเฉพาะ:**
   - ลูกค้าที่ระบุ (customer_code)
   - สินค้าที่ระบุ (SKU)
   - ช่วงเวลาที่กำหนด (price_start_date - price_end_date)

2. **สถานะโครงการ:**
   - `active` - ใช้งานได้
   - `expired` - หมดอายุ
   - `cancel` - ยกเลิก

3. **การระบุสินค้า:**
   - สามารถระบุแบบกว้างๆ เช่น "กระจกใส AGC 6mm"
   - หรือระบุ SKU เฉพาะเจาะจง
   - ระบบจะจับคู่ตาม SKU ที่ระบุ

4. **จำนวน (Quantity):**
   - เป็น optional field
   - ใช้สำหรับอ้างอิงจำนวนที่ตกลงกับลูกค้า
   - ไม่มีผลต่อการคำนวณราคา

---

## Files ที่เกี่ยวข้อง

### Backend
- `backend/project_price_router.py` - API endpoints
- `backend/main.py` - Router registration

### Frontend
- `frontend/src/pages/ProjectPriceManagement.jsx` - หน้าจัดการโครงการ
- `frontend/src/pages/UpdatePrice.jsx` - หน้าหลักที่มี tabs

### Database
- `Project_Price_Header` - ตารางหลัก
- `Project_Price_Line` - ตารางรายการสินค้า

---

## TODO / Future Enhancements

1. ✅ เพิ่มการเลือกสินค้าแบบ Filter (เสร็จแล้ว)
2. เพิ่มการค้นหาและ Filter โครงการ
3. เพิ่มการ Export รายงานโครงการ
4. เพิ่มการแจ้งเตือนเมื่อโครงการใกล้หมดอายุ
5. เพิ่มการ Copy โครงการเดิมมาสร้างใหม่
6. เพิ่มการอัปโหลด Excel สำหรับรายการสินค้าจำนวนมาก
7. เพิ่มประวัติการแก้ไข (Audit Log)
8. เพิ่มการแสดงราคาโครงการในหน้าสร้างใบเสนอราคา
9. เพิ่มการเปรียบเทียบราคาโครงการกับราคามาตรฐาน
10. เพิ่มการ Bulk Edit ราคาสินค้าในโครงการ
