-- ============================================
-- SQL Scripts สำหรับสร้างตารางใน MSSQL
-- ระบบขอราคาพิเศษ (Special Price Request System)
-- ============================================

-- ตาราง 1: special_price_requests (ตารางหลัก)
CREATE TABLE special_price_requests (
    id INT IDENTITY(1,1) PRIMARY KEY,
    request_number NVARCHAR(20) UNIQUE NOT NULL,
    quote_no NVARCHAR(50) NOT NULL,
    customer_code NVARCHAR(50),
    customer_name NVARCHAR(255),
    
    -- ข้อมูลผู้ขอ
    requester_name NVARCHAR(255) NOT NULL,
    requester_email NVARCHAR(255) NOT NULL,
    requester_phone NVARCHAR(50),
    request_reason NVARCHAR(MAX) NOT NULL,
    
    -- ข้อมูลราคา
    original_total DECIMAL(15,2) NOT NULL,
    requested_total DECIMAL(15,2) NOT NULL,
    discount_percentage DECIMAL(5,2),
    
    -- สถานะและการอนุมัติ
    status NVARCHAR(20) NOT NULL DEFAULT 'pending',
    approver_email NVARCHAR(255) NOT NULL,
    approved_by NVARCHAR(255),
    approved_at DATETIME2,
    rejection_reason NVARCHAR(MAX),
    
    -- ข้อมูล Email และ Token
    approval_token NVARCHAR(64) UNIQUE,
    email_sent_at DATETIME2 NOT NULL,
    email_message_id NVARCHAR(255),
    
    -- Timestamps
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- สร้าง Indexes สำหรับ special_price_requests
CREATE INDEX idx_request_number ON special_price_requests(request_number);
CREATE INDEX idx_quote_no ON special_price_requests(quote_no);
CREATE INDEX idx_status ON special_price_requests(status);
CREATE INDEX idx_created_at ON special_price_requests(created_at DESC);
GO

-- ตาราง 2: special_price_request_items (รายการสินค้า)
CREATE TABLE special_price_request_items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    request_id INT NOT NULL,
    item_code NVARCHAR(100) NOT NULL,
    item_name NVARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit NVARCHAR(50),
    w1_price DECIMAL(15,2) NOT NULL,
    requested_price DECIMAL(15,2) NOT NULL,
    original_amount DECIMAL(15,2) NOT NULL,
    requested_amount DECIMAL(15,2) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    
    -- Foreign Key
    CONSTRAINT FK_special_price_request_items_request 
        FOREIGN KEY (request_id) 
        REFERENCES special_price_requests(id) 
        ON DELETE CASCADE
);
GO

-- สร้าง Index สำหรับ special_price_request_items
CREATE INDEX idx_request_id ON special_price_request_items(request_id);
GO

-- ============================================
-- หมายเหตุ: Quote_Header อยู่ใน SQLite
-- ไม่ต้องสร้าง Foreign Key ระหว่าง MSSQL กับ SQLite
-- แต่ต้องเพิ่ม columns ใน Quote_Header (SQLite) ดังนี้:
--
-- ALTER TABLE Quote_Header ADD COLUMN special_price_request_id INTEGER;
-- ALTER TABLE Quote_Header ADD COLUMN special_price_status VARCHAR(20);
-- ============================================

-- Trigger สำหรับอัปเดต updated_at อัตโนมัติ
CREATE TRIGGER trg_special_price_requests_updated_at
ON special_price_requests
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE special_price_requests
    SET updated_at = GETDATE()
    FROM special_price_requests spr
    INNER JOIN inserted i ON spr.id = i.id;
END;
GO

-- ============================================
-- ตัวอย่างการ Query
-- ============================================

-- ดูคำขอทั้งหมด
-- SELECT * FROM special_price_requests ORDER BY created_at DESC;

-- ดูคำขอพร้อมรายการสินค้า
-- SELECT 
--     spr.*,
--     spri.item_code,
--     spri.item_name,
--     spri.quantity,
--     spri.w1_price,
--     spri.requested_price
-- FROM special_price_requests spr
-- LEFT JOIN special_price_request_items spri ON spr.id = spri.request_id
-- WHERE spr.request_number = 'SP-250130-0001';

-- ดูคำขอที่รออนุมัติ
-- SELECT * FROM special_price_requests WHERE status = 'pending';

-- ดูคำขอของ Quote เฉพาะ
-- SELECT * FROM special_price_requests WHERE quote_no = 'Q-2025-001';
