-- =====================================================
-- Full-Text Search Setup for Items_Test Table
-- =====================================================
-- ⭐ สคริปต์นี้จะสร้าง Full-Text Index สำหรับตาราง Items_Test
-- เพื่อให้การค้นหาสินค้าเร็วขึ้นมาก (เร็วกว่า LIKE หลายเท่า)
-- =====================================================

USE [Quetung];
GO

-- =====================================================
-- 1. สร้าง Full-Text Catalog (ถ้ายังไม่มี)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.fulltext_catalogs WHERE name = 'ItemsCatalog')
BEGIN
    CREATE FULLTEXT CATALOG ItemsCatalog AS DEFAULT;
    PRINT '✅ Created Full-Text Catalog: ItemsCatalog';
END
ELSE
BEGIN
    PRINT 'ℹ️  Full-Text Catalog already exists: ItemsCatalog';
END
GO

-- =====================================================
-- 2. สร้าง Full-Text Index บน Items_Test
-- =====================================================
-- ⚠️ ต้องมี Primary Key หรือ Unique Index ก่อน
-- ตรวจสอบว่ามี Primary Key หรือไม่
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE object_id = OBJECT_ID('Items_Test') 
    AND is_primary_key = 1
)
BEGIN
    PRINT '⚠️  WARNING: Items_Test ไม่มี Primary Key!';
    PRINT '   กำลังสร้าง Primary Key บน No...';
    
    -- สร้าง Primary Key ถ้ายังไม่มี
    ALTER TABLE Items_Test
    ADD CONSTRAINT PK_Items_Test PRIMARY KEY (No);
    
    PRINT '✅ Created Primary Key on Items_Test.No';
END
GO

-- สร้าง Full-Text Index
IF NOT EXISTS (SELECT * FROM sys.fulltext_indexes WHERE object_id = OBJECT_ID('Items_Test'))
BEGIN
    CREATE FULLTEXT INDEX ON Items_Test
    (
        No LANGUAGE 1033,              -- SKU (English)
        No_2 LANGUAGE 1033,            -- SKU2 (English)
        Description LANGUAGE 1054,     -- ชื่อสินค้า (Thai)
        AlternateName LANGUAGE 1054    -- ชื่อสำรอง (Thai)
    )
    KEY INDEX PK_Items_Test
    ON ItemsCatalog
    WITH CHANGE_TRACKING AUTO;
    
    PRINT '✅ Created Full-Text Index on Items_Test';
    PRINT '   Indexed columns: No, No_2, Description, AlternateName';
END
ELSE
BEGIN
    PRINT 'ℹ️  Full-Text Index already exists on Items_Test';
END
GO

-- =====================================================
-- 3. ทดสอบการค้นหา
-- =====================================================

PRINT '';
PRINT '=====================================================';
PRINT 'ทดสอบการค้นหา Full-Text Search';
PRINT '=====================================================';

-- 3.1 ค้นหาด้วย SKU (prefix search)
PRINT '';
PRINT '1. ค้นหา SKU ที่ขึ้นต้นด้วย "A01"';
SELECT TOP 10
    No, No_2, Description, Inventory_Posting_Group
FROM Items_Test
WHERE CONTAINS((No, No_2), '"A01*"')
ORDER BY No;

-- 3.2 ค้นหาด้วยชื่อสินค้า (fuzzy search)
PRINT '';
PRINT '2. ค้นหาสินค้าที่มีคำว่า "อลูมิเนียม"';
SELECT TOP 10
    No, No_2, Description, Inventory_Posting_Group
FROM Items_Test
WHERE FREETEXT((Description, AlternateName), 'อลูมิเนียม')
ORDER BY No;

-- 3.3 ค้นหาแบบผสม (SKU หรือ ชื่อ)
PRINT '';
PRINT '3. ค้นหา SKU หรือชื่อที่มี "กระจก"';
SELECT TOP 10
    No, No_2, Description, Inventory_Posting_Group
FROM Items_Test
WHERE CONTAINS((No, No_2), '"G*"')
   OR FREETEXT((Description, AlternateName), 'กระจก')
ORDER BY No;

-- =====================================================
-- 4. ตรวจสอบสถานะ Full-Text Index
-- =====================================================
PRINT '';
PRINT '=====================================================';
PRINT 'สถานะ Full-Text Index';
PRINT '=====================================================';

SELECT 
    OBJECT_NAME(object_id) AS table_name,
    is_enabled,
    change_tracking_state_desc,
    has_crawl_completed,
    crawl_type_desc,
    crawl_start_date,
    crawl_end_date
FROM sys.fulltext_indexes
WHERE object_id = OBJECT_ID('Items_Test');

-- =====================================================
-- 5. Rebuild Full-Text Index (ถ้าจำเป็น)
-- =====================================================
-- ⚠️ ใช้เมื่อข้อมูลมีการเปลี่ยนแปลงมาก หรือ search ไม่ค่อยแม่นยำ
-- ALTER FULLTEXT INDEX ON Items_Test START FULL POPULATION;

-- =====================================================
-- 6. Drop Full-Text Index (ถ้าต้องการลบ)
-- =====================================================
-- DROP FULLTEXT INDEX ON Items_Test;
-- DROP FULLTEXT CATALOG ItemsCatalog;

PRINT '';
PRINT '✅ Full-Text Search Setup Complete!';
PRINT '';
PRINT 'หมายเหตุ:';
PRINT '- Full-Text Index จะทำงานอัตโนมัติเมื่อมีการเพิ่ม/แก้ไข/ลบข้อมูล';
PRINT '- ถ้าต้องการ rebuild: ALTER FULLTEXT INDEX ON Items_Test START FULL POPULATION;';
PRINT '- ตรวจสอบสถานะ: SELECT * FROM sys.fulltext_indexes WHERE object_id = OBJECT_ID(''Items_Test'')';
