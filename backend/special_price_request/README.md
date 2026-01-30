# Special Price Request Module

โมดูลสำหรับจัดการคำขอราคาพิเศษ

## โครงสร้างไฟล์

- `router.py` - API endpoints สำหรับคำขอราคาพิเศษ
- `service.py` - Business logic สำหรับจัดการคำขอ
- `pdf_service.py` - สร้าง PDF สำหรับคำขอราคาพิเศษ
- `email_reply_checker.py` - ตรวจสอบ email reply เพื่ออนุมัติ/ปฏิเสธ
- `run_email_checker.py` - Background service สำหรับตรวจสอบ email
- `check_email_now.py` - Script สำหรับตรวจสอบ email ทันที
- `migrations/` - Database migrations
- `add_approval_pdf_column.py` - Migration script

## การใช้งาน

### รัน Email Checker
```bash
cd backend
python -m special_price_request.run_email_checker
```

### ตรวจสอบ Email ทันที
```bash
cd backend
python -m special_price_request.check_email_now
```

### รัน Migration
```bash
cd backend
python -m special_price_request.add_approval_pdf_column
```
