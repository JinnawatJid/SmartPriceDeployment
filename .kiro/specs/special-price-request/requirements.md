# Requirements: Special Price Request System

## 1. ภาพรวม

ระบบขอราคาพิเศษ (Special Price Request System) เป็นฟีเจอร์ที่ช่วยให้พนักงานขายสามารถขอราคาพิเศษจากผู้มีอำนาจอนุมัติ เมื่อต้องการเสนอราคาที่ต่ำกว่าราคามาตรฐาน W1 ให้กับลูกค้า

### ข้อมูลบริบท
- **ระบบปัจจุบัน**: Python FastAPI + SQLite + React
- **ตาราง Database**: `Quote_Header`, `Quote_Line`, `Items_Test`
- **ข้อจำกัด**: เครื่อง Client ออกเน็ตไม่ได้ มีเพียง Server เท่านั้นที่ส่ง Email ได้

## 2. User Stories

### 2.1 ขอราคาพิเศษด้วยตนเอง
**As a** พนักงานขาย  
**I want to** กดปุ่มขอราคาพิเศษในหน้าสรุปรายการสินค้า  
**So that** ฉันสามารถขออนุมัติราคาพิเศษจากผู้จัดการได้

**Acceptance Criteria:**
- 2.1.1 มีปุ่ม "ขอราคาพิเศษ" แสดงในหน้า Step6 ตรงข้ามกับคำว่า "รายการสินค้า"
- 2.1.2 เมื่อกดปุ่มแล้วเปิด Modal กรอกข้อมูลการขอราคาพิเศษ
- 2.1.3 Modal แสดงข้อมูลสรุปราคาเดิมและราคาที่ขอ

### 2.2 ตรวจจับราคาต่ำกว่า W1 อัตโนมัติ
**As a** พนักงานขาย  
**I want to** ระบบตรวจสอบราคาที่ฉันแก้ไขอัตโนมัติ  
**So that** ถ้าฉันใส่ราคาต่ำกว่า W1 ระบบจะเปิด Modal ขอราคาพิเศษทันที

**Acceptance Criteria:**
- 2.2.1 เมื่อแก้ไขราคาสินค้าใน PriceEditModal ระบบต้องเปรียบเทียบกับราคา W1
- 2.2.2 ถ้าราคาที่ใส่ < W1 ต้องเปิด Modal ขอราคาพิเศษทันทีหลังกด Save
- 2.2.3 แสดงรายการสินค้าที่มีราคาต่ำกว่า W1 ใน Modal (highlight สีแดง)

### 2.3 กรอกข้อมูลคำขอราคาพิเศษ
**As a** พนักงานขาย  
**I want to** กรอกข้อมูลผู้ขอและเหตุผลในการขอราคาพิเศษ  
**So that** ผู้อนุมัติสามารถพิจารณาคำขอของฉันได้

**Acceptance Criteria:**
- 2.3.1 Form ต้องมีฟิลด์: ชื่อผู้ขอ, Email ผู้ขอ, เบอร์โทร, เหตุผล, Email ผู้อนุมัติ
- 2.3.2 Validate email format สำหรับ Email ผู้ขอและ Email ผู้อนุมัติ
- 2.3.3 ฟิลด์ที่ required: ชื่อผู้ขอ, Email ผู้ขอ, เหตุผล, Email ผู้อนุมัติ
- 2.3.4 แสดงสรุปราคา: ราคาเดิม, ราคาที่ขอ, % ส่วนลด
- 2.3.5 แสดงรายการสินค้าทั้งหมดพร้อมราคา W1 และราคาที่ขอ

### 2.4 ส่งคำขอและสร้าง PDF
**As a** พนักงานขาย  
**I want to** ส่งคำขอราคาพิเศษไปยัง Email ผู้อนุมัติพร้อม PDF  
**So that** ผู้อนุมัติสามารถตรวจสอบและอนุมัติได้

**Acceptance Criteria:**
- 2.4.1 สร้างเลขที่คำขอรูปแบบ `SP-YYMMDD-XXXX` (เช่น SP-250130-0001)
- 2.4.2 บันทึกข้อมูลลงตาราง `special_price_requests` และ `special_price_request_items`
- 2.4.3 สร้าง PDF สรุปรายการขอราคาพิเศษ
- 2.4.4 ส่ง Email ไปหา approver_email พร้อมแนบ PDF
- 2.4.5 Email Subject: `[Approval Required] Special Price Request SP-YYMMDD-XXXX`
- 2.4.6 Email Body มีคำแนะนำการ Reply: "APPROVE" หรือ "REJECT: <เหตุผล>"
- 2.4.7 แสดง Success Message หลังส่งสำเร็จ

### 2.5 สถานะ Pending และการบล็อกการยืนยัน
**As a** พนักงานขาย  
**I want to** ใบเสนอราคาที่ขอราคาพิเศษต้องรอการอนุมัติก่อน  
**So that** ฉันไม่สามารถยืนยันใบเสนอราคาได้จนกว่าจะได้รับการอนุมัติ

**Acceptance Criteria:**
- 2.5.1 หลังส่งคำขอ อัปเดต `Quote_Header.Status` = `"pending_approval"`
- 2.5.2 ปุ่ม "ยืนยันใบเสนอราคา" ต้อง disabled
- 2.5.3 แสดงข้อความ "รอการอนุมัติราคาพิเศษ" แทนปุ่ม
- 2.5.4 ในหน้า Draft List แสดงสถานะ "กำลังขอราคาพิเศษ" (badge สีเหลือง)
- 2.5.5 สามารถแก้ไขรายการสินค้าได้ แต่ไม่สามารถยืนยันได้

