# Requirements Document

## Introduction

ระบบนี้จะทำการย้ายข้อมูล Item จากโครงสร้างเดิม (ตาราง Items_Test ที่เก็บข้อมูลทั้งหมดในตารางเดียว) ไปเป็นโครงสร้างใหม่ที่แยกเป็น 2 ตาราง (Item_Master และ Item_Price) โดยดึงข้อมูลจาก Business Central API แทนการใช้ข้อมูลที่เก็บไว้ในตาราง ระบบจะ sync ข้อมูล Item Master จาก API มาเก็บใน MSSQL และดึงข้อมูล Inventory แบบ real-time จาก Item Ledger Entries API

## Glossary

- **Item_Master**: ตารางเก็บข้อมูลหลักของสินค้า (SKU, Description, Unit, Category, etc.)
- **Item_Price**: ตารางเก็บข้อมูลราคาสินค้าที่พนักงาน upload
- **Items_Test**: ตารางเดิมที่เก็บข้อมูลทั้งหมดในตารางเดียว (legacy table)
- **SKU**: รหัสสินค้าหลัก (Primary Key) ที่ใช้ในการ map ข้อมูลระหว่างตาราง
- **BC_API_Client**: Client สำหรับเชื่อมต่อกับ Business Central API
- **SP683_Item_API**: Business Central API endpoint สำหรับดึงข้อมูล Item Master
- **SP683_Item_Ledger_API**: Business Central API endpoint สำหรับดึงข้อมูล Inventory แบบ real-time
- **Sync_Job**: Background job สำหรับ sync ข้อมูลจาก API มายัง MSSQL
- **Price_Upload_Service**: Service สำหรับรับการ upload ราคาจากพนักงาน
- **Inventory_Query_Service**: Service สำหรับดึงข้อมูล Inventory แบบ real-time

## Requirements

### Requirement 1: Database Schema Creation

**User Story:** ในฐานะ System Administrator ฉันต้องการสร้างโครงสร้างตารางใหม่ เพื่อแยกข้อมูล Item Master และ Price ออกจากกัน

#### Acceptance Criteria

1. THE System SHALL create Item_Master table with columns: SKU (PK, varchar), No_2 (varchar), Description (nvarchar), Base_Unit_of_Measure (varchar), Inventory_Posting_Group (varchar), Product_Group (varchar), Product_Sub_Group (varchar), RE (decimal), CreatedAt (datetime)
2. THE System SHALL create Item_Price table with columns: SKU (PK/FK, varchar), SDM (decimal), R2 (decimal), R1 (decimal), W2 (decimal), W1 (decimal), UpdatedAt (datetime)
3. THE System SHALL create foreign key constraint from Item_Price.SKU to Item_Master.SKU with ON DELETE CASCADE
4. THE System SHALL create index on Item_Master.SKU for fast lookup
5. THE System SHALL create index on Item_Master.Inventory_Posting_Group for category filtering
6. THE System SHALL create index on Item_Master.Product_Group for product group filtering

### Requirement 2: Business Central API Client

**User Story:** ในฐานะ Developer ฉันต้องการ API client สำหรับเชื่อมต่อกับ Business Central เพื่อดึงข้อมูล Item และ Inventory

#### Acceptance Criteria

1. THE BC_API_Client SHALL read connection configuration from environment variables (ITEM_API_URL, ITEM_API_KEY, ITEMLEDGER_API_URL, ITEMLEDGER_API_KEY)
2. WHEN BC_API_Client makes API request, THE BC_API_Client SHALL include API key in Authorization header
3. WHEN API request fails with network error, THE BC_API_Client SHALL retry up to 3 times with exponential backoff
4. WHEN API returns 401 or 403 status, THE BC_API_Client SHALL raise authentication error without retry
5. WHEN API returns 5xx status, THE BC_API_Client SHALL retry the request
6. WHEN API returns 4xx status (except 401/403), THE BC_API_Client SHALL raise client error without retry
7. THE BC_API_Client SHALL parse JSON response and return structured data

### Requirement 3: Item Master Data Synchronization

**User Story:** ในฐานะ System Administrator ฉันต้องการ sync ข้อมูล Item Master จาก Business Central API มายัง MSSQL เพื่อให้สามารถ query ได้เร็ว

