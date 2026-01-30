# Design: Special Price Request System

## 1. Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │────────▶│   Backend    │────────▶│   Email     │
│   (React)   │         │   (FastAPI)  │         │   Server    │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │                        ▼                        │
      │                  ┌──────────┐                   │
      │                  │  SQLite  │                   │
      │                  │    DB    │                   │
      │                  └──────────┘                   │
      │                        ▲                        │
      │                        │                        │
      └────────────────────────┴────────────────────────┘
                    Background Job (IMAP Check)
```

## 2. Database Design

### 2.1 ตาราง `special_price_requests`

```sql
CREATE TABLE special_price_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number VARCHAR(20) UNIQUE NOT NULL,
    quote_no VARCHAR(50) NOT NULL,
    customer_code VARCHAR(50),
    customer_name VARCHAR(255),
    
    -- ข้อมูลผู้ขอ
    requester_name VARCHAR(255) NOT NULL,
    requester_email VARCHAR(255) NOT NULL,
    requester_phone VARCHAR(50),
    request_reason TEXT NOT NULL,
    
    -- ข้อมูลราคา
    original_total DECIMAL(15,2) NOT NULL,
    requested_total DECIMAL(15,2) NOT NULL,
    discount_percentage DECIMAL(5,2),
    
    -- สถานะและการอนุมัติ
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approver_email VARCHAR(255) NOT NULL,
    approved_by VARCHAR(255),
    approved_at DATETIME,
    rejection_reason TEXT,
    
    -- Email tracking
    email_sent_at DATETIME NOT NULL,
    email_message_id VARCHAR(255),
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (quote_no) REFERENCES Quote_Header(QuoteNo)
);

CREATE INDEX idx_request_number ON special_price_requests(request_number);
CREATE INDEX idx_status ON special_price_requests(status);
CREATE INDEX idx_quote_no ON special_price_requests(quote_no);
```

### 2.2 ตาราง `special_price_request_items`

```sql
CREATE TABLE special_price_request_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    
    -- ข้อมูลสินค้า
    item_code VARCHAR(100) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50),
    
    -- ราคา
    w1_price DECIMAL(15,2) NOT NULL,
    requested_price DECIMAL(15,2) NOT NULL,
    original_amount DECIMAL(15,2) NOT NULL,
    requested_amount DECIMAL(15,2) NOT NULL,
    is_below_w1 BOOLEAN DEFAULT FALSE,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (request_id) REFERENCES special_price_requests(id) ON DELETE CASCADE
);

CREATE INDEX idx_request_id ON special_price_request_items(request_id);
```

### 2.3 แก้ไขตาราง `Quote_Header`

```sql
ALTER TABLE Quote_Header ADD COLUMN special_price_request_id INTEGER;
ALTER TABLE Quote_Header ADD COLUMN special_price_status VARCHAR(20);

