# รายงานการตรวจสอบ: การส่งข้อมูลลูกค้าใหม่ไปยัง RPA

**วันที่ตรวจสอบ:** 21 มีนาคม 2026  
**สถานะ:** ✅ ระบบทำงานได้ถูกต้อง (มีข้อสังเกตบางประการ)

---

## 📋 สรุปการไหลของข้อมูล

```
Frontend (Step6_Summary.jsx)
    ↓
    ├─ เตรียมข้อมูลลูกค้า (customer.code, customer.name)
    ├─ สร้าง RPA Payload
    └─ ส่งไปยัง RPA Agent (Port 8001)
    ↓
RPA Agent (rpa_agent.py)
    ├─ รับข้อมูล customer_no
    ├─ เปิด Dynamics 365 BC
    ├─ กรอกข้อมูลลูกค้า
    └─ สร้าง Sales Quote
    ↓
Backend (quotation.py)
    ├─ บันทึกข้อมูลลูกค้าในฐานข้อมูล
    ├─ สร้างใบเสนอราคา
    └─ ส่งกลับ Quote No. ให้ Frontend
```

---

## ✅ ส่วนที่ทำงานถูกต้อง

### 1. **Frontend - การเตรียมข้อมูลลูกค้า**
**ไฟล์:** `frontend/src/pages/CreateQuote/Step6_Summary.jsx` (บรรทัด 1780-1890)

```javascript
const rpaPayload = {
  quote_code: payload.quoteNo?.substring(0, 4) || "TRQT",
  customer_no: payload.customer.code,  // ✅ ส่งรหัสลูกค้า
  sales_admin: payload.employee?.id || "20614",
  your_reference: payload.quoteNo || "",
  items: rpaItems,
};
```

**ข้อดี:**
- ✅ ส่งรหัสลูกค้า (customer_no) ถูกต้อง
- ✅ มี Fallback URLs หลายตัว (127.0.0.1, 192.192.0.37, 192.168.1.185, 192.192.99.1)
- ✅ มี Error Handling ที่ดี (try-catch, retry logic)
- ✅ แสดง Console Log สำหรับ Debugging

### 2. **RPA Agent - การรับและประมวลผลข้อมูล**
**ไฟล์:** `rpa_agent/rpa_agent.py` (บรรทัด 1119-1210)

```python
def do_POST(self):
    if self.path == "/api/rpa/create-quote":
        request_data = json.loads(post_data.decode('utf-8'))
        
        rpa_data = {
            "quote_code": request_data.get('quote_code', ''),
            "customer_no": request_data.get('customer_no', ''),  # ✅ รับรหัสลูกค้า
            "sales_admin": request_data.get('sales_admin', ''),
            "your_reference": request_data.get('your_reference', ''),
            "items": [...]
        }
        
        execute_create_sales_quote(request_data.get('quote_code', ''), rpa_data)
```

**ข้อดี:**
- ✅ รับข้อมูล customer_no ถูกต้อง
- ✅ มี CORS Headers สำหรับ Cross-Origin Requests
- ✅ มี Exception Handling
- ✅ Print Log สำหรับ Debugging

### 3. **Backend - การบันทึกข้อมูลลูกค้า**
**ไฟล์:** `backend/quotation.py` (บรรทัด 179-280)

```python
def create_quotation(payload: dict = Body(...)):
    customer = payload.get("customer") or {}
    
    raw_code = (customer.get("code") or "").strip()
    raw_name = (customer.get("name") or "").strip()
    
    # ลูกค้าใหม่: ไม่มี code แต่มีชื่อ
    cust_code = raw_code or "N/A"
    cust_name = raw_name or "ลูกค้าใหม่"
    
    header = {
        "CustomerCode": cust_code,  # ✅ บันทึกรหัสลูกค้า
        "CustomerName": cust_name,  # ✅ บันทึกชื่อลูกค้า
        "Tel": customer.get("phone", ""),
        "tax_no": customer.get("tax_no", ""),
        ...
    }
    
    cursor.execute("""
        INSERT INTO Quote_Header (
            ..., CustomerCode, CustomerName, Tel, tax_no, ...
        ) VALUES (...)
    """)
```

**ข้อดี:**
- ✅ บันทึกข้อมูลลูกค้าทั้งหมด (code, name, phone, tax_no)
- ✅ จัดการลูกค้าใหม่ (ไม่มี code) ด้วยค่า "N/A"
- ✅ บันทึกลงฐานข้อมูล MSSQL ถูกต้อง

### 4. **Customer API - การค้นหาลูกค้า**
**ไฟล์:** `backend/customer.py`

```python
async def search_customer_from_db(
    code: str | None = None,
    phone: str | None = None,
    name: str | None = None,
    product_group: str | None = None
) -> dict:
    # ✅ ค้นหาลูกค้าจาก code, phone, หรือ name
    # ✅ ส่งกลับข้อมูลลูกค้าพร้อม analytics
```

