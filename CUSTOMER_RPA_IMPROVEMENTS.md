# แนวทางการปรับปรุง: การส่งข้อมูลลูกค้าไปยัง RPA

---

## 1. สร้างรหัสลูกค้าใหม่ (High Priority)

### ปัญหา
เมื่อสร้างใบเสนอราคาสำหรับลูกค้าใหม่ที่ไม่มี code ในระบบ ระบบจะใช้ "N/A" ซึ่งอาจทำให้ RPA ล้มเหลว

### วิธีแก้ไข

**ไฟล์:** `backend/quotation.py`

```python
import uuid
from datetime import datetime

def generate_new_customer_code():
    """
    สร้างรหัสลูกค้าใหม่ในรูปแบบ: CUST-YYYYMMDD-XXXX
    เช่น: CUST-20260321-0001
    """
    today = datetime.now().strftime("%Y%m%d")
    random_suffix = str(uuid.uuid4().hex[:4]).upper()
    return f"CUST-{today}-{random_suffix}"

def create_quotation(payload: dict = Body(...)):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    employee = payload.get("employee") or {}
    customer = payload.get("customer") or {}
    branch = employee.get("branchId", "")

    raw_code = (customer.get("code") or "").strip()
    raw_name = (customer.get("name") or "").strip()

    # ✅ สร้างรหัสลูกค้าใหม่แทนการใช้ "N/A"
    if raw_code:
        cust_code = raw_code
    else:
        cust_code = generate_new_customer_code()
        logger.info(f"Generated new customer code: {cust_code}")

    if raw_name:
        cust_name = raw_name
    else:
        cust_name = "ลูกค้าใหม่"

    # ... rest of code ...
```

---

## 2. เพิ่ม Validation สำหรับข้อมูลลูกค้า (High Priority)

### ปัญหา
ไม่มีการตรวจสอบว่าข้อมูลลูกค้าครบถ้วนหรือไม่

### วิธีแก้ไข

**ไฟล์:** `backend/quotation.py`

```python
from pydantic import BaseModel, validator

class CustomerData(BaseModel):
    code: Optional[str] = None
    name: str  # ✅ Required
    phone: Optional[str] = None
    tax_no: Optional[str] = None
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('ชื่อลูกค้าไม่ได้ระบุ')
        return v.strip()

def validate_customer_data(customer: dict) -> CustomerData:
    """Validate customer data before creating quotation"""
    try:
        return CustomerData(**customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def create_quotation(payload: dict = Body(...)):
    # ✅ ตรวจสอบข้อมูลลูกค้าก่อน
    customer_data = validate_customer_data(payload.get("customer") or {})
    
    # ... rest of code ...
```

---

## 3. เพิ่ม Logging ใน Backend (Medium Priority)

### ปัญหา
ไม่มี Log ที่บันทึกว่าส่งข้อมูลลูกค้าไปยัง RPA หรือไม่

### วิธีแก้ไข

**ไฟล์:** `backend/quotation.py`

```python
import logging

logger = logging.getLogger(__name__)

def create_quotation(payload: dict = Body(...)):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    employee = payload.get("employee") or {}
    customer = payload.get("customer") or {}
    branch = employee.get("branchId", "")

    # ✅ Log ข้อมูลลูกค้า
    logger.info(f"Creating quotation for customer:")
    logger.info(f"  Code: {customer.get('code')}")
    logger.info(f"  Name: {customer.get('name')}")
    logger.info(f"  Phone: {customer.get('phone')}")
    logger.info(f"  Tax No: {customer.get('tax_no')}")

    raw_code = (customer.get("code") or "").strip()
    raw_name = (customer.get("name") or "").strip()

    cust_code = raw_code or "N/A"
    cust_name = raw_name or "ลูกค้าใหม่"

    quote_no = _generate_quote_no(branch)
    now = _now_iso()

    # ... rest of code ...

    conn.commit()
    conn.close()

    # ✅ Log ผลลัพธ์
    logger.info(f"Quotation created successfully:")
    logger.info(f"  Quote No: {quote_no}")
    logger.info(f"  Customer Code: {cust_code}")
    logger.info(f"  Customer Name: {cust_name}")

    return {
        "id": quote_no,
        "quoteNo": quote_no,
        "status": payload.get("status", "draft")
    }
```

---

## 4. ตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC (Medium Priority)

