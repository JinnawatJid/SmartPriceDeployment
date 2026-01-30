# Tasks: Special Price Request System

## Phase 1: Database Setup

- [ ] 1. สร้างตาราง Database
  - [ ] 1.1 สร้างตาราง `special_price_requests`
  - [ ] 1.2 สร้างตาราง `special_price_request_items`
  - [ ] 1.3 เพิ่ม column `special_price_request_id` และ `special_price_status` ใน `Quote_Header`
  - [ ] 1.4 สร้าง Migration Script
  - [ ] 1.5 Test Migration Script

## Phase 2: Backend - Core Services

- [ ] 2. สร้าง SpecialPriceRequestService
  - [ ] 2.1 สร้างไฟล์ `backend/services/special_price_request_service.py`
  - [ ] 2.2 Implement `generate_request_number()` - สร้างเลขที่คำขอรูปแบบ SP-YYMMDD-XXXX
  - [ ] 2.3 Implement `calculate_discount_percentage()` - คำนวณ % ส่วนลด
  - [ ] 2.4 Implement `create_request()` - สร้างคำขอใหม่
  - [ ] 2.5 Implement `get_requests()` - ดึงรายการคำขอ
  - [ ] 2.6 Implement `get_request_detail()` - ดึงรายละเอียดคำขอ
  - [ ] 2.7 Implement `approve_request()` - อนุมัติคำขอ
  - [ ] 2.8 Implement `reject_request()` - ปฏิเสธคำขอ
  - [ ] 2.9 Write Unit Tests

- [ ] 3. สร้าง EmailService
  - [ ] 3.1 สร้างไฟล์ `backend/services/email_service.py`
  - [ ] 3.2 สร้าง Email Configuration (`backend/config/email_config.py`)
  - [ ] 3.3 Implement `send_email()` - ส่ง Email พื้นฐาน
  - [ ] 3.4 Implement `send_approval_request()` - ส่ง Email ขออนุมัติพร้อมแนบ PDF
  - [ ] 3.5 Implement `send_approval_notification()` - แจ้งผลการอนุมัติ
  - [ ] 3.6 Implement `send_rejection_notification()` - แจ้งผลการปฏิเสธ
  - [ ] 3.7 Write Unit Tests (Mock SMTP)

- [ ] 4. สร้าง PDFService
  - [ ] 4.1 สร้างไฟล์ `backend/services/pdf_service.py`
  - [ ] 4.2 สร้าง PDF Template สำหรับคำขอราคาพิเศษ
  - [ ] 4.3 Implement `generate_special_price_request_pdf()` - สร้าง PDF
  - [ ] 4.4 Test PDF Generation

## Phase 3: Backend - API Endpoints

- [ ] 5. สร้าง API Router
  - [ ] 5.1 สร้างไฟล์ `backend/special_price_request_router.py`
  - [ ] 5.2 Implement POST `/api/special-price-requests` - สร้างคำขอใหม่
  - [ ] 5.3 Implement GET `/api/special-price-requests` - ดึงรายการคำขอ
  - [ ] 5.4 Implement GET `/api/special-price-requests/{request_number}` - ดึงรายละเอียด
  - [ ] 5.5 Implement GET `/api/special-price-requests/{request_number}/pdf` - ดาวน์โหลด PDF
  - [ ] 5.6 Implement POST `/api/special-price-requests/{request_number}/approve` - อนุมัติ (Optional)
  - [ ] 5.7 Implement POST `/api/special-price-requests/{request_number}/reject` - ปฏิเสธ (Optional)
  - [ ] 5.8 Register Router ใน `main.py`
  - [ ] 5.9 Write Integration Tests

- [ ] 6. แก้ไข Quotation API
  - [ ] 6.1 เพิ่ม field `special_price_request_id` และ `special_price_status` ใน Response
  - [ ] 6.2 อัปเดต GET `/api/quotation/{quote_no}` ให้รวมข้อมูลคำขอราคาพิเศษ
  - [ ] 6.3 Test API Changes

## Phase 4: Backend - Background Job

