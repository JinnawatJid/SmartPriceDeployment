# แนวทางการปรับปรุง: การใช้รหัสลูกค้าจากช่องเพิ่มลูกค้าใหม่

---

## 1. เพิ่ม Validation สำหรับรหัสลูกค้าใน Frontend (High Priority)

### ปัญหา
ไม่มีการตรวจสอบว่ารหัสลูกค้าว่างเปล่าหรือไม่

### วิธีแก้ไข

**ไฟล์:** `frontend/src/components/wizard/NewCustomerModal.jsx`

```javascript
import React, { useState } from "react";

export default function NewCustomerModal({ open, onClose, onConfirm }) {
  const [customerId, setCustomerId] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [taxNo, setTaxNo] = useState("");
  const [error, setError] = useState("");

  if (!open) return null;

  const handleConfirm = () => {
    // ✅ ตรวจสอบรหัสลูกค้า
    if (!customerId.trim()) {
      setError("กรุณากรอกรหัสลูกค้า");
      return;
    }

    // ✅ ตรวจสอบชื่อลูกค้า
    if (!name.trim()) {
      setError("กรุณากรอกชื่อลูกค้า");
      return;
    }

    // ✅ ตรวจสอบเบอร์โทรศัพท์
    if (!phone.trim()) {
      setError("กรุณากรอกเบอร์โทรศัพท์");
      return;
    }

    // ✅ ตรวจสอบรูปแบบรหัสลูกค้า (ตัวอักษร, ตัวเลข, ขีดกลาง เท่านั้น)
    const customerIdRegex = /^[A-Za-z0-9\-]+$/;
    if (!customerIdRegex.test(customerId.trim())) {
      setError("รหัสลูกค้าต้องเป็นตัวอักษร ตัวเลข หรือขีดกลางเท่านั้น");
      return;
    }

    // ✅ ตรวจสอบความยาวรหัสลูกค้า (ไม่เกิน 20 ตัวอักษร)
    if (customerId.trim().length > 20) {
      setError("รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร");
      return;
    }

    onConfirm({
      id: customerId.trim(),
      name: name.trim(),
      phone: phone.trim(),
      tax_no: taxNo.trim(),
      isTempCustomer: true,
    });

    // Reset form
    setCustomerId("");
    setName("");
    setPhone("");
    setTaxNo("");
    setError("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h3 className="text-lg font-bold text-gray-800 mb-4">เพิ่มลูกค้าใหม่</h3>

        <div className="space-y-3">
          {/* ✅ รหัสลูกค้า - Required */}
          <div>
            <input
              type="text"
              placeholder="รหัสลูกค้า (Customer ID) *"
              value={customerId}
              onChange={(e) => {
                setCustomerId(e.target.value);
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm ${
                error && !customerId.trim() ? "border-red-500" : "border-gray-300"
              }`}
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              ตัวอักษร ตัวเลข หรือขีดกลาง (สูงสุด 20 ตัวอักษร)
            </p>
          </div>

          {/* ✅ ชื่อลูกค้า - Required */}
          <div>
            <input
              type="text"
              placeholder="ชื่อลูกค้า *"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm ${
                error && !name.trim() ? "border-red-500" : "border-gray-300"
              }`}
              required
            />
          </div>

          {/* ✅ เบอร์โทรศัพท์ - Required */}
          <div>
            <input
              type="text"
              placeholder="เบอร์โทรศัพท์ *"
              value={phone}
              onChange={(e) => {
                setPhone(e.target.value);
                if (error) setError("");
              }}
              className={`w-full rounded-lg border p-3 text-sm ${
                error && !phone.trim() ? "border-red-500" : "border-gray-300"
              }`}
              required
            />
          </div>

          {/* เลขประจำตัวผู้เสียภาษี - Optional */}
          <input
            type="text"
            placeholder="เลขประจำตัวผู้เสียภาษี (Tax No.)"
            value={taxNo}
            onChange={(e) => {
              setTaxNo(e.target.value);
              if (error) setError("");
            }}
            className="w-full rounded-lg border border-gray-300 p-3 text-sm"
          />

          {/* ✅ Error Message */}
          {error && (
            <p className="text-sm text-red-500 bg-red-50 p-2 rounded-lg">
              {error}
            </p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-md border hover:bg-gray-100"
          >
            ยกเลิก
          </button>

          <button
            onClick={handleConfirm}
            className="px-4 py-2 text-sm rounded-md bg-blue-600 text-white hover:bg-blue-700"
          >
            บันทึก
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 2. เพิ่ม Validation สำหรับรหัสลูกค้าใน Backend (High Priority)

### ปัญหา
Backend ไม่ตรวจสอบว่ารหัสลูกค้าว่างเปล่าหรือไม่

### วิธีแก้ไข

**ไฟล์:** `backend/quotation.py`

```python
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, validator
from config.db_mssql import get_mssql_conn
import logging