CREATE INDEX idx_special_price_request ON Quote_Header(special_price_request_id);
```

**Status Values:**
- `Quote_Header.Status`: `"draft"`, `"pending_approval"`, `"open"`, `"cancelled"`
- `Quote_Header.special_price_status`: `NULL`, `"approved"`, `"rejected"`
- `special_price_requests.status`: `"pending"`, `"approved"`, `"rejected"`

## 3. API Design

### 3.1 POST `/api/special-price-requests`
สร้างคำขอราคาพิเศษใหม่

**Request Body:**
```json
{
  "quote_no": "BSQT-2501/0001",
  "requester_name": "สมชาย ใจดี",
  "requester_email": "somchai@company.com",
  "requester_phone": "081-234-5678",
  "request_reason": "ลูกค้าเป็น VIP และสั่งซื้อจำนวนมาก",
  "approver_email": "manager@company.com",
  "items": [
    {
      "item_code": "A010010100101",
      "item_name": "อลูมิเนียม",
      "quantity": 100,
      "unit": "เมตร",
      "w1_price": 150.00,
      "requested_price": 120.00
    }
  ]
}
```

**Response:**
```json
{
  "request_number": "SP-250130-0001",
  "status": "pending",
  "email_sent": true,
  "message": "ส่งคำขอราคาพิเศษสำเร็จ"
}
```

### 3.2 GET `/api/special-price-requests`
ดึงรายการคำขอทั้งหมด

**Query Parameters:**
- `status`: `pending`, `approved`, `rejected`, `all` (default: `all`)
- `limit`: จำนวนรายการต่อหน้า (default: 20)
- `offset`: เริ่มต้นที่รายการที่ (default: 0)

**Response:**
```json
{
  "items": [
    {
      "request_number": "SP-250130-0001",
      "quote_no": "BSQT-2501/0001",
      "customer_name": "บริษัท ABC จำกัด",
      "requester_name": "สมชาย ใจดี",
      "original_total": 15000.00,
      "requested_total": 12000.00,
      "discount_percentage": 20.00,
      "status": "pending",
      "created_at": "2025-01-30T10:30:00",
      "approved_by": null,
      "approved_at": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### 3.3 GET `/api/special-price-requests/{request_number}`
ดึงรายละเอียดคำขอ

**Response:**
```json
{
  "request_number": "SP-250130-0001",
  "quote_no": "BSQT-2501/0001",
  "customer_code": "C001",
  "customer_name": "บริษัท ABC จำกัด",
  "requester_name": "สมชาย ใจดี",
  "requester_email": "somchai@company.com",
  "requester_phone": "081-234-5678",
  "request_reason": "ลูกค้าเป็น VIP",
  "original_total": 15000.00,
  "requested_total": 12000.00,
  "discount_percentage": 20.00,
  "status": "approved",
  "approver_email": "manager@company.com",
  "approved_by": "ผู้จัดการสมหญิง",
  "approved_at": "2025-01-30T11:00:00",
  "items": [
    {
      "item_code": "A010010100101",
      "item_name": "อลูมิเนียม",
      "quantity": 100,
      "unit": "เมตร",
      "w1_price": 150.00,
      "requested_price": 120.00,
      "original_amount": 15000.00,
      "requested_amount": 12000.00,
      "is_below_w1": true
    }
  ]
}
```

### 3.4 POST `/api/special-price-requests/{request_number}/approve`
อนุมัติคำขอ (สำหรับ Web Endpoint - Optional)

**Request Body:**
```json
{
  "token": "abc123...",
  "approved_by": "ผู้จัดการสมหญิง"
}
```

### 3.5 POST `/api/special-price-requests/{request_number}/reject`
ปฏิเสธคำขอ (สำหรับ Web Endpoint - Optional)

**Request Body:**
```json
{
  "token": "abc123...",
  "rejection_reason": "ราคาต่ำเกินไป ไม่สามารถอนุมัติได้"
}
```

### 3.6 GET `/api/special-price-requests/{request_number}/pdf`
ดาวน์โหลด PDF

**Response:** PDF File

## 4. Frontend Components

### 4.1 SpecialPriceRequestButton
ปุ่มขอราคาพิเศษในหน้า Step6

**Location:** `frontend/src/components/wizard/SpecialPriceRequestButton.jsx`

**Props:**
- `cart`: รายการสินค้าทั้งหมด
- `totals`: ข้อมูลราคารวม
- `customer`: ข้อมูลลูกค้า
- `quoteNo`: เลขที่ใบเสนอราคา
- `onRequestSent`: Callback เมื่อส่งคำขอสำเร็จ

### 4.2 SpecialPriceRequestModal
Modal กรอกข้อมูลคำขอ

**Location:** `frontend/src/components/wizard/SpecialPriceRequestModal.jsx`

**Props:**
- `isOpen`: เปิด/ปิด Modal
- `onClose`: Callback เมื่อปิด Modal
- `cart`: รายการสินค้า
- `totals`: ข้อมูลราคา
- `customer`: ข้อมูลลูกค้า
- `quoteNo`: เลขที่ใบเสนอราคา
- `itemsBelowW1`: รายการสินค้าที่ราคาต่ำกว่า W1

**State:**
```javascript
{
  requesterName: "",
  requesterEmail: "",
  requesterPhone: "",
  requestReason: "",
  approverEmail: "",
  isSubmitting: false,
  errors: {}
}
```

### 4.3 SpecialPriceRequestHistory
หน้าแสดงประวัติการขอราคาพิเศษ

**Location:** `frontend/src/pages/SpecialPriceRequestHistory.jsx`

**Features:**
- ตารางแสดงรายการคำขอทั้งหมด
- Filter ตามสถานะ
- Pagination
- คลิกดูรายละเอียด
- ดาวน์โหลด PDF

### 4.4 PriceEditModal Enhancement
แก้ไข PriceEditModal เพื่อตรวจสอบราคา W1

**Location:** `frontend/src/components/wizard/PriceEditModal.jsx`

**Changes:**
- เพิ่ม prop `w1Price` เพื่อเปรียบเทียบ
- เมื่อกด Save ตรวจสอบว่า `newPrice < w1Price`
- ถ้าใช่ แสดง Warning และเปิด SpecialPriceRequestModal
- เพิ่ม Warning Message: "ราคาที่ใส่ต่ำกว่าราคา W1 (฿{w1Price}) ต้องขอราคาพิเศษ"

## 5. Backend Services

### 5.1 SpecialPriceRequestService
**Location:** `backend/services/special_price_request_service.py`

**Methods:**
- `create_request(data)`: สร้างคำขอใหม่
- `get_requests(status, limit, offset)`: ดึงรายการคำขอ
- `get_request_detail(request_number)`: ดึงรายละเอียด
- `approve_request(request_number, approved_by)`: อนุมัติคำขอ
- `reject_request(request_number, reason)`: ปฏิเสธคำขอ
- `generate_request_number()`: สร้างเลขที่คำขอ
- `calculate_discount_percentage(original, requested)`: คำนวณ % ส่วนลด

### 5.2 EmailService
**Location:** `backend/services/email_service.py`

**Methods:**
- `send_approval_request(request_data, pdf_path)`: ส่ง Email ขออนุมัติ
- `send_approval_notification(request_data)`: แจ้งผลการอนุมัติ
- `send_rejection_notification(request_data)`: แจ้งผลการปฏิเสธ

**Email Template:**
```
Subject: [Approval Required] Special Price Request {request_number}

เรียน ผู้อนุมัติ

มีคำขอราคาพิเศษรอการพิจารณา

เลขที่คำขอ: {request_number}
ผู้ขอ: {requester_name}
ลูกค้า: {customer_name}
ราคาเดิม: ฿{original_total:,.2f}
ราคาที่ขอ: ฿{requested_total:,.2f}
ส่วนลด: {discount_percentage}%

เหตุผล: {request_reason}

กรุณา Reply Email นี้ด้วยคำว่า:
- APPROVE เพื่ออนุมัติ
- REJECT: <เหตุผล> เพื่อปฏิเสธ

*** กรุณาอย่าแก้ไข Subject ***

รายละเอียดเพิ่มเติมในไฟล์แนบ
```

### 5.3 PDFService
**Location:** `backend/services/pdf_service.py`

**Methods:**
- `generate_special_price_request_pdf(request_data)`: สร้าง PDF คำขอราคาพิเศษ

**PDF Content:**
- Header: เลขที่คำขอ, วันที่
- ข้อมูลผู้ขอ
- ข้อมูลลูกค้า
- ตารางรายการสินค้า (แสดง W1 Price vs Requested Price)
- สรุปราคา
- เหตุผลที่ขอ

### 5.4 EmailReplyProcessor (Background Job)
**Location:** `backend/services/email_reply_processor.py`

**Methods:**
- `check_inbox()`: ตรวจสอบ Email Inbox ทุก 5 นาที
- `process_reply(email_message)`: ประมวลผล Reply Email
- `extract_request_number(subject)`: ดึงเลขที่คำขอจาก Subject
- `parse_action(body)`: Parse คำว่า APPROVE หรือ REJECT

**Logic:**
```python
def process_reply(email_message):
    subject = email_message.subject
    body = email_message.body
    
    # Extract request number from subject
    request_number = extract_request_number(subject)
    if not request_number:
        return
    
    # Check if request exists
    request = get_request_by_number(request_number)
    if not request or request.status != 'pending':
        return
    
    # Parse action
    if 'APPROVE' in body.upper():
        approve_request(request_number, email_message.from_email)
        send_approval_notification(request)
    elif 'REJECT:' in body.upper():
        reason = extract_rejection_reason(body)
        reject_request(request_number, reason)
        send_rejection_notification(request)
```

## 6. Workflow Diagram

### 6.1 การขอราคาพิเศษ

```
[พนักงานขาย]
    │
    ├─ กดปุ่ม "ขอราคาพิเศษ" หรือ แก้ไขราคา < W1
    │
    ▼
[เปิด Modal]
    │
    ├─ กรอกข้อมูล: ชื่อ, Email, เหตุผล, Email ผู้อนุมัติ
    │
    ▼
[กดยืนยัน]
    │
    ├─ Validate ข้อมูล
    ├─ สร้างเลขที่คำขอ (SP-YYMMDD-XXXX)
    ├─ บันทึกลง DB
    ├─ สร้าง PDF
    ├─ ส่ง Email พร้อมแนบ PDF
    ├─ อัปเดต Quote Status = "pending_approval"
    │
    ▼
[แสดง Success Message]
```

### 6.2 การอนุมัติ

```
[ผู้อนุมัติ]
    │
    ├─ รับ Email
    ├─ อ่านรายละเอียดใน PDF
    │
    ▼
[Reply Email]
    │
    ├─ พิมพ์ "APPROVE" หรือ "REJECT: เหตุผล"
    ├─ ส่ง Reply
    │
    ▼
[Background Job]
    │
    ├─ ตรวจสอบ Inbox ทุก 5 นาที
    ├─ อ่าน Reply Email
    ├─ Parse คำว่า APPROVE/REJECT
    ├─ อัปเดตสถานะใน DB
    ├─ อัปเดต Quote Status
    ├─ ส่ง Email แจ้งผลกลับผู้ขอ
    │
    ▼
[พนักงานขาย]
    │
    ├─ รับ Email แจ้งผล
    ├─ เปิดใบเสนอราคา
    ├─ เห็นสถานะ "อนุมัติแล้ว" หรือ "ปฏิเสธ"
    │
    ▼
[ดำเนินการต่อ]
```

## 7. Correctness Properties

### Property 1: Request Number Uniqueness
**Description:** เลขที่คำขอต้องไม่ซ้ำกัน

**Property:**
```python
def test_request_number_uniqueness():
    # สร้างคำขอหลายรายการในวันเดียวกัน
    requests = [create_request() for _ in range(10)]
    request_numbers = [r.request_number for r in requests]
    
    # ต้องไม่มีเลขที่ซ้ำ
    assert len(request_numbers) == len(set(request_numbers))
```

### Property 2: Price Validation
**Description:** ราคาที่ขอต้องไม่เป็นลบและไม่มากกว่าราคาเดิม

**Property:**
```python
def test_price_validation(cart, requested_prices):
    for item, requested_price in zip(cart, requested_prices):
        assert requested_price >= 0
        assert requested_price <= item.original_price
```

### Property 3: Status Transition
**Description:** สถานะต้องเปลี่ยนตามลำดับที่ถูกต้อง

**Property:**
```python
def test_status_transition():
    # pending -> approved หรือ rejected
    # approved/rejected ไม่สามารถกลับไปเป็น pending
    
    request = create_request()  # status = pending
    assert request.status == "pending"
    
    approve_request(request.id)
    assert request.status == "approved"
    
    # ไม่สามารถเปลี่ยนกลับเป็น pending
    with pytest.raises(InvalidStatusTransition):
        update_status(request.id, "pending")
```

### Property 4: Email Sent Confirmation
**Description:** ทุกคำขอต้องมีการส่ง Email

**Property:**
```python
def test_email_sent_confirmation():
    request = create_request(data)
    
    # ต้องมี email_sent_at
    assert request.email_sent_at is not None
    
    # ต้องมี email_message_id
    assert request.email_message_id is not None
```

### Property 5: Quote Status Sync
**Description:** สถานะของ Quote ต้องสอดคล้องกับสถานะคำขอ

**Property:**
```python
def test_quote_status_sync():
    request = create_request(quote_no="BSQT-2501/0001")
    quote = get_quote(request.quote_no)
    
    # เมื่อสร้างคำขอ Quote ต้องเป็น pending_approval
    assert quote.status == "pending_approval"
    
    # เมื่ออนุมัติ Quote ต้องกลับเป็น draft
    approve_request(request.id)
    quote = get_quote(request.quote_no)
    assert quote.status == "draft"
    assert quote.special_price_status == "approved"
```

## 8. Testing Strategy

### 8.1 Unit Tests
- Test การสร้างเลขที่คำขอ
- Test การคำนวณ % ส่วนลด
- Test Email Template Generation
- Test PDF Generation
- Test Email Reply Parsing

### 8.2 Integration Tests
- Test API Endpoints
- Test Database Operations
- Test Email Sending
- Test Background Job

### 8.3 Property-Based Tests
- Test Request Number Uniqueness (Property 1)
- Test Price Validation (Property 2)
- Test Status Transition (Property 3)
- Test Email Sent Confirmation (Property 4)
- Test Quote Status Sync (Property 5)

### 8.4 E2E Tests
- Test การขอราคาพิเศษจาก Frontend
- Test การอนุมัติผ่าน Email Reply
- Test การแสดงสถานะใน UI

## 9. Configuration

### 9.1 Email Configuration
**Location:** `backend/config/email_config.py`

```python
EMAIL_CONFIG = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "noreply@company.com",
    "smtp_password": "***",
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_user": "noreply@company.com",
    "imap_password": "***",
    "from_email": "noreply@company.com",
    "from_name": "ระบบใบเสนอราคา"
}
```

### 9.2 Background Job Configuration
**Location:** `backend/config/job_config.py`

```python
JOB_CONFIG = {
    "email_check_interval": 300,  # 5 minutes
    "max_retries": 3,
    "retry_delay": 60  # 1 minute
}
```

## 10. Deployment Considerations

- ต้องติดตั้ง Email Server (SMTP/IMAP) บน Server
- ต้องเปิด Port 587 (SMTP) และ 993 (IMAP)
- ต้องรัน Background Job เป็น Service (systemd หรือ supervisor)
- ต้องสร้างตาราง Database ใหม่ (Migration Script)
- ต้อง Backup Database ก่อน Deploy
