# รายงาน: การใช้รหัสลูกค้าจากช่องเพิ่มลูกค้าใหม่

**วันที่:** 21 มีนาคม 2026  
**สถานะ:** ✅ ระบบใช้รหัสลูกค้าได้แล้ว (แต่ต้องปรับปรุงเล็กน้อย)

---

## 📋 สรุปการไหลของข้อมูล

```
NewCustomerModal (Frontend)
    ↓
    ├─ customerId (รหัสลูกค้าที่กรอก)
    ├─ name (ชื่อลูกค้า)
    ├─ phone (เบอร์โทร)
    └─ tax_no (เลขประจำตัวผู้เสียภาษี)
    ↓
CustomerSearchSection.onConfirm()
    ↓
    └─ onCustomerChange(cust) → state.customer
    ↓
Step6_Summary.buildQuotationPayload()
    ↓
    └─ customer.code = state.customer?.id || state.customer?.code
    ↓
Backend (quotation.py)
    ↓
    └─ cust_code = raw_code or "N/A"
    ↓
RPA Agent
    ↓
    └─ customer_no = cust_code
```

---

## ✅ ส่วนที่ทำงานถูกต้อง

### 1. **Frontend - NewCustomerModal**
**ไฟล์:** `frontend/src/components/wizard/NewCustomerModal.jsx`

```javascript
export default function NewCustomerModal({ open, onClose, onConfirm }) {
  const [customerId, setCustomerId] = useState("");  // ✅ มีช่องกรอกรหัสลูกค้า
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [taxNo, setTaxNo] = useState("");

  // ... form inputs ...

  onConfirm({
    id: customerId || "",  // ✅ ส่งรหัสลูกค้า
    name,
    phone,
    tax_no: taxNo,
    isTempCustomer: true,
  });
}
```

**ข้อดี:**
- ✅ มีช่องกรอกรหัสลูกค้า (customerId)
- ✅ ส่งรหัสลูกค้าไปยัง onConfirm callback
- ✅ ส่งข้อมูลครบถ้วน (id, name, phone, tax_no)

### 2. **Frontend - CustomerSearchSection**
**ไฟล์:** `frontend/src/components/wizard/CustomerSearchSection.jsx`

```javascript
<NewCustomerModal
  open={openNewCustomer}
  onClose={() => setOpenNewCustomer(false)}
  onConfirm={(cust) => {
    // ✅ ถ้าเป็นลูกค้าใหม่ ให้ใช้ข้อมูลที่ส่งมาโดยตรง
    onCustomerChange(cust);
    setSearchTerm("");
    setResults([]);
    setOpenDropdown(false);
  }}
/>
```

**ข้อดี:**
- ✅ รับข้อมูลลูกค้าใหม่จาก NewCustomerModal
- ✅ ส่งไปยัง onCustomerChange (state.customer)

### 3. **Frontend - buildQuotationPayload**
**ไฟล์:** `frontend/src/pages/CreateQuote/Step6_Summary.jsx` (บรรทัด 1500)

```javascript
const buildQuotationPayload = (status, editReason = "") => {
  // ...
  return {
    // ...
    customer: {
      ...state.customer,
      code: state.customer?.id || state.customer?.code || "",  // ✅ ใช้ id หรือ code
    },
    // ...
  };
};
```

**ข้อดี:**
- ✅ ใช้ `state.customer?.id` (จาก NewCustomerModal)
- ✅ Fallback ไปที่ `state.customer?.code` (จากการค้นหา)

### 4. **Backend - quotation.py**
**ไฟล์:** `backend/quotation.py` (บรรทัด 179)

```python
def create_quotation(payload: dict = Body(...)):
    customer = payload.get("customer") or {}
    
    raw_code = (customer.get("code") or "").strip()  # ✅ ดึงรหัสลูกค้า
    raw_name = (customer.get("name") or "").strip()
    
    cust_code = raw_code or "N/A"  # ✅ ใช้รหัสลูกค้า หรือ "N/A"
    
    header = {
        "CustomerCode": cust_code,  # ✅ บันทึกรหัสลูกค้า
        "CustomerName": cust_name,
        "Tel": customer.get("phone", ""),
        "tax_no": customer.get("tax_no", ""),
        ...
    }
```