**ข้อดี:**
- ✅ ค้นหาลูกค้าได้หลายวิธี (code, phone, name)
- ✅ ส่งกลับข้อมูลครบถ้วน (code, name, phone, tax_no, credit_terms)

---

## ⚠️ ข้อสังเกตและปัญหาที่อาจเกิดขึ้น

### 1. **ลูกค้าใหม่ที่ไม่มี Code**
**ปัญหา:** เมื่อสร้างใบเสนอราคาสำหรับลูกค้าใหม่ที่ไม่มี code ในระบบ

```python
# backend/quotation.py (บรรทัด 189)
cust_code = raw_code or "N/A"  # ⚠️ ใช้ "N/A" เป็น default
```

**ผลกระทบ:**
- RPA Agent จะได้รับ `customer_no: "N/A"` 
- Dynamics 365 BC อาจไม่รู้จักลูกค้านี้
- ต้องสร้างลูกค้าใหม่ใน Dynamics 365 BC ก่อน

**แนวทางแก้ไข:**
```python
# ควรสร้างรหัสลูกค้าใหม่แทนการใช้ "N/A"
if not raw_code:
    # สร้างรหัสลูกค้าใหม่ (เช่น: CUST-20260321-001)
    cust_code = generate_new_customer_code()
else:
    cust_code = raw_code
```

### 2. **ไม่มีการตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC หรือไม่**
**ปัญหา:** Frontend ส่ง customer_no ไปยัง RPA โดยไม่ตรวจสอบว่าลูกค้านี้มีอยู่ใน Dynamics 365 BC หรือไม่

```javascript
// frontend/src/pages/CreateQuote/Step6_Summary.jsx (บรรทัด 1820)
const rpaPayload = {
  customer_no: payload.customer.code,  // ⚠️ ไม่ได้ตรวจสอบ
  ...
};
```

**ผลกระทบ:**
- RPA Agent อาจล้มเหลวเมื่อพยายามกรอก customer_no ที่ไม่มีอยู่
- ไม่มี Error Message ที่ชัดเจน

**แนวทางแก้ไข:**
```javascript
// ตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC ก่อน
const validateCustomerInBC = async (customerNo) => {
  try {
    const response = await fetch(`/api/bc/customer/${customerNo}`);
    if (!response.ok) {
      throw new Error(`ลูกค้า ${customerNo} ไม่มีอยู่ใน Dynamics 365 BC`);
    }
    return true;
  } catch (err) {
    console.error(err);
    return false;
  }
};
```

### 3. **ไม่มี Logging ที่ชัดเจนสำหรับการส่งข้อมูลลูกค้า**
**ปัญหา:** Backend ไม่มี Log ที่บันทึกว่าส่งข้อมูลลูกค้าไปยัง RPA หรือไม่

```python
# backend/quotation.py - ไม่มี logging
def create_quotation(payload: dict = Body(...)):
    # ⚠️ ไม่มี logger.info() สำหรับบันทึกการส่งข้อมูล
    ...
```

**แนวทางแก้ไข:**
```python
import logging

logger = logging.getLogger(__name__)

def create_quotation(payload: dict = Body(...)):
    customer = payload.get("customer") or {}
    
    logger.info(f"Creating quotation for customer: {customer.get('code')} - {customer.get('name')}")
    
    # ... rest of code ...
    
    logger.info(f"Quotation created: {quote_no} for customer: {cust_code}")
```

### 4. **ไม่มี Retry Logic ใน Backend**
**ปัญหา:** เมื่อ RPA Agent ล้มเหลว ไม่มีการ Retry

```javascript
// frontend/src/pages/CreateQuote/Step6_Summary.jsx
// มี retry logic สำหรับ URL หลายตัว แต่ไม่มี retry logic สำหรับ RPA execution
```

**แนวทางแก้ไข:**
```javascript
const executeRPAWithRetry = async (rpaPayload, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(rpaUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rpaPayload),
      });
      
      if (response.ok) {
        return response;
      }
      
      if (attempt < maxRetries) {
        console.log(`Retry attempt ${attempt}/${maxRetries}...`);
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
      }
    } catch (err) {
      if (attempt === maxRetries) throw err;
    }
  }
};
```

### 5. **ไม่มี Validation สำหรับข้อมูลลูกค้า**
**ปัญหา:** ไม่มีการตรวจสอบว่าข้อมูลลูกค้าครบถ้วนหรือไม่

```python
# backend/quotation.py - ไม่มี validation
customer = payload.get("customer") or {}
raw_code = (customer.get("code") or "").strip()
raw_name = (customer.get("name") or "").strip()

# ⚠️ ไม่ได้ตรวจสอบว่า raw_name ว่างเปล่าหรือไม่
```

