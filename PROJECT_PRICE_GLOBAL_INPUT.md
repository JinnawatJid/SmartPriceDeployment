# Project Price Management - Global Price Input Feature

## Overview
ระบบการกรอกราคาและจำนวนแบบรวม (Global Input) สำหรับการเพิ่มสินค้าหลายรายการพร้อมกัน

## การทำงาน

### 1. เลือกสินค้าตาม Filter
- เลือก Category (Glass, Aluminum, Sealant, ฯลฯ)
- เลือก Filter เพิ่มเติม (Brand, Group, SubGroup, Color, Thickness)
- ระบบจะแสดงรายการ SKU ที่ตรงกับเงื่อนไข

### 2. กรอกราคาและจำนวนครั้งเดียว
หลังจากเลือกสินค้าเสร็จแล้ว จะมีช่องกรอกข้อมูลดังนี้:

**ช่องกรอกข้อมูล:**
- Brand (ไม่บังคับ) - เช่น AGC, Guardian
- ความหนา (ไม่บังคับ) - เช่น 6mm, 8mm
- หน่วย (ไม่บังคับ) - เช่น ตารางฟุต, ชิ้น, เมตร
- **ราคา (บังคับ)** - ราคาต่อหน่วย
- จำนวน (ไม่บังคับ) - จำนวนที่ตกลง

**หมายเหตุ:**
- ราคาและจำนวนที่กรอกจะถูกใช้กับสินค้าทั้งหมดที่เลือก
- ต้องกรอกราคาก่อนจึงจะสามารถเพิ่มสินค้าได้
- จำนวนเป็นข้อมูลเสริม (optional)

### 3. เพิ่มสินค้าเข้าโครงการ
- กดปุ่ม "เพิ่มสินค้า (X รายการ)"
- ระบบจะเพิ่มสินค้าทั้งหมดพร้อมราคาและจำนวนที่กรอก
- สินค้าจะปรากฏในตารางรายการสินค้าของโครงการ

## ตัวอย่างการใช้งาน

### กรณีที่ 1: กระจกใส AGC 6mm
```
Filter:
- Category: Glass
- Brand: AGC
- Thickness: 6mm

Global Input:
- Brand: AGC
- ความหนา: 6mm
- หน่วย: ตารางฟุต
- ราคา: 20.25
- จำนวน: 115000

ผลลัพธ์: สินค้าทั้งหมดที่ตรงกับ Filter จะได้ราคา 20.25 บาท/ตารางฟุต จำนวน 115,000 ตรฟ.
```

### กรณีที่ 2: อลูมิเนียมหลายรุ่น
```
Filter:
- Category: Aluminum
- Brand: YKK

Global Input:
- Brand: YKK
- หน่วย: เมตร
- ราคา: 150.00
- จำนวน: 5000

ผลลัพธ์: อลูมิเนียม YKK ทุกรุ่นที่ตรงกับ Filter จะได้ราคา 150 บาท/เมตร จำนวน 5,000 เมตร
```

## State Variables

```javascript
// Global input states
const [globalPrice, setGlobalPrice] = useState('');        // ราคาสำหรับทุกรายการ
const [globalQuantity, setGlobalQuantity] = useState('');  // จำนวนสำหรับทุกรายการ
const [globalBrand, setGlobalBrand] = useState('');        // Brand (optional)
const [globalThickness, setGlobalThickness] = useState(''); // ความหนา (optional)
const [globalUnit, setGlobalUnit] = useState('');          // หน่วย (optional)
```

## Key Functions

### addItemsFromFilter()
```javascript
const addItemsFromFilter = () => {
  // 1. ตรวจสอบว่ามี SKU ที่ตรงกับเงื่อนไข
  if (matchedSkus.length === 0) {
    alert('ไม่พบสินค้าที่ตรงกับเงื่อนไข');
    return;
  }

  // 2. ตรวจสอบว่ากรอกราคาแล้ว (required)
  if (!globalPrice || parseFloat(globalPrice) <= 0) {
    alert('กรุณากรอกราคา');
    return;
  }

  // 3. สร้างรายการสินค้าใหม่ด้วยราคาและจำนวนเดียวกัน
  const newItems = matchedSkus.map(sku => ({
    sku: sku.sku,
    product_name: sku.description || '',
    brand: globalBrand || '',
    thickness: globalThickness || '',
    unit: globalUnit || '',
    price: globalPrice,              // ใช้ราคาเดียวกันทั้งหมด
    quantity: globalQuantity || '',  // ใช้จำนวนเดียวกันทั้งหมด
  }));

  // 4. เพิ่มเข้า items list
  setItems([...items, ...newItems]);
  
  // 5. ปิด modal และ reset ค่า
  setShowFilterModal(false);
  resetFilterAndGlobalInputs();
};
```

## UI Components

### Global Input Section
```jsx
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
  <p className="text-blue-800 font-semibold mb-3">
    📝 กรอกราคาและจำนวนสำหรับสินค้าทั้งหมด
  </p>
  
  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
    {/* Brand, Thickness, Unit, Price*, Quantity */}
  </div>

  <p className="text-xs text-gray-600 mt-3">
    💡 ราคาและจำนวนนี้จะถูกใช้กับสินค้าทั้งหมด {matchedSkus.length} รายการ
  </p>
</div>
```

### Add Button with Validation
```jsx
<button
  type="button"
  onClick={addItemsFromFilter}
  disabled={matchedSkus.length === 0 || !globalPrice || parseFloat(globalPrice) <= 0}
  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
             disabled:opacity-50 disabled:cursor-not-allowed"
>
  เพิ่มสินค้า {matchedSkus.length > 0 && `(${matchedSkus.length} รายการ)`}
</button>
```

## Validation Rules

1. **ราคา (Price)** - บังคับกรอก
   - ต้องมีค่ามากกว่า 0
   - ปุ่มเพิ่มสินค้าจะ disabled ถ้าไม่กรอกราคา

2. **จำนวน (Quantity)** - ไม่บังคับ
   - สามารถเว้นว่างได้
   - ถ้ากรอกจะถูกบันทึกเป็น decimal

3. **Brand, Thickness, Unit** - ไม่บังคับ
   - เป็นข้อมูลเสริมเพื่อความชัดเจน
   - ถ้าไม่กรอกจะเป็นค่าว่าง

## Benefits

✅ **ประหยัดเวลา** - ไม่ต้องกรอกราคาทีละรายการ
✅ **ลดข้อผิดพลาด** - ราคาเดียวกันสำหรับทุกรายการ
✅ **ยืดหยุ่น** - สามารถเลือกสินค้าด้วย Filter ที่หลากหลาย
✅ **ชัดเจน** - แสดงจำนวน SKU ที่จะเพิ่มก่อนกดยืนยัน

## Related Files

- `frontend/src/pages/ProjectPriceManagement.jsx` - Main component
- `backend/project_price_router.py` - API endpoints
- `PROJECT_PRICE_README.md` - Complete documentation