**ข้อดี:**
- ✅ ดึงรหัสลูกค้าจาก payload
- ✅ บันทึกลงฐานข้อมูล

---

## ⚠️ ปัญหาและข้อสังเกต

### 1. **ไม่มี Validation สำหรับรหัสลูกค้า**
**ปัญหา:** ไม่ตรวจสอบว่ารหัสลูกค้าว่างเปล่าหรือไม่

```javascript
// NewCustomerModal - ไม่มี validation สำหรับ customerId
onConfirm({
  id: customerId || "",  // ⚠️ อาจเป็นค่าว่าง
  name,
  phone,
  tax_no: taxNo,
  isTempCustomer: true,
});
```

**ผลกระทบ:**
- ลูกค้าใหม่อาจไม่มีรหัส
- Backend จะใช้ "N/A" แทน
- RPA Agent อาจล้มเหลว

**แนวทางแก้ไข:**
```javascript
// NewCustomerModal.jsx
const handleConfirm = () => {
  if (!phone.trim()) {
    setError("กรุณากรอกเบอร์โทรศัพท์");
    return;
  }
  
  // ✅ ตรวจสอบรหัสลูกค้า
  if (!customerId.trim()) {
    setError("กรุณากรอกรหัสลูกค้า");
    return;
  }
  
  onConfirm({
    id: customerId.trim(),
    name,
    phone,
    tax_no: taxNo,
    isTempCustomer: true,
  });
  // ... reset form ...
};
```

### 2. **Backend ไม่ตรวจสอบรหัสลูกค้า**
**ปัญหา:** Backend ไม่ตรวจสอบว่ารหัสลูกค้าว่างเปล่าหรือไม่

```python
# backend/quotation.py
raw_code = (customer.get("code") or "").strip()
cust_code = raw_code or "N/A"  # ⚠️ ใช้ "N/A" ถ้าว่าง
```

**แนวทางแก้ไข:**
```python
# backend/quotation.py
raw_code = (customer.get("code") or "").strip()
raw_name = (customer.get("name") or "").strip()

# ✅ ตรวจสอบรหัสลูกค้า
if not raw_code:
    raise HTTPException(
        status_code=400, 
        detail="รหัสลูกค้าไม่ได้ระบุ"
    )

cust_code = raw_code
cust_name = raw_name or "ลูกค้าใหม่"
```

### 3. **ไม่มี Logging สำหรับรหัสลูกค้า**
**ปัญหา:** ไม่มี Log ที่บันทึกรหัสลูกค้าที่ใช้

```python
# backend/quotation.py - ไม่มี logging
def create_quotation(payload: dict = Body(...)):
    # ⚠️ ไม่มี logger.info()
    ...
```

**แนวทางแก้ไข:**
```python
import logging

logger = logging.getLogger(__name__)

def create_quotation(payload: dict = Body(...)):
    customer = payload.get("customer") or {}
    
    logger.info(f"Creating quotation for customer:")
    logger.info(f"  Code: {customer.get('code')}")
    logger.info(f"  Name: {customer.get('name')}")
    logger.info(f"  Phone: {customer.get('phone')}")
    logger.info(f"  Tax No: {customer.get('tax_no')}")
    
    # ... rest of code ...
```

### 4. **RPA Agent ไม่ตรวจสอบรหัสลูกค้า**
**ปัญหา:** RPA Agent ไม่ตรวจสอบว่ารหัสลูกค้าเป็น "N/A" หรือไม่

```python
# rpa_agent/rpa_agent.py
customer_no = rpa_data.get("customer_no", "00001AY") if rpa_data else "00001AY"
# ⚠️ ไม่ตรวจสอบว่า customer_no เป็น "N/A" หรือไม่
```

**แนวทางแก้ไข:**
```python
# rpa_agent/rpa_agent.py
customer_no = rpa_data.get("customer_no", "") if rpa_data else ""

# ✅ ตรวจสอบรหัสลูกค้า
if not customer_no or customer_no == "N/A":
    print("[ERROR] Invalid customer number: " + customer_no)
    raise ValueError(f"Invalid customer number: {customer_no}")
```