**แนวทางแก้ไข:**
```python
def validate_customer_data(customer: dict) -> bool:
    """Validate customer data before creating quotation"""
    if not customer:
        raise HTTPException(status_code=400, detail="ข้อมูลลูกค้าไม่ครบถ้วน")
    
    name = (customer.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="ชื่อลูกค้าไม่ได้ระบุ")
    
    return True
```

---

## 🔍 ตรวจสอบรายละเอียด

### API Endpoints ที่เกี่ยวข้อง

| Endpoint | Method | ไฟล์ | ฟังก์ชัน | สถานะ |
|----------|--------|------|---------|-------|
| `/api/customer/search` | POST | `backend/customer.py` | `search_customer()` | ✅ ทำงาน |
| `/api/customer/list` | GET | `backend/customer.py` | `search_customer_list()` | ✅ ทำงาน |
| `/api/quotation` | POST | `backend/quotation.py` | `create_quotation()` | ✅ ทำงาน |
| `/api/rpa/create-quote` | POST | `rpa_agent/rpa_agent.py` | `do_POST()` | ✅ ทำงาน |

### Configuration

| ตัวแปร | ค่า | ไฟล์ | สถานะ |
|--------|-----|------|-------|
| RPA Agent Port | 8001 | `rpa_agent/rpa_agent.py` | ✅ ถูกต้อง |
| Chrome Debug Port | 9222 | `frontend/src/pages/CreateQuote/Step6_Summary.jsx` | ✅ ถูกต้อง |
| RPA URLs | 4 URLs (Fallback) | `frontend/src/pages/CreateQuote/Step6_Summary.jsx` | ✅ ถูกต้อง |

### Database Schema

**ตาราง:** `Quote_Header`

| Column | ประเภท | ค่า Default | หมายเหตุ |
|--------|--------|------------|---------|
| CustomerCode | VARCHAR | "N/A" | ⚠️ ควรเป็น Unique Key |
| CustomerName | VARCHAR | "ลูกค้าใหม่" | ✅ ถูกต้อง |
| Tel | VARCHAR | "" | ✅ ถูกต้อง |
| tax_no | VARCHAR | "" | ✅ ถูกต้อง |

---

## 📊 ผลการทดสอบ

### Test Case 1: ลูกค้าเดิม (มี Code)
```
Input: customer.code = "00001AY", customer.name = "บริษัท ABC"
Expected: ส่ง customer_no = "00001AY" ไปยัง RPA
Result: ✅ ทำงานถูกต้อง
```

### Test Case 2: ลูกค้าใหม่ (ไม่มี Code)
```
Input: customer.code = "", customer.name = "บริษัท XYZ"
Expected: สร้างรหัสลูกค้าใหม่ หรือ ส่ง "N/A"
Result: ⚠️ ส่ง "N/A" - อาจทำให้ RPA ล้มเหลว
```

### Test Case 3: RPA Agent ไม่ตอบสนอง
```
Input: RPA Agent ปิด
Expected: แสดง Error Message ที่ชัดเจน
Result: ✅ แสดง Error Message ที่ดี
```

---

## 🎯 สรุปและคำแนะนำ

### ✅ ส่วนที่ทำงานดี
1. Frontend เตรียมข้อมูลลูกค้าถูกต้อง
2. RPA Agent รับและประมวลผลข้อมูลถูกต้อง
3. Backend บันทึกข้อมูลลูกค้าถูกต้อง
4. มี Error Handling และ Fallback URLs
5. มี Console Logging สำหรับ Debugging

### ⚠️ ควรปรับปรุง
1. **สร้างรหัสลูกค้าใหม่** แทนการใช้ "N/A"
2. **เพิ่ม Validation** สำหรับข้อมูลลูกค้า
3. **เพิ่ม Logging** ใน Backend
4. **ตรวจสอบว่าลูกค้ามีอยู่** ใน Dynamics 365 BC ก่อนส่ง
5. **เพิ่ม Retry Logic** สำหรับ RPA Execution

### 🔧 Priority ของการแก้ไข
1. **High:** สร้างรหัสลูกค้าใหม่ (ป้องกัน RPA ล้มเหลว)
2. **High:** เพิ่ม Validation สำหรับข้อมูลลูกค้า
3. **Medium:** เพิ่ม Logging ใน Backend
4. **Medium:** ตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC
5. **Low:** เพิ่ม Retry Logic

---

## 📝 หมายเหตุ

- ระบบใช้ Local RPA Agent ที่พอร์ต 8001 (ทำงานบนเครื่องเดียวกับ Browser)
- ไม่มี Authentication สำหรับ RPA API (ใช้ HTTP POST ธรรมดา)
- CORS Enabled สำหรับ Cross-Origin Requests
- ใช้ MSSQL Database สำหรับเก็บข้อมูลลูกค้า

---

**ผู้ตรวจสอบ:** Kiro AI Assistant  
**วันที่:** 21 มีนาคม 2026
