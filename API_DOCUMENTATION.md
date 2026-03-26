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
