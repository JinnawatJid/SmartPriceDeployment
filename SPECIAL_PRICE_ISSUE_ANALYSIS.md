# Special Price Issue Analysis - Unit Conversion Problem

## ปัญหาที่พบ

เมื่อแก้ราคากระจกและอลูมิเนียมในระบบ special price request มีปัญหาการแปลงหน่วยไม่ตรงกัน:

### 1. **ปัญหากระจก (Glass - Category G)**
- **Frontend (PriceEditModal.jsx)**: ผู้ใช้แก้ไขราคาต่อ **ตารางฟุต (บาท/ตร.ฟุต)**
- **Backend (pricing_router.py)**: ระบบคำนวณราคาต่อ **แผ่น (บาท/แผ่น)** โดยคูณ sqft_sheet
- **ปัญหา**: เมื่อสร้าง special price request ส่งค่า `requested_price` ที่เป็นราคาต่อแผ่น แต่ระบบเปรียบเทียบกับ `normal_price` ที่เป็นราคาต่อตารางฟุต

### 2. **ปัญหาอลูมิเนียม (Aluminium - Category A)**
- **Frontend (PriceEditModal.jsx)**: ผู้ใช้แก้ไขราคาต่อ **กิโลกรัม (บาท/กก.)**
- **Backend (pricing_router.py)**: ระบบคำนวณราคาต่อ **เส้น (บาท/เส้น)** โดยคูณ product_weight
- **ปัญหา**: เมื่อสร้าง special price request ส่งค่า `requested_price` ที่เป็นราคาต่อเส้น แต่ระบบเปรียบเทียบกับ `normal_price` ที่เป็นราคาต่อกิโลกรัม

## Flow ปัจจุบัน

### Frontend (PriceEditModal.jsx)
```
ผู้ใช้แก้ไข:
- Glass: ราคาต่อตารางฟุต (pricePerSqft)
- Aluminium: ราคาต่อกิโลกรัม (pricePerKg)

คำนวณและบันทึก:
- Glass: unitPrice = pricePerSqft × sqft_sheet (ราคาต่อแผ่น)
- Aluminium: unitPrice = pricePerKg × weight (ราคาต่อเส้น)
```

### Backend (special_price_request_router.py)
```
รับค่า requested_price จาก frontend:
- Glass: ราคาต่อแผ่น
- Aluminium: ราคาต่อเส้น

เปรียบเทียบกับ normal_price:
- Glass: ราคาต่อตารางฟุต (W1 × sqft_sheet)
- Aluminium: ราคาต่อกิโลกรัม (W1 × weight)

❌ หน่วยไม่ตรงกัน!
```

## วิธีแก้ไข

### Option 1: ปรับ Backend ให้รับราคาต่อหน่วยพื้นฐาน (แนะนำ)
ให้ frontend ส่งราคาต่อหน่วยพื้นฐาน (ตร.ฟุต/กก.) แทนราคาต่อแผ่น/เส้น

**ข้อดี:**
- ลดความสับสน
- เปรียบเทียบราคาได้ถูกต้อง
- ไม่ต้องแปลงหน่วยหลายครั้ง

**ข้อเสีย:**
- ต้องแก้ไข frontend logic

### Option 2: ปรับ Frontend ให้ส่งราคาต่อหน่วยพื้นฐาน
ให้ frontend คำนวณและส่งราคาต่อหน่วยพื้นฐาน (ตร.ฟุต/กก.) ไปยัง backend

**ข้อดี:**
- Backend logic ไม่ต้องเปลี่ยน

**ข้อเสีย:**
- Frontend ต้องแปลงหน่วยเพิ่มเติม

### Option 3: ปรับทั้ง Frontend และ Backend
ให้ส่งข้อมูลหน่วยพื้นฐานพร้อมกับราคา เพื่อให้ backend สามารถแปลงได้ถูกต้อง

## ข้อมูลที่ต้องส่ง

### สำหรับกระจก (Glass)
```javascript
{
  sku: "G001",
  quantity: 10,
  normal_price: 100,           // ราคาต่อตารางฟุต (บาท/ตร.ฟุต)
  requested_price: 95,         // ราคาต่อตารางฟุต (บาท/ตร.ฟุต) ⭐ ต้องเป็นหน่วยเดียวกัน
  sqft_sheet: 5,               // ตารางฟุตต่อแผ่น
  unit: "ตร.ฟุต"
}
```

### สำหรับอลูมิเนียม (Aluminium)
```javascript
{
  sku: "A001",
  quantity: 20,
  normal_price: 50,            // ราคาต่อกิโลกรัม (บาท/กก.)
  requested_price: 48,         // ราคาต่อกิโลกรัม (บาท/กก.) ⭐ ต้องเป็นหน่วยเดียวกัน
  product_weight: 2.5,         // กิโลกรัมต่อเส้น
  unit: "กก."
}
```

## ไฟล์ที่ต้องแก้ไข

1. **frontend/src/components/wizard/PriceEditModal.jsx**
   - แก้ไข `handleSave()` ให้ส่งราคาต่อหน่วยพื้นฐาน

2. **backend/special_price_request_router.py**
   - ปรับ `create_special_price_request()` ให้รับและเก็บราคาต่อหน่วยพื้นฐาน
   - ปรับ `approve_special_price_request()` ให้แปลงราคาถูกต้องเมื่อบันทึกลงระบบ

3. **backend/pricing_router.py** (ถ้าจำเป็น)
   - ตรวจสอบว่า `normal_price` ถูกคำนวณจากหน่วยพื้นฐานหรือไม่