- [ ] 7. สร้าง Email Reply Processor
  - [ ] 7.1 สร้างไฟล์ `backend/services/email_reply_processor.py`
  - [ ] 7.2 สร้าง Job Configuration (`backend/config/job_config.py`)
  - [ ] 7.3 Implement `check_inbox()` - ตรวจสอบ Email Inbox ผ่าน IMAP
  - [ ] 7.4 Implement `process_reply()` - ประมวลผล Reply Email
  - [ ] 7.5 Implement `extract_request_number()` - ดึงเลขที่คำขอจาก Subject
  - [ ] 7.6 Implement `parse_action()` - Parse คำว่า APPROVE/REJECT
  - [ ] 7.7 Implement `extract_rejection_reason()` - ดึงเหตุผลจาก REJECT
  - [ ] 7.8 Write Unit Tests

- [ ] 8. สร้าง Background Job Runner
  - [ ] 8.1 สร้างไฟล์ `backend/background_jobs.py`
  - [ ] 8.2 Implement Job Scheduler (APScheduler)
  - [ ] 8.3 Schedule Email Check Job ทุก 5 นาที
  - [ ] 8.4 Add Error Handling และ Logging
  - [ ] 8.5 Test Background Job

## Phase 5: Frontend - Components

- [ ] 9. สร้าง SpecialPriceRequestButton
  - [ ] 9.1 สร้างไฟล์ `frontend/src/components/wizard/SpecialPriceRequestButton.jsx`
  - [ ] 9.2 Implement Button Component
  - [ ] 9.3 Add Styling (Tailwind CSS)
  - [ ] 9.4 Test Component

- [ ] 10. สร้าง SpecialPriceRequestModal
  - [ ] 10.1 สร้างไฟล์ `frontend/src/components/wizard/SpecialPriceRequestModal.jsx`
  - [ ] 10.2 Implement Form Fields (ชื่อ, Email, เบอร์โทร, เหตุผล, Email ผู้อนุมัติ)
  - [ ] 10.3 Implement Form Validation
  - [ ] 10.4 แสดงสรุปราคา (ราคาเดิม, ราคาที่ขอ, % ส่วนลด)
  - [ ] 10.5 แสดงรายการสินค้าที่ราคาต่ำกว่า W1 (Highlight)
  - [ ] 10.6 Implement Submit Handler
  - [ ] 10.7 Add Loading State
  - [ ] 10.8 Add Success/Error Messages
  - [ ] 10.9 Add Styling
  - [ ] 10.10 Test Component

- [ ] 11. แก้ไข PriceEditModal
  - [ ] 11.1 เพิ่ม prop `w1Price`
  - [ ] 11.2 เพิ่มการตรวจสอบราคา < W1 เมื่อกด Save
  - [ ] 11.3 แสดง Warning Message ถ้าราคาต่ำกว่า W1
  - [ ] 11.4 เปิด SpecialPriceRequestModal ถ้าราคาต่ำกว่า W1
  - [ ] 11.5 Test Changes

- [ ] 12. แก้ไข Step6_Summary
  - [ ] 12.1 เพิ่ม SpecialPriceRequestButton ตรงข้ามกับ "รายการสินค้า"
  - [ ] 12.2 แสดงสถานะ "รอการอนุมัติราคาพิเศษ" ถ้า status = "pending_approval"
  - [ ] 12.3 Disable ปุ่ม "ยืนยันใบเสนอราคา" ถ้า status = "pending_approval"
  - [ ] 12.4 แสดงสถานะ "ราคาพิเศษได้รับการอนุมัติแล้ว" ถ้า special_price_status = "approved"
  - [ ] 12.5 แสดงเหตุผลที่ถูกปฏิเสธ ถ้า special_price_status = "rejected"
  - [ ] 12.6 Test Changes

- [ ] 13. สร้าง SpecialPriceRequestHistory Page
  - [ ] 13.1 สร้างไฟล์ `frontend/src/pages/SpecialPriceRequestHistory.jsx`
  - [ ] 13.2 Implement ตารางแสดงรายการคำขอ
  - [ ] 13.3 Implement Filter ตามสถานะ (All, Pending, Approved, Rejected)
  - [ ] 13.4 Implement Pagination
  - [ ] 13.5 Implement คลิกดูรายละเอียด (Modal)
  - [ ] 13.6 Implement ดาวน์โหลด PDF
  - [ ] 13.7 Add Styling
  - [ ] 13.8 Test Page

- [ ] 14. แก้ไข QuoteDraftListPage
  - [ ] 14.1 แสดง Badge "กำลังขอราคาพิเศษ" สำหรับ status = "pending_approval"
  - [ ] 14.2 แสดง Badge "ราคาพิเศษอนุมัติแล้ว" สำหรับ special_price_status = "approved"
  - [ ] 14.3 Test Changes