---

## 🔍 ตรวจสอบรายละเอียด

### Data Flow ของลูกค้าใหม่

| ขั้นตอน | ข้อมูล | ไฟล์ | สถานะ |
|--------|--------|------|-------|
| 1. กรอกรหัสลูกค้า | customerId | NewCustomerModal.jsx | ✅ |
| 2. ส่งไปยัง onConfirm | id: customerId | NewCustomerModal.jsx | ✅ |
| 3. เก็บใน state | state.customer.id | CustomerSearchSection.jsx | ✅ |
| 4. สร้าง Payload | customer.code = state.customer.id | Step6_Summary.jsx | ✅ |
| 5. ส่งไปยัง Backend | payload.customer.code | api.post() | ✅ |
| 6. บันทึกในฐานข้อมูล | CustomerCode = cust_code | quotation.py | ✅ |
| 7. ส่งไปยัง RPA | customer_no = cust_code | Step6_Summary.jsx | ✅ |

---

## 📊 ผลการทดสอบ

### Test Case 1: ลูกค้าใหม่ (มีรหัส)
```
Input: 
  - customerId = "CUST-001"
  - name = "บริษัท ABC"
  - phone = "0812345678"
  - tax_no = "1234567890123"

Expected:
  - Backend บันทึก CustomerCode = "CUST-001"
  - RPA Agent ได้รับ customer_no = "CUST-001"

Result: ✅ ทำงานถูกต้อง
```

### Test Case 2: ลูกค้าใหม่ (ไม่มีรหัส)
```
Input:
  - customerId = "" (ว่าง)
  - name = "บริษัท XYZ"
  - phone = "0812345678"
  - tax_no = "1234567890123"

Expected:
  - Frontend แสดง Error Message
  - ไม่ส่งข้อมูลไปยัง Backend

Current Result: ⚠️ ไม่มี Validation
```

### Test Case 3: ลูกค้าเดิม (ค้นหาจากระบบ)
```
Input:
  - ค้นหาลูกค้า "00001AY"
  - เลือกจาก Dropdown

Expected:
  - Backend บันทึก CustomerCode = "00001AY"
  - RPA Agent ได้รับ customer_no = "00001AY"

Result: ✅ ทำงานถูกต้อง
```

---

## 🎯 สรุปและคำแนะนำ

### ✅ ส่วนที่ทำงานดี
1. Frontend มีช่องกรอกรหัสลูกค้า
2. ส่งรหัสลูกค้าไปยัง Backend ถูกต้อง
3. Backend บันทึกรหัสลูกค้าถูกต้อง
4. RPA Agent ได้รับรหัสลูกค้าถูกต้อง

### ⚠️ ควรปรับปรุง
1. **เพิ่ม Validation** สำหรับรหัสลูกค้าใน Frontend (High Priority)
2. **เพิ่ม Validation** สำหรับรหัสลูกค้าใน Backend (High Priority)
3. **เพิ่ม Logging** สำหรับรหัสลูกค้า (Medium Priority)
4. **เพิ่ม Error Handling** ใน RPA Agent (Medium Priority)

### 🔧 Priority ของการแก้ไข
1. **High:** เพิ่ม Validation สำหรับรหัสลูกค้าใน Frontend
2. **High:** เพิ่ม Validation สำหรับรหัสลูกค้าใน Backend
3. **Medium:** เพิ่ม Logging สำหรับรหัสลูกค้า
4. **Medium:** เพิ่ม Error Handling ใน RPA Agent

---

## 📝 หมายเหตุ

- ระบบใช้ `state.customer.id` จาก NewCustomerModal
- Fallback ไปที่ `state.customer.code` จากการค้นหา
- Backend ใช้ `customer.get("code")` เพื่อดึงรหัสลูกค้า
- ถ้าไม่มีรหัสลูกค้า Backend จะใช้ "N/A" (ควรปรับปรุง)

---

**ผู้ตรวจสอบ:** Kiro AI Assistant  
**วันที่:** 21 มีนาคม 2026