### ปัญหา
Frontend ส่ง customer_no ไปยัง RPA โดยไม่ตรวจสอบว่าลูกค้านี้มีอยู่ใน Dynamics 365 BC หรือไม่

### วิธีแก้ไข

**ไฟล์:** `backend/api/bc_client.py` (สร้างใหม่ หรือเพิ่มเข้าไป)

```python
import httpx
from config.config_external_api import CUSTOMER_API_URL, CUSTOMER_API_HEADERS

async def validate_customer_in_bc(customer_code: str) -> bool:
    """
    ตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC หรือไม่
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{CUSTOMER_API_URL}/customers/{customer_code}",
                headers=CUSTOMER_API_HEADERS
            )
            
            if response.status_code == 200:
                logger.info(f"Customer {customer_code} found in BC")
                return True
            elif response.status_code == 404:
                logger.warning(f"Customer {customer_code} not found in BC")
                return False
            else:
                logger.error(f"Error checking customer in BC: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error validating customer in BC: {e}")
        return False
```

**ไฟล์:** `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

```javascript
const handleSendToBC = async () => {
  try {
    setSendingToBC(true);

    const payload = buildQuotationPayload("complete");

    // ✅ ตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC ก่อน
    const customerCode = payload.customer.code;
    if (!customerCode) {
      throw new Error("ไม่ได้ระบุรหัสลูกค้า");
    }

    try {
      const validateRes = await fetch(`/api/bc/validate-customer/${customerCode}`);
      if (!validateRes.ok) {
        throw new Error(`ลูกค้า ${customerCode} ไม่มีอยู่ใน Dynamics 365 BC`);
      }
    } catch (err) {
      console.error("Customer validation failed:", err);
      alert(`ตรวจสอบลูกค้าไม่สำเร็จ: ${err.message}`);
      return;
    }

    // ... rest of code ...
  } catch (err) {
    console.error(err);
    alert(err.message || "ส่งข้อมูลเข้า Dynamics 365 ไม่สำเร็จ");
  } finally {
    setSendingToBC(false);
  }
};
```

---

## 5. เพิ่ม Retry Logic สำหรับ RPA Execution (Low Priority)

### ปัญหา
เมื่อ RPA Agent ล้มเหลว ไม่มีการ Retry

### วิธีแก้ไข

**ไฟล์:** `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

```javascript
const executeRPAWithRetry = async (rpaPayload, maxRetries = 3) => {
  const rpaUrls = [
    "http://127.0.0.1:8001/api/rpa/create-quote",
    "http://192.192.0.37:8001/api/rpa/create-quote",
    "http://192.168.1.185:8001/api/rpa/create-quote",
    "http://192.192.99.1:8001/api/rpa/create-quote"
  ];

  for (const url of rpaUrls) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`[RPA] Attempt ${attempt}/${maxRetries} to: ${url}`);
        
        const rpaRes = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(rpaPayload),
        });

        if (rpaRes.ok) {
          console.log(`[RPA] Successfully connected to: ${url}`);
          return rpaRes;
        } else {
          console.warn(`[RPA] Failed with status ${rpaRes.status} from: ${url}`);
        }
      } catch (err) {
        console.warn(`[RPA] Connection failed to: ${url}`, err);
        
        // Wait before retry
        if (attempt < maxRetries) {
          console.log(`[RPA] Waiting 2 seconds before retry...`);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    }
  }

  throw new Error("ไม่สามารถเชื่อมต่อ RPA Agent ได้ - โปรดตรวจสอบว่า RPA Agent เปิดอยู่หรือไม่");
};

const handleSendToBC = async () => {
  try {
    setSendingToBC(true);

    const payload = buildQuotationPayload("complete");

    // ... prepare rpaPayload ...

    // ✅ ใช้ executeRPAWithRetry แทน
    const rpaRes = await executeRPAWithRetry(rpaPayload);

    if (!rpaRes.ok) {
      throw new Error("ส่งข้อมูลเข้า Dynamics 365 ไม่สำเร็จ");
    }

    alert("ส่งข้อมูลเข้า Dynamics 365 ผ่าน RPA เรียบร้อยแล้ว");

    dispatch({ type: "RESET_QUOTE" });
    navigate("/confirmed-quotes");

  } catch (err) {
    console.error(err);
    alert(err.message || "ส่งข้อมูลเข้า Dynamics 365 ไม่สำเร็จ");
  } finally {
    setSendingToBC(false);
  }
};
```