## Phase 6: Frontend - API Integration

- [ ] 15. สร้าง API Service
  - [ ] 15.1 เพิ่ม Functions ใน `frontend/src/services/api.js`
  - [ ] 15.2 Implement `createSpecialPriceRequest()`
  - [ ] 15.3 Implement `getSpecialPriceRequests()`
  - [ ] 15.4 Implement `getSpecialPriceRequestDetail()`
  - [ ] 15.5 Implement `downloadSpecialPriceRequestPDF()`
  - [ ] 15.6 Test API Calls

- [ ] 16. เพิ่ม Route
  - [ ] 16.1 เพิ่ม Route `/special-price-requests` ใน `App.jsx`
  - [ ] 16.2 เพิ่ม Menu Item "ประวัติการขอราคาพิเศษ" ใน Navbar
  - [ ] 16.3 Test Navigation

## Phase 7: Testing

- [ ] 17. Unit Tests
  - [ ] 17.1 Test `generate_request_number()` - ต้องไม่ซ้ำกัน
  - [ ] 17.2 Test `calculate_discount_percentage()` - คำนวณถูกต้อง
  - [ ] 17.3 Test Email Template Generation
  - [ ] 17.4 Test Email Reply Parsing
  - [ ] 17.5 Test PDF Generation

- [ ] 18. Integration Tests
  - [ ] 18.1 Test POST `/api/special-price-requests` - สร้างคำขอสำเร็จ
  - [ ] 18.2 Test GET `/api/special-price-requests` - ดึงรายการสำเร็จ
  - [ ] 18.3 Test Email Sending - ส่ง Email สำเร็จ
  - [ ] 18.4 Test Background Job - ประมวลผล Reply Email สำเร็จ
  - [ ] 18.5 Test Quote Status Update - อัปเดตสถานะสำเร็จ

- [ ] 19. Property-Based Tests
  - [ ] 19.1 Test Property 1: Request Number Uniqueness
  - [ ] 19.2 Test Property 2: Price Validation
  - [ ] 19.3 Test Property 3: Status Transition
  - [ ] 19.4 Test Property 4: Email Sent Confirmation
  - [ ] 19.5 Test Property 5: Quote Status Sync

- [ ] 20. E2E Tests
  - [ ] 20.1 Test การขอราคาพิเศษจาก Frontend
  - [ ] 20.2 Test การแสดงสถานะ Pending
  - [ ] 20.3 Test การอนุมัติผ่าน Email Reply
  - [ ] 20.4 Test การแสดงสถานะ Approved
  - [ ] 20.5 Test การปฏิเสธและแสดงเหตุผล

## Phase 8: Deployment

- [ ] 21. Configuration
  - [ ] 21.1 สร้าง `.env` สำหรับ Email Configuration
  - [ ] 21.2 สร้าง systemd service สำหรับ Background Job
  - [ ] 21.3 เพิ่ม Email Server Configuration ใน Deployment Guide

- [ ] 22. Database Migration
  - [ ] 22.1 Backup Database ปัจจุบัน
  - [ ] 22.2 รัน Migration Script
  - [ ] 22.3 Verify ตารางใหม่

- [ ] 23. Deploy Backend
  - [ ] 23.1 Deploy Backend Code
  - [ ] 23.2 Start Background Job Service
  - [ ] 23.3 Test Email Sending
  - [ ] 23.4 Test Email Reply Processing

- [ ] 24. Deploy Frontend
  - [ ] 24.1 Build Frontend
  - [ ] 24.2 Deploy Frontend
  - [ ] 24.3 Test UI

- [ ] 25. Final Testing
  - [ ] 25.1 Test End-to-End Workflow
  - [ ] 25.2 Test Email Delivery
  - [ ] 25.3 Test PDF Generation
  - [ ] 25.4 Test Background Job
  - [ ] 25.5 Monitor Logs

## Phase 9: Documentation

- [ ] 26. สร้าง Documentation
  - [ ] 26.1 เขียน User Guide - วิธีใช้งานระบบขอราคาพิเศษ
  - [ ] 26.2 เขียน Admin Guide - วิธีตั้งค่า Email Server
  - [ ] 26.3 เขียน Developer Guide - API Documentation
  - [ ] 26.4 อัปเดต PROJECT_DOCUMENTATION.md
