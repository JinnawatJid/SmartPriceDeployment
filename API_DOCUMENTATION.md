# Project Price API Documentation

## Get All Projects by Customer Code

### Endpoint
```
GET /api/project-prices/customer/{customer_code}/all
```

### Description
ดึงรายการโครงการทั้งหมดของลูกค้า (ไม่กรองสถานะหรือวันที่)

### Parameters
- `customer_code` (path parameter, required): รหัสลูกค้า เช่น `08015AY`

### Example Request
```bash
curl -X GET "http://localhost:8000/api/project-prices/customer/08015AY/all"
```

### Example Response
```json
[
    {
        "project_code": "PJ2501001",
        "project_name": "โครงการคอนโดXXX",
        "customer_code": "08015AY",
        "customer_name": "บริษัท ABC",
        "branch_code": "BKK",
        "request_by": "สมชาย",
        "remark": "หมายเหตุเพิ่มเติม"
    },
    {
        "project_code": "PJ2501002",
        "project_name": "โครงการสำนักงาน",
        "customer_code": "08015AY",
        "customer_name": "บริษัท ABC",
        "branch_code": "BKK",
        "request_by": "สมหญิง",
        "remark": ""
    }
]
```

### Response Fields
- `project_code`: เลขที่โครงการ
- `project_name`: ชื่อโครงการ
- `customer_code`: รหัสลูกค้า
- `customer_name`: ชื่อลูกค้า
- `branch_code`: รหัสสาขา
- `request_by`: ชื่อผู้ขอ
- `remark`: หมายเหตุ

### Status Codes
- `200`: สำเร็จ (ส่งกลับรายการโครงการ หรือ array ว่างถ้าไม่มีโครงการ)
- `500`: เกิดข้อผิดพลาดในเซิร์ฟเวอร์

### Notes
- API นี้ส่งกลับโครงการทั้งหมด ไม่ว่าจะเป็น active หรือ inactive
- ไม่มีการกรองตามวันที่
- ผลลัพธ์เรียงลำดับจากโครงการล่าสุดไปเก่าสุด (project_code DESC)


---

## Get Pre-Order Quotes by Branch Code

### Endpoint
```
GET /quotation/pre-order/{branch_code}
```

### Description
ดึงรายการใบเสนอราคาที่เป็น Pre-Order ตามรหัสสาขา (ส่งเฉพาะ Quote_Header ที่มี Pre_Order = 1)

### Parameters
- `branch_code` (path parameter, required): รหัสสาขา เช่น `BKK`, `CNX`

### Example Request
```bash
curl -X GET "http://localhost:8000/quotation/pre-order/BKK"
```

### Example Response
```json
[
    {
        "QuoteNo": "BKK2501001",
        "Status": "complete",
        "CustomerCode": "08015AY",
        "CustomerName": "บริษัท ABC",
        "SalesID": "20614",
        "SalesName": "สมชาย",
        "CreateDate": "2025-01-15 10:30:00",
        "ExpireDate": "2025-02-15",
        "ApproveDate": "2025-01-15",
        "BranchCode": "BKK",
        "ShippingCost": 500.00,
        "DiscountAmount": 1000.00,
        "SubtotalAmount": 50000.00,
        "TotalAmount": 49500.00,
        "NeedsTax": 1,
        "Remark": "หมายเหตุ",
        "Remark_Shipping": "หมายเหตุการจัดส่ง",
        "LastUpdate": "2025-01-15 10:30:00",
        "Tel": "0812345678",
        "tax_no": "1234567890123",
        "ShippingCustomerPay": 0,
        "Pre_Order": 1,
        "Required_Delivery_Date": "2025-02-28",
        "project_code": "PJ2501001"
    },
    {
        "QuoteNo": "BKK2501002",
        "Status": "complete",
        "CustomerCode": "08016AY",
        "CustomerName": "บริษัท XYZ",
        "SalesID": "20614",
        "SalesName": "สมชาย",
        "CreateDate": "2025-01-14 14:20:00",
        "ExpireDate": "2025-02-14",
        "ApproveDate": "2025-01-14",
        "BranchCode": "BKK",
        "ShippingCost": 300.00,
        "DiscountAmount": 500.00,
        "SubtotalAmount": 30000.00,
        "TotalAmount": 29800.00,
        "NeedsTax": 1,
        "Remark": "",
        "Remark_Shipping": "",
        "LastUpdate": "2025-01-14 14:20:00",
        "Tel": "0898765432",
        "tax_no": "9876543210987",
        "ShippingCustomerPay": 0,
        "Pre_Order": 1,
        "Required_Delivery_Date": "2025-02-20",
        "project_code": null
    }
]
```

