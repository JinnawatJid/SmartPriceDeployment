-- =====================================================
-- Full-Text Search Setup for Customer Table
-- =====================================================
-- ใช้สำหรับค้นหาลูกค้าแบบ Full-Text Search (ถ้าต้องการ)
-- รันใน SSMS หรือ Azure Data Studio

-- =====================================================
-- 1. สร้าง Full-Text Catalog
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'CustomerCatalog')
BEGIN
    CREATE FULLTEXT CATALOG CustomerCatalog AS DEFAULT;
    PRINT '✅ Created Full-Text Catalog: CustomerCatalog';
END
ELSE
BEGIN
    PRINT '⚠️ Full-Text Catalog already exists: CustomerCatalog';
END
GO

-- =====================================================
-- 2. สร้าง Full-Text Index บน Customer table
-- =====================================================
-- ต้องมี Primary Key หรือ Unique Index ก่อน
IF NOT EXISTS (SELECT * FROM sys.fulltext_indexes WHERE object_id = OBJECT_ID('Customer'))
BEGIN
    CREATE FULLTEXT INDEX ON Customer
    (
        customer_code LANGUAGE 1033,  -- English
        customer_name LANGUAGE 1054   -- Thai
    )
    KEY INDEX PK_Customer  -- ⚠️ เปลี่ยนเป็นชื่อ Primary Key ของคุณ
    ON CustomerCatalog
    WITH CHANGE_TRACKING AUTO;
    
    PRINT '✅ Created Full-Text Index on Customer table';
END
ELSE
BEGIN
    PRINT '⚠️ Full-Text Index already exists on Customer table';
END
GO

-- =====================================================
-- 3. ตัวอย่างการใช้งาน Full-Text Search
-- =====================================================

-- 3.1 ค้นหาแบบ CONTAINS (exact word)
SELECT TOP 15
    customer_code, customer_name, phone, tax_no
FROM Customer
WHERE CONTAINS(customer_name, '"จำรัส"')
ORDER BY customer_name;

-- 3.2 ค้นหาแบบ FREETEXT (fuzzy search)
SELECT TOP 15
    customer_code, customer_name, phone, tax_no
FROM Customer
WHERE FREETEXT(customer_name, 'จำรัส')
ORDER BY customer_name;

-- 3.3 ค้นหาแบบ prefix (starts with)
SELECT TOP 15
    customer_code, customer_name, phone, tax_no
FROM Customer
WHERE CONTAINS(customer_code, '"08015*"')
ORDER BY customer_code;

-- 3.4 ค้นหาหลายคอลัมน์พร้อมกัน
SELECT TOP 15
    customer_code, customer_name, phone, tax_no
FROM Customer
WHERE CONTAINS((customer_code, customer_name), '"08015*" OR "จำรัส"')
ORDER BY customer_name;

-- =====================================================
-- 4. ตรวจสอบสถานะ Full-Text Index
-- =====================================================
SELECT 
    OBJECT_NAME(object_id) AS table_name,
    is_enabled,
    change_tracking_state_desc,
    crawl_type_desc,
    crawl_start_date,
    crawl_end_date
FROM sys.fulltext_indexes
WHERE object_id = OBJECT_ID('Customer');

-- =====================================================
-- 5. Rebuild Full-Text Index (ถ้าจำเป็น)
-- =====================================================
-- ALTER FULLTEXT INDEX ON Customer START FULL POPULATION;

-- =====================================================
-- 6. Drop Full-Text Index (ถ้าต้องการลบ)
-- =====================================================
-- DROP FULLTEXT INDEX ON Customer;
-- DROP FULLTEXT CATALOG CustomerCatalog;
