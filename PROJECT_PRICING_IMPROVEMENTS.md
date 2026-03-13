# การปรับปรุงระบบราคาโครงการ (Project Pricing)

## ปัญหาที่แก้ไข

1. **การนำราคาโครงการมาใช้**: เมื่อเลือกโครงการ หากเลือก SKU ที่มีการขอราคาไว้ ต้องนำราคาโครงการนั้นมาใช้
2. **การเปลี่ยนโครงการ**: หากมีการกดเปลี่ยนโครงการ หากสินค้านั้นไม่ได้ถูกขอในโครงการนั้น จะต้องเปลี่ยนมาใช้ราคาปกติ
3. **การแสดงสถานะราคา**: ต้องแสดงให้ผู้ใช้เห็นว่าใช้ราคาจากแหล่งไหน (โครงการ/ประวัติ/ระบบ/แก้ไขแล้ว)

## การแก้ไขที่ทำ

### 1. Frontend (Step6_Summary.jsx)

#### ปรับปรุง useEffect สำหรับการเปลี่ยนโครงการ:
```javascript
// โหลดราคาโครงการเมื่อเลือกโครงการ และคำนวณราคาใหม่
useEffect(() => {
  // ถ้าไม่มีสินค้าในตะกร้า ไม่ต้องคำนวณ
  if (!state.cart || state.cart.length === 0) {
    return;
  }

  // ถ้าไม่มีลูกค้า ไม่ต้องคำนวณ
  const customerCode = getCustomerCode(state.customer);
  if (!customerCode || customerCode.toUpperCase() === "N/A") {
    return;
  }

  const recalculateWithProject = async () => {
    // คำนวณราคาใหม่พร้อมส่ง project_id
    const calcRes = await api.post("/api/pricing/calculate", {
      customerData: {
        // ... ข้อมูลลูกค้า
        project_id: selectedProject, // 🔥 ส่ง project_id ที่เลือก (null ถ้าไม่เลือก)
      },
      // ... ข้อมูลอื่นๆ
    });
    
    // อัพเดท calculation state
    setCalculation({
      cart: items,
      totals: { /* ... */ },
      loading: false,
      error: null,
    });
  };

  recalculateWithProject();
}, [selectedProject, state.customer, state.cart]);
```

**ประโยชน์:**
- เมื่อเปลี่ยนโครงการ จะคำนวณราคาใหม่ทันที
- หากสินค้าไม่อยู่ในโครงการใหม่ จะใช้ราคาระบบ/ประวัติ
- หากสินค้าอยู่ในโครงการใหม่ จะใช้ราคาโครงการ

### 2. Frontend (CartItemRow.jsx)

#### เพิ่มการแสดงสถานะราคา:
```javascript
// ตรวจสอบว่าใช้ราคาโครงการหรือไม่
const isProjectPrice = calculatedItem?.priceSource === 'project' || calculatedItem?.price_source === 'project';

// แสดง badge สถานะราคา
{isProjectPrice && (
  <span className="text-[9px] text-green-600 font-semibold bg-green-50 px-1 py-0.5 rounded">
    🏗️ ราคาโครงการ
  </span>
)}

{(calculatedItem?.priceSource === 'history' || calculatedItem?.price_source === 'history') && (
  <span className="text-[9px] text-orange-600 font-semibold bg-orange-50 px-1 py-0.5 rounded">
    📋 ราคาประวัติ
  </span>
)}

{(calculatedItem?.priceSource === 'system' || calculatedItem?.price_source === 'system') && (
  <span className="text-[9px] text-blue-600 font-semibold bg-blue-50 px-1 py-0.5 rounded">
    💻 ราคาระบบ
  </span>
)}

{item.priceSource === 'manual' && (
  <span className="text-[9px] text-purple-600 font-semibold bg-purple-50 px-1 py-0.5 rounded">
    ✏️ แก้ไขแล้ว
  </span>
)}
```

**ประโยชน์:**
- ผู้ใช้เห็นได้ชัดว่าราคาแต่ละรายการมาจากแหล่งไหน
- ช่วยในการตรวจสอบและยืนยันความถูกต้องของราคา

