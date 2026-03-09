# ค่าขนส่งใน RPA - ขั้นตอนสุดท้าย

## ✅ การตั้งค่าที่ถูกต้อง

### สำหรับสินค้าทั่วไป (รวมค่าขนส่ง OT01-014):
- กด Tab **3 ครั้ง** หลังจาก Quantity เพื่อไปยัง Unit Price

### สำหรับกระจก (G):
- กด Tab 2 ครั้ง → Price per Sqft
- กด Tab 1 ครั้ง → Price per Sheet

## 📋 ลำดับขั้นตอนสำหรับค่าขนส่ง (OT01-014)

```
STEP 8: กรอก SKU
└─> "OT01-014"

STEP 9: กรอก Description
└─> "ค่าขนส่ง"

STEP 10: กรอก Quantity
├─> กด Tab 3 ครั้ง
└─> กรอก "1"

STEP 11: กรอก Unit Price
├─> กด Tab 3 ครั้ง
└─> กรอก "500.00"

เสร็จสิ้น (รายการสุดท้าย)
```

## 🔍 Log ที่ควรเห็น

```
[Item 3] Step 8: Adding Item Code: OT01-014
[OK] Item added in iframe 0

[Item 3] Step 9: Filling Description: ค่าขนส่ง
[WAIT] Pressing Tab 1 time...
[WAIT] Pressing Tab 3 more times...
[WAIT] Selecting all text (Ctrl+A)...
[WAIT] Deleting selected text...
[WAIT] Typing new description: ค่าขนส่ง
[OK] Description filled successfully

[Item 3] Step 10: Filling Quantity: 1
[WAIT] Pressing Tab 3 times...
[WAIT] Typing quantity: 1
[OK] Quantity filled successfully

[Item 3] Step 11: Filling price
[WAIT] Item does not start with 'G' - filling unit price...
[WAIT] Pressing Tab 3 times to reach unit price...
[WAIT] Typing unit price: 500.00
[OK] Unit price filled: 500.00 baht

[OK] All 3 items added successfully!
[OK] RPA script completed successfully!
```

## 🚀 วิธี Build

```bash
cd rpa_agent
.\build_agent.bat
```

## ✅ สรุป

- **รหัสสินค้า:** OT01-014
- **ตำแหน่ง:** รายการสุดท้ายเสมอ
- **Tab Count:** 3 ครั้ง (เหมือนสินค้าทั่วไป)
- **ทำงาน:** เหมือนสินค้าทั่วไปทุกประการ