#### Acceptance Criteria

1. WHEN Sync_Job executes, THE Sync_Job SHALL fetch all items from SP683_Item_API
2. WHEN Sync_Job receives item data, THE Sync_Job SHALL map API fields to database columns: No_ to SKU, No_2 to No_2, Description to Description, Base_Unit_of_Measure to Base_Unit_of_Measure, Inventory_Posting_Group to Inventory_Posting_Group, Product_Group to Product_Group, Product_Subgroup to Product_Sub_Group, Unit_Cost to RE
3. WHEN item SKU exists in Item_Master, THE Sync_Job SHALL update the existing record with new data
4. WHEN item SKU does not exist in Item_Master, THE Sync_Job SHALL insert new record
5. WHEN Sync_Job inserts new record, THE Sync_Job SHALL set CreatedAt to current timestamp
6. WHEN Sync_Job completes successfully, THE Sync_Job SHALL log total items synced and execution time
7. WHEN Sync_Job encounters error, THE Sync_Job SHALL log error details and continue with next item
8. THE Sync_Job SHALL support pagination when fetching items from API

### Requirement 4: Real-time Inventory Query

**User Story:** ในฐานะ Sales Representative ฉันต้องการดูข้อมูล Inventory แบบ real-time เพื่อให้ข้อมูลที่ถูกต้องกับลูกค้า

#### Acceptance Criteria

1. WHEN Inventory_Query_Service receives SKU, THE Inventory_Query_Service SHALL query SP683_Item_Ledger_API with Item_No_ filter
2. WHEN SP683_Item_Ledger_API returns ledger entries, THE Inventory_Query_Service SHALL sum Quantity field grouped by Branch_Code
3. WHEN SP683_Item_Ledger_API returns empty result, THE Inventory_Query_Service SHALL return zero inventory for all branches
4. THE Inventory_Query_Service SHALL return inventory data as list of objects with branch and quantity fields
5. WHEN API query takes longer than 5 seconds, THE Inventory_Query_Service SHALL timeout and return error
6. THE Inventory_Query_Service SHALL cache inventory results for 60 seconds to reduce API calls

### Requirement 5: Price Upload Integration

**User Story:** ในฐานะ Sales Manager ฉันต้องการ upload ราคาสินค้าเข้าระบบ เพื่ออัพเดทราคาให้เป็นปัจจุบัน

#### Acceptance Criteria

1. WHEN Price_Upload_Service receives price file, THE Price_Upload_Service SHALL validate file format is CSV or Excel
2. WHEN Price_Upload_Service parses price file, THE Price_Upload_Service SHALL validate required columns: SKU, SDM, R2, R1, W2, W1
3. WHEN Price_Upload_Service validates SKU, THE Price_Upload_Service SHALL check SKU exists in Item_Master table
4. WHEN SKU does not exist in Item_Master, THE Price_Upload_Service SHALL skip that row and log warning
5. WHEN SKU exists in Item_Master and exists in Item_Price, THE Price_Upload_Service SHALL update existing price record
6. WHEN SKU exists in Item_Master and does not exist in Item_Price, THE Price_Upload_Service SHALL insert new price record
7. WHEN Price_Upload_Service updates or inserts price, THE Price_Upload_Service SHALL set UpdatedAt to current timestamp
8. WHEN Price_Upload_Service completes, THE Price_Upload_Service SHALL return summary with total rows processed, successful updates, and errors

### Requirement 6: Item Query API

**User Story:** ในฐานะ Frontend Developer ฉันต้องการ API endpoint สำหรับดึงข้อมูล Item พร้อมราคาและ Inventory เพื่อแสดงผลบน UI

#### Acceptance Criteria

1. WHEN Item_Query_API receives GET request with SKU, THE Item_Query_API SHALL query Item_Master table by SKU
2. WHEN Item_Master record exists, THE Item_Query_API SHALL join with Item_Price table using SKU
3. WHEN Item_Price record exists, THE Item_Query_API SHALL include price data in response
4. WHEN Item_Price record does not exist, THE Item_Query_API SHALL return null for all price fields
5. WHEN Item_Query_API retrieves item data, THE Item_Query_API SHALL call Inventory_Query_Service to get real-time inventory
6. THE Item_Query_API SHALL return combined data with item master fields, price fields, and inventory fields
7. WHEN SKU does not exist in Item_Master, THE Item_Query_API SHALL return 404 status with error message
8. THE Item_Query_API SHALL support query by No_2 field as alternative to SKU