### 3. Backend (pricing_router.py)

#### ระบบมีการตรวจสอบราคาโครงการอยู่แล้ว:
```python
# ตรวจสอบราคาโครงการก่อน (มีลำดับความสำคัญสูงสุด)
project_id = req.customerData.get("project_id")

if project_id:
    for idx, row in df_price.iterrows():
        sku = row["sku"]
        
        # ดึงราคาโครงการที่ active
        sql = """
        SELECT TOP (1) ph.project_code, ph.project_name, pl.price
        FROM Project_Price_Header ph
        JOIN Project_Price_Line pl ON ph.project_id = pl.project_id
        WHERE ph.project_id = ? AND pl.sku = ?
        """
        
        result = cursor.fetchone()
        
        if result:
            # ใช้ราคาโครงการทันที
            df_price.at[idx, "NewPrice"] = project_price
            df_price.at[idx, "price_source"] = "project"
        else:
            # ไม่พบในโครงการ → ใช้ราคาระบบ/ประวัติ
            print(f"ไม่พบในโครงการนี้ → ใช้ราคาระบบ/ประวัติ")
```

**ประโยชน์:**
- ลำดับความสำคัญ: ราคาโครงการ > ราคาประวัติ > ราคาระบบ
- เมื่อเปลี่ยนโครงการ สินค้าที่ไม่อยู่ในโครงการใหม่จะใช้ราคาระบบ/ประวัติ

## ลำดับการทำงาน

1. **ผู้ใช้เลือกโครงการ** → `selectedProject` เปลี่ยน
2. **useEffect ถูก trigger** → เรียก API `/api/pricing/calculate` พร้อม `project_id`
3. **Backend ตรวจสอบราคาโครงการ** → หา SKU ในโครงการที่เลือก
4. **ถ้าพบ** → ใช้ราคาโครงการ (`price_source: "project"`)
5. **ถ้าไม่พบ** → ใช้ราคาประวัติ/ระบบ (`price_source: "history"/"system"`)
6. **Frontend แสดงผล** → แสดง badge สถานะราคาตาม `price_source`

## การทดสอบ

1. **เลือกโครงการที่มี SKU ในตะกร้า** → ควรเห็น badge "🏗️ ราคาโครงการ"
2. **เปลี่ยนเป็นโครงการที่ไม่มี SKU นั้น** → ควรเห็น badge "📋 ราคาประวัติ" หรือ "💻 ราคาระบบ"
3. **ไม่เลือกโครงการ** → ควรใช้ราคาประวัติ/ระบบ
4. **แก้ไขราคาด้วยตนเอง** → ควรเห็น badge "✏️ แก้ไขแล้ว"

## ข้อดี

1. **ใช้งานง่าย**: ผู้ใช้แค่เลือกโครงการ ระบบจะคำนวณราคาให้อัตโนมัติ
2. **โปร่งใส**: แสดงที่มาของราคาแต่ละรายการอย่างชัดเจน
3. **ยืดหยุ่น**: สามารถเปลี่ยนโครงการได้ตลอดเวลา ราคาจะอัพเดททันที
4. **ถูกต้อง**: ใช้ลำดับความสำคัญที่ถูกต้อง (โครงการ > ประวัติ > ระบบ)

## ไฟล์ที่แก้ไข

1. `frontend/src/pages/CreateQuote/Step6_Summary.jsx` - ปรับปรุง useEffect สำหรับการเปลี่ยนโครงการ
2. `frontend/src/components/wizard/CartItemRow.jsx` - เพิ่มการแสดงสถานะราคา
3. `backend/pricing_router.py` - มีระบบตรวจสอบราคาโครงการอยู่แล้ว (ไม่ต้องแก้ไข)

## สรุป

การปรับปรุงนี้ทำให้ระบบราคาโครงการทำงานได้อย่างสมบูรณ์ ผู้ใช้สามารถเลือกโครงการและเห็นการเปลี่ยนแปลงราคาทันที พร้อมทั้งทราบที่มาของราคาแต่ละรายการอย่างชัดเจน