### 2.6 ระบบอนุมัติผ่าน Email Reply
**As a** ผู้อนุมัติ  
**I want to** ตอบกลับ Email ด้วยคำว่า "APPROVE" หรือ "REJECT"  
**So that** ระบบจะอัปเดตสถานะการอนุมัติอัตโนมัติ

**Acceptance Criteria:**
- 2.6.1 ระบบมี Background Job ตรวจสอบ Email Inbox (IMAP) ทุก 5 นาที
- 2.6.2 อ่าน Reply Email ที่มี Subject ตรงกับ Request Number
- 2.6.3 Parse เนื้อหา Email:
  - ถ้าเจอคำว่า "APPROVE" → อัปเดตสถานะเป็น `approved`
  - ถ้าเจอคำว่า "REJECT:" → อัปเดตสถานะเป็น `rejected` พร้อมเก็บเหตุผล
- 2.6.4 บันทึก approved_by, approved_at
- 2.6.5 ส่ง Email แจ้งผลกลับไปหาผู้ขอ

### 2.7 หลังได้รับการอนุมัติ
**As a** พนักงานขาย  
**I want to** สามารถยืนยันใบเสนอราคาได้หลังได้รับการอนุมัติ  
**So that** ฉันสามารถดำเนินการต่อได้

**Acceptance Criteria:**
- 2.7.1 อัปเดต `Quote_Header.Status` = `"draft"` (กลับมาเป็น draft ปกติ)
- 2.7.2 อัปเดต `Quote_Header.special_price_status` = `"approved"`
- 2.7.3 ปุ่ม "ยืนยันใบเสนอราคา" สามารถกดได้อีกครั้ง
- 2.7.4 แสดงข้อความ "ราคาพิเศษได้รับการอนุมัติแล้ว" (badge สีเขียว)
- 2.7.5 แสดงชื่อผู้อนุมัติและวันที่อนุมัติ

### 2.8 หลังถูกปฏิเสธ
**As a** พนักงานขาย  
**I want to** เห็นเหตุผลที่ถูกปฏิเสธและสามารถแก้ไขได้  
**So that** ฉันสามารถปรับราคาและขอใหม่ได้

**Acceptance Criteria:**
- 2.8.1 อัปเดต `Quote_Header.Status` = `"draft"`
- 2.8.2 อัปเดต `Quote_Header.special_price_status` = `"rejected"`
- 2.8.3 แสดงเหตุผลที่ถูกปฏิเสธ (Alert หรือ Banner สีแดง)
- 2.8.4 สามารถแก้ไขราคาและขอราคาพิเศษใหม่ได้
- 2.8.5 ปุ่ม "ยืนยันใบเสนอราคา" สามารถกดได้ (ถ้าราคาไม่ต่ำกว่า W1)

### 2.9 ประวัติการขอราคาพิเศษ
**As a** ผู้จัดการ/พนักงานขาย  
**I want to** ดูประวัติการขอราคาพิเศษทั้งหมด  
**So that** ฉันสามารถติดตามและตรวจสอบคำขอได้

**Acceptance Criteria:**
- 2.9.1 มีหน้า "ประวัติการขอราคาพิเศษ" ใน Menu
- 2.9.2 แสดงตาราง: Request Number, วันที่ขอ, ผู้ขอ, ลูกค้า, ราคาที่ขอ, สถานะ, ผู้อนุมัติ
- 2.9.3 Filter ตามสถานะ: All, Pending, Approved, Rejected
- 2.9.4 คลิกดูรายละเอียดแต่ละคำขอได้ (Modal หรือหน้าใหม่)
- 2.9.5 แสดงรายการสินค้าและราคาที่ขอในรายละเอียด
- 2.9.6 สามารถดาวน์โหลด PDF ที่ส่งไปได้

## 3. Non-Functional Requirements

### 3.1 Performance
- การส่ง Email ต้องไม่เกิน 10 วินาที
- Background Job ตรวจสอบ Email ทุก 5 นาที
- การสร้าง PDF ต้องไม่เกิน 5 วินาที

### 3.2 Security
- Email ต้องส่งผ่าน TLS/SSL
- ต้องมี Token สำหรับ Approve/Reject Link (ถ้าใช้ Web Endpoint)
- Token หมดอายุภายใน 7 วัน

### 3.3 Usability
- Modal ต้องแสดงข้อความ Error ที่ชัดเจน
- แสดง Loading Indicator ขณะส่ง Email
- แสดง Success/Error Message หลังดำเนินการ

### 3.4 Reliability
- ถ้าส่ง Email ไม่สำเร็จ ต้อง Retry 3 ครั้ง
- บันทึก Log การส่ง Email ทุกครั้ง
- ถ้า Background Job ล้มเหลว ต้องแจ้งเตือน Admin

## 4. Technical Constraints

- **Backend**: Python FastAPI, SQLite
- **Email**: SMTP (ส่ง), IMAP (รับ)
- **PDF Generation**: ReportLab หรือ WeasyPrint
- **Frontend**: React, Modal Component
- **Network**: เฉพาะ Server ออกเน็ตได้

## 5. Out of Scope

- การอนุมัติแบบหลายขั้นตอน (Multi-level Approval)
- การแจ้งเตือนผ่าน LINE หรือ SMS
- การอนุมัติผ่าน Mobile App
- การตั้งค่าผู้อนุมัติตาม Role หรือ Branch