---

## 6. เพิ่ม Error Handling ใน RPA Agent (Medium Priority)

### ปัญหา
RPA Agent ไม่มี Error Handling ที่ชัดเจนเมื่อลูกค้าไม่มีอยู่

### วิธีแก้ไข

**ไฟล์:** `rpa_agent/rpa_agent.py`

```python
def execute_create_sales_quote(quote_code, rpa_data=None):
    """
    Automate creating a sales quote with specific series code
    """
    print("[START] Starting RPA script for Sales Quote creation...")
    print(f"[INFO] Quote code: {quote_code}")
    
    # ✅ ตรวจสอบข้อมูลลูกค้า
    customer_no = rpa_data.get("customer_no", "") if rpa_data else ""
    if not customer_no or customer_no == "N/A":
        print("[ERROR] Invalid customer number: " + customer_no)
        raise ValueError(f"Invalid customer number: {customer_no}")
    
    # Convert the quote code
    target_series = convert_quote_code(quote_code)
    
    # ... rest of code ...
    
    try:
        # ... RPA automation code ...
        print("[SUCCESS] Sales Quote created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create Sales Quote: {e}")
        raise
```

---

## 7. เพิ่ม Database Constraint (Low Priority)

### ปัญหา
ไม่มี Unique Constraint สำหรับ CustomerCode ในตาราง Quote_Header

### วิธีแก้ไข

**SQL Migration:**

```sql
-- เพิ่ม Unique Constraint สำหรับ CustomerCode
ALTER TABLE Quote_Header
ADD CONSTRAINT UQ_Quote_Header_CustomerCode 
UNIQUE (CustomerCode);

-- เพิ่ม Index สำหรับ CustomerCode เพื่อเพิ่มความเร็ว
CREATE INDEX IX_Quote_Header_CustomerCode 
ON Quote_Header(CustomerCode);

-- เพิ่ม Index สำหรับ CustomerName
CREATE INDEX IX_Quote_Header_CustomerName 
ON Quote_Header(CustomerName);
```

---

## 📋 Checklist สำหรับการปรับปรุง

- [ ] สร้างรหัสลูกค้าใหม่ (High Priority)
- [ ] เพิ่ม Validation สำหรับข้อมูลลูกค้า (High Priority)
- [ ] เพิ่ม Logging ใน Backend (Medium Priority)
- [ ] ตรวจสอบว่าลูกค้ามีอยู่ใน Dynamics 365 BC (Medium Priority)
- [ ] เพิ่ม Retry Logic สำหรับ RPA Execution (Low Priority)
- [ ] เพิ่ม Error Handling ใน RPA Agent (Medium Priority)
- [ ] เพิ่ม Database Constraint (Low Priority)

---

## 🧪 Testing Plan

### Test Case 1: ลูกค้าเดิม (มี Code)
```
1. เลือกลูกค้าที่มี code ในระบบ
2. สร้างใบเสนอราคา
3. ส่งไปยัง RPA
4. ตรวจสอบว่า Quote ถูกสร้างใน Dynamics 365 BC
```

### Test Case 2: ลูกค้าใหม่ (ไม่มี Code)
```
1. ใส่ชื่อลูกค้าใหม่ (ไม่มี code)
2. สร้างใบเสนอราคา
3. ตรวจสอบว่าระบบสร้างรหัสลูกค้าใหม่
4. ส่งไปยัง RPA
5. ตรวจสอบว่า Quote ถูกสร้างใน Dynamics 365 BC
```

### Test Case 3: RPA Agent ไม่ตอบสนอง
```
1. ปิด RPA Agent
2. สร้างใบเสนอราคา
3. ส่งไปยัง RPA
4. ตรวจสอบว่าแสดง Error Message ที่ชัดเจน
```

### Test Case 4: ลูกค้าไม่มีอยู่ใน Dynamics 365 BC
```
1. ใส่รหัสลูกค้าที่ไม่มีอยู่ใน Dynamics 365 BC
2. สร้างใบเสนอราคา
3. ส่งไปยัง RPA
4. ตรวจสอบว่าแสดง Error Message ที่ชัดเจน
```

---

**ผู้เขียน:** Kiro AI Assistant  
**วันที่:** 21 มีนาคม 2026