### Requirement 7: Item List API with Filtering

**User Story:** ในฐานะ Sales Representative ฉันต้องการดูรายการสินค้าพร้อม filter ตาม category และ product group เพื่อค้นหาสินค้าได้ง่าย

#### Acceptance Criteria

1. WHEN Item_List_API receives GET request, THE Item_List_API SHALL query Item_Master table
2. WHEN request includes category filter, THE Item_List_API SHALL filter by Inventory_Posting_Group field
3. WHEN request includes product_group filter, THE Item_List_API SHALL filter by Product_Group field
4. WHEN request includes search term, THE Item_List_API SHALL search in SKU, No_2, and Description fields using LIKE operator
5. THE Item_List_API SHALL support pagination with limit and offset parameters
6. THE Item_List_API SHALL return total count of items matching filters
7. THE Item_List_API SHALL return items ordered by SKU ascending
8. THE Item_List_API SHALL join with Item_Price table to include price data in list response

### Requirement 8: Data Migration from Legacy Table

**User Story:** ในฐานะ System Administrator ฉันต้องการ migrate ข้อมูลจาก Items_Test ไปยังตารางใหม่ เพื่อรักษาข้อมูลเดิมไว้

#### Acceptance Criteria

1. THE Migration_Script SHALL read all records from Items_Test table
2. WHEN Migration_Script processes Items_Test record, THE Migration_Script SHALL map No to SKU, No_2 to No_2, Description to Description, Base_Unit_of_Measure to Base_Unit_of_Measure, Inventory_Posting_Group to Inventory_Posting_Group, Product_Group to Product_Group, Product_Sub_Group to Product_Sub_Group
3. WHEN Migration_Script processes Items_Test record, THE Migration_Script SHALL insert into Item_Master if SKU does not exist
4. WHEN Migration_Script processes price fields (SDM, R2, R1, W2, W1), THE Migration_Script SHALL insert into Item_Price if any price field is not null
5. WHEN Migration_Script encounters duplicate SKU, THE Migration_Script SHALL skip and log warning
6. THE Migration_Script SHALL run as one-time operation and not be part of regular sync
7. WHEN Migration_Script completes, THE Migration_Script SHALL log total records migrated to Item_Master and Item_Price

### Requirement 9: Scheduled Synchronization

**User Story:** ในฐานะ System Administrator ฉันต้องการให้ระบบ sync ข้อมูล Item Master อัตโนมัติ เพื่อให้ข้อมูลเป็นปัจจุบันเสมอ

#### Acceptance Criteria

1. THE System SHALL schedule Sync_Job to run every 6 hours
2. WHEN scheduled time arrives, THE System SHALL execute Sync_Job automatically
3. WHEN Sync_Job is already running, THE System SHALL skip new execution and log warning
4. THE System SHALL support manual trigger of Sync_Job via API endpoint
5. WHEN manual trigger is requested, THE System SHALL execute Sync_Job immediately regardless of schedule
6. THE System SHALL log each Sync_Job execution with start time, end time, and status

### Requirement 10: Error Handling and Logging

**User Story:** ในฐานะ System Administrator ฉันต้องการ log และ error handling ที่ดี เพื่อ debug ปัญหาได้ง่าย

#### Acceptance Criteria

1. WHEN any component encounters error, THE System SHALL log error with timestamp, component name, error message, and stack trace
2. WHEN BC_API_Client fails after all retries, THE System SHALL log API endpoint, request parameters, and final error
3. WHEN database operation fails, THE System SHALL log SQL statement and error details
4. THE System SHALL log all Sync_Job executions with summary statistics
5. THE System SHALL log all Price_Upload_Service operations with file name and processing results
6. WHEN System logs error, THE System SHALL use ERROR level for critical errors and WARN level for recoverable issues
7. THE System SHALL rotate log files daily and keep logs for 30 days