logger = logging.getLogger(__name__)

# ✅ Pydantic Model สำหรับ Validation
class CustomerData(BaseModel):
    code: str  # Required
    name: str  # Required
    phone: str  # Required
    tax_no: Optional[str] = None
    
    @validator('code')
    def code_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('รหัสลูกค้าไม่ได้ระบุ')
        if len(v.strip()) > 20:
            raise ValueError('รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร')
        return v.strip()
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('ชื่อลูกค้าไม่ได้ระบุ')
        return v.strip()
    
    @validator('phone')
    def phone_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('เบอร์โทรศัพท์ไม่ได้ระบุ')
        return v.strip()

def validate_customer_data(customer: dict) -> CustomerData:
    """Validate customer data before creating quotation"""
    try:
        return CustomerData(**customer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def create_quotation(payload: dict = Body(...)):
    conn = get_mssql_conn()
    cursor = conn.cursor()

    employee = payload.get("employee") or {}
    customer = payload.get("customer") or {}
    branch = employee.get("branchId", "")

    # ✅ ตรวจสอบข้อมูลลูกค้า
    try:
        customer_data = validate_customer_data(customer)
    except HTTPException as e:
        logger.error(f"Customer validation failed: {e.detail}")
        raise

    # ✅ Log ข้อมูลลูกค้า
    logger.info(f"Creating quotation for customer:")
    logger.info(f"  Code: {customer_data.code}")
    logger.info(f"  Name: {customer_data.name}")
    logger.info(f"  Phone: {customer_data.phone}")
    logger.info(f"  Tax No: {customer_data.tax_no}")

    raw_code = customer_data.code
    raw_name = customer_data.name

    cust_code = raw_code
    cust_name = raw_name

    quote_no = _generate_quote_no(branch)
    now = _now_iso()

    header = {
        "QuoteNo": quote_no,
        "Status": payload.get("status", "draft"),
        "CustomerCode": cust_code,  # ✅ ใช้รหัสลูกค้าที่ตรวจสอบแล้ว
        "SalesID": employee.get("id", ""),
        "SalesName": employee.get("name", ""),
        "CreateDate": now,
        "ExpireDate": payload.get("expireDate", ""),
        "ApproveDate": now,
        "BranchCode": branch,
        "PaymentTerm": payload.get("paymentTerm", ""),
        "CreditTerm": payload.get("creditTerm", ""),
        "ShippingMethod": payload.get("deliveryType", ""),
        "ShippingCost": payload.get("totals", {}).get("shippingRaw", 0),
        "DiscountAmount": payload.get("discount", 0),
        "SubtotalAmount": payload.get("totals", {}).get("exVat", 0),
        "TotalAmount": payload.get("totals", {}).get("grandTotal", 0),
        "NeedsTax": "Y" if payload.get("needTaxInvoice") else "N",
        "Remark": (payload.get("remark", "") or "")[:255],
        "Remark_Shipping": (payload.get("note", "") or "")[:255],
        "LastUpdate": now,
        "CustomerName": cust_name,
        "Tel": customer_data.phone,
        "tax_no": customer_data.tax_no or "",
        "ShippingCustomerPay": payload.get("totals", {}).get("shippingCustomerPay", 0),
        "Pre_Order": payload.get("pre_order", 0),
        "Required_Delivery_Date": payload.get("required_delivery_date") or None,
    }

    cursor.execute("""
        INSERT INTO Quote_Header (
            QuoteNo, Status, CustomerCode, SalesID, SalesName,
            CreateDate, ExpireDate, ApproveDate, BranchCode,
            PaymentTerm, CreditTerm, ShippingMethod, ShippingCost,
            DiscountAmount, SubtotalAmount, TotalAmount,
            NeedsTax, Remark, Remark_Shipping, LastUpdate,
            CustomerName, Tel, tax_no, ShippingCustomerPay, Pre_Order, Required_Delivery_Date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, tuple(header.values()))

    cart = payload.get("cart", [])
    if not cart:
        raise HTTPException(400, "ต้องมีสินค้าอย่างน้อย 1 รายการ")

    lines_to_excel = []

    for item in cart:
        line = _build_line_from_payload(item)

        cursor.execute("""
            INSERT INTO Quote_Line (
                QuoteID, ItemCode, ItemName, Category,
                Unit, Quantity, Price_System, UnitPrice, TotalPrice,
                IsGlassCut, CutInfoJson, Remark,
                Sqft_Sheet, VariantCode, ProductWeight
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            quote_no,
            line["ItemCode"], line["ItemName"], line["Category"],
            line["Unit"], line["Quantity"], line["Price_System"], line["UnitPrice"],
            line["TotalPrice"], line["IsGlassCut"],
            line["CutInfoJson"], line["Remark"],
            line["Sqft_Sheet"], line["VariantCode"], line["ProductWeight"],
        ))

        lines_to_excel.append(line)

    conn.commit()
    conn.close()

    # ✅ Log ผลลัพธ์
    logger.info(f"Quotation created successfully:")
    logger.info(f"  Quote No: {quote_no}")
    logger.info(f"  Customer Code: {cust_code}")
    logger.info(f"  Customer Name: {cust_name}")

    _append_header_to_excel(header)
    _append_lines_to_excel(quote_no, lines_to_excel)

    return {
        "id": quote_no,
        "quoteNo": quote_no,
        "status": payload.get("status", "draft")
    }
```

---

## 3. เพิ่ม Error Handling ใน RPA Agent (Medium Priority)

### ปัญหา
RPA Agent ไม่ตรวจสอบว่ารหัสลูกค้าเป็น "N/A" หรือไม่

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
    
    if not customer_no:
        print("[ERROR] Customer number is empty")
        raise ValueError("Customer number is empty")
    
    if customer_no == "N/A":
        print("[ERROR] Customer number is N/A (invalid)")
        raise ValueError("Customer number is N/A - please provide a valid customer code")
    
    # Convert the quote code
    target_series = convert_quote_code(quote_code)
    
    # ✅ Log ข้อมูลลูกค้า
    print(f"[INFO] Customer No: {customer_no}")
    print(f"[INFO] Sales Admin: {rpa_data.get('sales_admin', '')}")
    print(f"[INFO] Your Reference: {rpa_data.get('your_reference', '')}")
    
    # ... rest of RPA automation code ...
    
    try:
        # ... RPA automation code ...
        print("[SUCCESS] Sales Quote created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create Sales Quote: {e}")
        raise
```

---

## 4. เพิ่ม Logging ใน Frontend (Medium Priority)

### วิธีแก้ไข

**ไฟล์:** `frontend/src/pages/CreateQuote/Step6_Summary.jsx`

```javascript
const handleSendToBC = async () => {
  try {
    setSendingToBC(true);

    const payload = buildQuotationPayload("complete");

    // ✅ Log ข้อมูลลูกค้า
    console.log("[Customer] Code:", payload.customer.code);
    console.log("[Customer] Name:", payload.customer.name);
    console.log("[Customer] Phone:", payload.customer.phone);
    console.log("[Customer] Tax No:", payload.customer.tax_no);

    // ⭐ เตรียมข้อมูลสำหรับ RPA Local Agent
    const rpaItems = payload.cart.map((it) => {
      // ... item mapping code ...
    });

    const rpaPayload = {
      quote_code: payload.quoteNo?.substring(0, 4) || "TRQT",
      customer_no: payload.customer.code,  // ✅ ใช้รหัสลูกค้า
      sales_admin: payload.employee?.id || "20614",
      your_reference: payload.quoteNo || "",
      items: rpaItems,
    };

    // ✅ Log RPA Payload
    console.log("[RPA] Sending payload:", rpaPayload);

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

## 📋 Checklist สำหรับการปรับปรุง

- [ ] เพิ่ม Validation สำหรับรหัสลูกค้าใน Frontend (High Priority)
- [ ] เพิ่ม Validation สำหรับรหัสลูกค้าใน Backend (High Priority)
- [ ] เพิ่ม Error Handling ใน RPA Agent (Medium Priority)
- [ ] เพิ่ม Logging ใน Frontend (Medium Priority)
- [ ] ทดสอบ Test Cases ทั้งหมด

---

## 🧪 Testing Plan

### Test Case 1: ลูกค้าใหม่ (มีรหัส)
```
1. คลิก "ลูกค้าใหม่"
2. กรอก:
   - รหัสลูกค้า: "CUST-001"
   - ชื่อลูกค้า: "บริษัท ABC"
   - เบอร์โทร: "0812345678"
   - เลขประจำตัวผู้เสียภาษี: "1234567890123"
3. คลิก "บันทึก"
4. ตรวจสอบว่า:
   - ข้อมูลลูกค้าถูกบันทึก
   - Backend ได้รับ customer.code = "CUST-001"
   - RPA Agent ได้รับ customer_no = "CUST-001"
```

### Test Case 2: ลูกค้าใหม่ (ไม่มีรหัส)
```
1. คลิก "ลูกค้าใหม่"
2. กรอก:
   - รหัสลูกค้า: "" (ว่าง)
   - ชื่อลูกค้า: "บริษัท XYZ"
   - เบอร์โทร: "0812345678"
3. คลิก "บันทึก"
4. ตรวจสอบว่า:
   - แสดง Error Message: "กรุณากรอกรหัสลูกค้า"
   - ไม่ส่งข้อมูลไปยัง Backend
```

### Test Case 3: ลูกค้าใหม่ (รหัสไม่ถูกต้อง)
```
1. คลิก "ลูกค้าใหม่"
2. กรอก:
   - รหัสลูกค้า: "CUST@001" (มีอักษรพิเศษ)
   - ชื่อลูกค้า: "บริษัท ABC"
   - เบอร์โทร: "0812345678"
3. คลิก "บันทึก"
4. ตรวจสอบว่า:
   - แสดง Error Message: "รหัสลูกค้าต้องเป็นตัวอักษร ตัวเลข หรือขีดกลางเท่านั้น"
   - ไม่ส่งข้อมูลไปยัง Backend
```

### Test Case 4: ลูกค้าใหม่ (รหัสยาวเกิน)
```
1. คลิก "ลูกค้าใหม่"
2. กรอก:
   - รหัสลูกค้า: "CUST-001-VERY-LONG-CODE" (เกิน 20 ตัวอักษร)
   - ชื่อลูกค้า: "บริษัท ABC"
   - เบอร์โทร: "0812345678"
3. คลิก "บันทึก"
4. ตรวจสอบว่า:
   - แสดง Error Message: "รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร"
   - ไม่ส่งข้อมูลไปยัง Backend
```

---

**ผู้เขียน:** Kiro AI Assistant  
**วันที่:** 21 มีนาคม 2026