### Response Fields
- `QuoteNo`: เลขที่ใบเสนอราคา
- `Status`: สถานะ (draft, complete, cancelled)
- `CustomerCode`: รหัสลูกค้า
- `CustomerName`: ชื่อลูกค้า
- `SalesID`: รหัสพนักงานขาย
- `SalesName`: ชื่อพนักงานขาย
- `CreateDate`: วันที่สร้าง
- `ExpireDate`: วันที่หมดอายุ
- `ApproveDate`: วันที่อนุมัติ
- `BranchCode`: รหัสสาขา
- `ShippingCost`: ค่าจัดส่ง
- `DiscountAmount`: ส่วนลด
- `SubtotalAmount`: รวมก่อนภาษี
- `TotalAmount`: รวมทั้งสิ้น
- `NeedsTax`: ต้องการภาษี (0 หรือ 1)
- `Remark`: หมายเหตุ
- `Remark_Shipping`: หมายเหตุการจัดส่ง
- `LastUpdate`: วันที่อัปเดตล่าสุด
- `Tel`: เบอร์โทรศัพท์
- `tax_no`: เลขประจำตัวผู้เสียภาษี
- `ShippingCustomerPay`: ลูกค้าจ่ายค่าจัดส่ง (0 หรือ 1)
- `Pre_Order`: เป็น Pre-Order (1 = ใช่, 0 = ไม่ใช่)
- `Required_Delivery_Date`: วันที่ต้องการจัดส่ง
- `project_code`: รหัสโครงการ (ถ้ามี)

### Status Codes
- `200`: สำเร็จ (ส่งกลับรายการใบเสนอราคา Pre-Order หรือ array ว่างถ้าไม่มี)
- `500`: เกิดข้อผิดพลาดในเซิร์ฟเวอร์

### Notes
- API นี้ส่งกลับเฉพาะใบเสนอราคาที่มี `Pre_Order = 1`
- ผลลัพธ์เรียงลำดับจากใบเสนอราคาล่าสุดไปเก่าสุด (CreateDate DESC)
- ส่งกลับ Quote_Header ทั้งหมด ไม่ว่าจะเป็น draft, complete หรือ cancelled
- ถ้าไม่มีใบเสนอราคา Pre-Order สำหรับสาขานั้น จะส่งกลับ array ว่าง


---

## Frontend Usage

### How to Use the Pre-Order Quotes API

The API endpoint is available at:
```
GET /api/quotation/pre-order/{branch_code}
```

#### JavaScript/React Example:
```javascript
import api from '../services/api';

// Fetch pre-order quotes for a branch
const fetchPreOrderQuotes = async (branchCode) => {
  try {
    const response = await api.get(`/quotation/pre-order/${branchCode}`);
    console.log('Pre-order quotes:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching pre-order quotes:', error);
  }
};

// Usage
fetchPreOrderQuotes('BKK');
```

#### Frontend Page
A pre-built page is available at `/pre-order-quotes` that provides a UI to search for pre-order quotes by branch code.

**URL**: `http://localhost:5173/pre-order-quotes`

This page includes:
- Search form to enter branch code
- Results table showing all pre-order quotes
- Display of customer info, sales person, dates, and amounts
- Status indicators

### Important Notes
- The API endpoint is `/api/quotation/pre-order/{branch_code}` (note the `/api` prefix)
- Do NOT try to navigate to `/quotation/pre-order/{branch_code}` as a frontend route
- Always use `api.get()` to call the endpoint from frontend code
- Branch codes are case-insensitive (BKK, bkk, Bkk all work)
