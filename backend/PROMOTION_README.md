# ระบบจัดการโปรโมชั่น (Promotion Management System)

## ภาพรวม

ระบบนี้ช่วยให้ Manager สามารถสร้างและจัดการโปรโมชั่นสินค้าได้ โดยโปรโมชั่นจะแสดงอัตโนมัติในหน้าสรุปใบเสนอราคา (Step 6) เมื่อพนักงานเลือกสินค้าที่มีโปรโมชั่น

## การติดตั้ง

### 1. สร้างตารางในฐานข้อมูล

```bash
python backend/init_promotion_tables.py
```

สคริปต์นี้จะสร้างตาราง:
- `Promotion_Header` - เก็บข้อมูลหัวโปรโมชั่น
- `Promotion_Items` - เก็บรายการสินค้าในโปรโมชั่น

### 2. เริ่มใช้งาน Backend

Backend API จะพร้อมใช้งานอัตโนมัติเมื่อรัน FastAPI server

## โครงสร้างฐานข้อมูล

### Promotion_Header
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary Key (Auto Increment) |
| promotion_name | TEXT | ชื่อโปรโมชั่น |
| branch | TEXT | สาขา (ALL, BKK, CNX) |
| start_date | TEXT | วันที่เริ่มต้น (YYYY-MM-DD) |
| end_date | TEXT | วันที่สิ้นสุด (YYYY-MM-DD) |
| status | TEXT | สถานะ (active/inactive) |
| created_by | TEXT | ผู้สร้าง |
| created_at | TEXT | วันที่สร้าง |
| updated_at | TEXT | วันที่อัพเดท |

### Promotion_Items
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary Key (Auto Increment) |
| promotion_id | INTEGER | Foreign Key → Promotion_Header.id |
| sku | TEXT | รหัสสินค้า |
| promotion_text | TEXT | รายละเอียดโปรโมชั่น |
| created_at | TEXT | วันที่สร้าง |

## API Endpoints

### 1. สร้างโปรโมชั่นใหม่
```
POST /api/promotions/
```

Request Body:
```json
{
  "promotion_name": "แถมฟรี กาวแท่ง 2 หลอด",
  "branch": "ALL",
  "start_date": "2026-03-01",
  "end_date": "2026-03-31",
  "items": [
    {
      "sku": "G-001",
      "promotion_text": "แถมฟรี กาวแท่ง 2 หลอด"
    }
  ]
}
```

### 2. ดึงรายการโปรโมชั่นทั้งหมด
```
GET /api/promotions/
```

Query Parameters:
- `status` (optional): active/inactive
- `branch` (optional): ALL/BKK/CNX

### 3. ดึงโปรโมชั่นที่ active ตาม SKU
```
GET /api/promotions/active-by-skus?skus=G-001,A-002,C-003
```

Response:
```json
{
  "G-001": [
    {
      "promotion_id": 1,
      "promotion_name": "แถมฟรี กาวแท่ง 2 หลอด",
      "promotion_text": "แถมฟรี กาวแท่ง 2 หลอด",
      "branch": "ALL"
    }
  ]
}
```

### 4. อัพเดทสถานะโปรโมชั่น
```
PUT /api/promotions/{promotion_id}/status?status=inactive
```

### 5. ลบโปรโมชั่น
```
DELETE /api/promotions/{promotion_id}
```

## การใช้งาน

### สำหรับ Manager

1. เข้าหน้า Dashboard
2. คลิกที่ "จัดการโปรโมชั่น"
3. คลิก "เพิ่มโปรโมชั่น"
4. กรอกข้อมูล:
   - ชื่อโปรโมชั่น
   - สาขา
   - วันที่เริ่มต้น - สิ้นสุด
   - เพิ่มสินค้า (SKU + รายละเอียด)
5. บันทึก

### สำหรับพนักงานขาย

เมื่อสร้างใบเสนอราคาและเลือกสินค้าที่มีโปรโมชั่น:
1. ระบบจะแสดง Promotion Banner อัตโนมัติในหน้า Step 6
2. Banner จะแสดงรายละเอียดโปรโมชั่นทั้งหมดที่เกี่ยวข้อง
3. แยกตามประเภทสินค้า (กระจก, อลูมิเนียม, อื่นๆ)

## Component Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── wizard/
│   │       └── PromotionBanner.jsx    # แสดง Promotion
│   └── pages/
│       ├── PromotionManagement.jsx    # หน้าจัดการ Promotion
│       └── CreateQuote/
│           └── Step6_Summary.jsx      # แสดง Promotion Banner

backend/
├── promotion_router.py                # API Routes
├── init_promotion_tables.py           # สร้างตาราง
└── sql/
    └── create_promotion_tables.sql    # SQL Schema
```

## ตัวอย่างการใช้งาน

### ตัวอย่างที่ 1: โปรโมชั่นกระจก
```
ชื่อ: "แถมฟรี กาวแท่ง 2 หลอด"
สาขา: ALL
วันที่: 2026-03-01 ถึง 2026-03-31
สินค้า:
  - SKU: G-001 → "แถมฟรี กาวแท่ง 2 หลอด"
  - SKU: G-002 → "แถมฟรี กาวแท่ง 2 หลอด"
```

### ตัวอย่างที่ 2: โปรโมชั่นอลูมิเนียม
```
ชื่อ: "ซื้อ 10 ตัวต่อคุณ ส่อบขาว TOP"
สาขา: BKK
วันที่: 2026-03-01 ถึง 2026-03-15
สินค้า:
  - SKU: A-001 → "ซื้อ 10 ตัวต่อคุณ ส่อบขาว TOP"
```

## หมายเหตุ

- โปรโมชั่นจะแสดงเฉพาะที่มีสถานะ `active`
- ตรวจสอบวันที่ปัจจุบันอยู่ระหว่าง `start_date` และ `end_date`
- สามารถมีหลายโปรโมชั่นต่อ SKU เดียวกันได้
- การลบโปรโมชั่นจะลบรายการสินค้าทั้งหมดด้วย (CASCADE)

## Troubleshooting

### ไม่แสดง Promotion Banner
1. ตรวจสอบว่าโปรโมชั่นมีสถานะ `active`
2. ตรวจสอบวันที่ปัจจุบันอยู่ในช่วงโปรโมชั่น
3. ตรวจสอบ SKU ในตะกร้าตรงกับ SKU ในโปรโมชั่น
4. เปิด Console ดู error (F12)

### API Error
1. ตรวจสอบว่าตารางถูกสร้างแล้ว
2. ตรวจสอบ Backend logs
3. ตรวจสอบ Authentication token

## การพัฒนาต่อ

- [ ] เพิ่มการอัพโหลดรูปภาพโปรโมชั่น
- [ ] เพิ่มการแจ้งเตือนเมื่อโปรโมชั่นใกล้หมดอายุ
- [ ] รายงานสถิติการใช้โปรโมชั่น
- [ ] ส่งออกรายงาน Excel
