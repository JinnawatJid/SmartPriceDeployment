# Implementation Plan: Item Data Migration from Business Central API

## Overview

This implementation plan breaks down the Item Data Migration feature into incremental coding tasks. The approach follows a bottom-up strategy: build core infrastructure first (database, API client), then build services on top, and finally wire everything together with APIs and scheduling.

## Tasks

- [x] 1. Set up database schema and models
  - Create SQL migration scripts for Item_Master and Item_Price tables
  - Create SQLAlchemy models (or equivalent ORM) for both tables
  - Add indexes and foreign key constraints
  - Write database connection utility functions
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [ ]* 1.1 Write unit tests for database schema
  - Test table creation and column types
  - Test foreign key CASCADE behavior
  - Test index existence
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2. Implement Business Central API Client
  - [x] 2.1 Create BCAPIClient class with configuration loading
    - Read ITEM_API_URL, ITEM_API_KEY, ITEMLEDGER_API_URL, ITEMLEDGER_API_KEY from environment
    - Implement connection initialization
    - _Requirements: 2.1_
  
  - [x] 2.2 Implement fetch_items method with pagination
    - Add skip and top parameters for OData pagination
    - Include Authorization header with API key
    - Parse JSON response into structured data
    - _Requirements: 2.2, 2.7, 3.8_
  
  - [x] 2.3 Implement fetch_inventory method
    - Query Item Ledger Entries API with Item_No_ filter
    - Parse response and return ledger entries
    - _Requirements: 2.2, 2.7_
  
  - [x] 2.4 Add retry logic and error handling
    - Implement exponential backoff for network errors and 5xx responses
    - Raise AuthenticationError for 401/403 without retry
    - Raise ClientError for other 4xx without retry
    - Add timeout handling (30s for Item API, 5s for Ledger API)
    - _Requirements: 2.3, 2.4, 2.5, 2.6_

- [ ]* 2.5 Write unit tests for BC API Client
  - Test configuration loading
  - Test retry logic with mocked network errors
  - Test error handling for different HTTP status codes
  - Test timeout behavior
  - _Requirements: 2.1, 2.3, 2.4, 2.5, 2.6_

- [ ]* 2.6 Write property test for API Client
  - **Property 4: Authorization Header Presence**
  - **Property 5: JSON Parsing Correctness**
  - **Validates: Requirements 2.2, 2.7**

- [x] 3. Implement Sync Job Service
  - [x] 3.1 Create SyncJobService class
    - Initialize with BCAPIClient and database connection
    - Implement field mapping function (API fields to DB columns)
    - _Requirements: 3.2_
  
  - [x] 3.2 Implement execute_sync method
    - Fetch all items from BC API using pagination
    - For each item: map fields and upsert to Item_Master
    - Set CreatedAt timestamp on new records
    - Log errors but continue processing
    - Return sync statistics (total, inserted, updated, errors)
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ]* 3.3 Write unit tests for Sync Job Service
  - Test that API is called with pagination
  - Test logging on success and errors
  - Test error handling continues with next item
  - _Requirements: 3.1, 3.6, 3.7, 3.8_

- [ ]* 3.4 Write property tests for Sync Job Service
  - **Property 1: API Field Mapping Consistency**
  - **Property 2: Upsert Idempotence**
  - **Property 3: Timestamp Consistency**
  - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

- [x] 4. Implement Inventory Query Service
  - [x] 4.1 Create InventoryQueryService class
    - Initialize with BCAPIClient and cache configuration
    - Set up in-memory cache with 60-second TTL (use cachetools or similar)
    - _Requirements: 4.6_
  
  - [x] 4.2 Implement get_inventory method
    - Check cache first, return if hit
    - Query BC Ledger API with SKU filter
    - Aggregate Quantity by Branch_Code
    - Handle empty results (return empty list)
    - Cache results before returning
    - Handle timeout (5 seconds)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 4.3 Write unit tests for Inventory Query Service
  - Test empty result handling (edge case)
  - Test timeout behavior
  - Test cache hit and miss scenarios
  - _Requirements: 4.3, 4.5, 4.6_

- [ ]* 4.4 Write property tests for Inventory Query Service
  - **Property 6: Inventory Aggregation Correctness**
  - **Property 7: Inventory Response Format**
  - **Validates: Requirements 4.2, 4.4**

- [x] 5. Checkpoint - Ensure core services work
  - Run all tests for BC API Client, Sync Job, and Inventory Service
  - Verify database schema is created correctly
  - Ask user if any questions arise

- [x] 6. Implement Price Upload Service
  - [x] 6.1 Create PriceUploadService class
    - Initialize with database connection
    - Implement file format validation (CSV and Excel)
    - Implement column validation (SKU, SDM, R2, R1, W2, W1)
    - _Requirements: 5.1, 5.2_
  
  - [x] 6.2 Implement process_upload method
    - Parse CSV or Excel file
    - For each row: validate SKU exists in Item_Master
    - Skip rows with invalid SKU and log warning
    - Upsert to Item_Price table (update if exists, insert if not)
    - Set UpdatedAt timestamp
    - Return summary with total_rows, successful_updates, errors
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [ ]* 6.3 Write property tests for Price Upload Service
  - **Property 8: File Format Validation**
  - **Property 9: Required Columns Validation**
  - **Property 10: SKU Existence Validation**
  - **Property 11: Invalid SKU Handling**
  - **Property 12: Upload Summary Completeness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.8**

- [ ]* 6.4 Write property tests for Price Upsert Logic
  - **Property 2: Upsert Idempotence** (for prices)
  - **Property 3: Timestamp Consistency** (for UpdatedAt)
  - **Validates: Requirements 5.5, 5.6, 5.7**

- [x] 7. Implement Item Query API endpoints
  - [x] 7.1 Create FastAPI router for items
    - Set up router with /items prefix
    - Initialize dependencies (database, InventoryQueryService)
    - _Requirements: 6.1_
  
  - [x] 7.2 Implement GET /items/{sku} endpoint
    - Query Item_Master by SKU
    - Join with Item_Price (left join)
    - Call InventoryQueryService for real-time inventory
    - Return combined response with all fields
    - Return 404 if SKU not found
    - Support query by No_2 as alternative
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  
  - [x] 7.3 Implement GET /items endpoint (list with filters)
    - Query Item_Master with optional filters (category, product_group, search)
    - Join with Item_Price
    - Apply pagination (limit, offset)
    - Return total count
    - Order by SKU ascending
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [ ]* 7.4 Write property tests for Item Query API
  - **Property 13: Item Query Response Completeness**
  - **Property 14: Alternative SKU Lookup**
  - **Property 15: Not Found Error Handling**
  - **Property 16: List Filtering Correctness**
  - **Property 17: Pagination Correctness**
  - **Property 18: Total Count Accuracy**
  - **Property 19: Result Ordering**
  - **Validates: Requirements 6.3, 6.4, 6.6, 6.7, 6.8, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7**

- [x] 8. Implement Migration Script
  - [x] 8.1 Create migration script to migrate from Items_Test
    - Read all records from Items_Test table
    - Map fields to Item_Master format
    - Insert into Item_Master if SKU doesn't exist (skip duplicates)
    - If price fields (SDM, R2, R1, W2, W1) are not null, insert into Item_Price
    - Log warnings for duplicate SKUs
    - Log summary statistics on completion
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.7_

- [ ]* 8.2 Write property tests for Migration Script
  - **Property 1: API Field Mapping Consistency** (for Items_Test mapping)
  - **Property 20: Migration Duplicate Handling**
  - **Validates: Requirements 8.2, 8.5**

- [ ]* 8.3 Write unit tests for Migration Script
  - Test reading from Items_Test
  - Test logging on completion
  - _Requirements: 8.1, 8.7_

- [x] 9. Implement Sync Job Scheduler
  - [x] 9.1 Create scheduler using APScheduler (or similar)
    - Configure job to run every 6 hours
    - Implement concurrent execution prevention (check if job is running)
    - Log each execution with start time, end time, status
    - _Requirements: 9.1, 9.2, 9.3, 9.6_
  
  - [x] 9.2 Create manual trigger API endpoint
    - POST /admin/sync-job/trigger endpoint
    - Execute sync job immediately regardless of schedule
    - Return job execution status
    - _Requirements: 9.4, 9.5_

- [ ]* 9.3 Write unit tests for Scheduler
  - Test schedule configuration
  - Test automatic execution
  - Test concurrent execution prevention
  - Test manual trigger
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 9.4 Write property test for Sync Job Logging
  - **Property 21: Sync Job Logging Completeness**
  - **Validates: Requirements 9.6, 10.4**

- [x] 10. Implement comprehensive logging
  - [x] 10.1 Set up logging configuration
    - Configure log format with timestamp, component name, level, message
    - Set up daily log rotation with 30-day retention
    - Configure log levels (ERROR for critical, WARN for recoverable)
    - _Requirements: 10.7_
  
  - [x] 10.2 Add logging to all components
    - BC API Client: log API failures with endpoint and parameters
    - Database operations: log SQL errors with statement
    - Sync Job: log execution summary
    - Price Upload: log file name and results
    - All errors: log with timestamp, component, message, stack trace
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 10.3 Write property tests for Logging
  - **Property 22: Error Logging Format**
  - **Property 23: Upload Logging Completeness**
  - **Property 24: Log Level Correctness**
  - **Validates: Requirements 10.1, 10.5, 10.6**

- [ ]* 10.4 Write unit tests for Logging
  - Test API failure logging
  - Test database error logging
  - Test log rotation configuration
  - _Requirements: 10.2, 10.3, 10.7_

- [x] 11. Create Price Upload API endpoint
  - [x] 11.1 Implement POST /admin/prices/upload endpoint
    - Accept CSV or Excel file upload
    - Call PriceUploadService to process file
    - Return upload summary (total_rows, successful, errors)
    - Handle validation errors and return appropriate HTTP status
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

- [x] 12. Integration and wiring
  - [x] 12.1 Wire all components together in main application
    - Initialize database connection pool
    - Initialize BC API Client with environment config
    - Initialize all services with dependencies
    - Register API routers
    - Start scheduler
    - _Requirements: All_
  
  - [x] 12.2 Create application startup script
    - Load environment variables
    - Run database migrations
    - Verify BC API connectivity
    - Start FastAPI application
    - _Requirements: All_

- [ ]* 12.3 Write integration tests
  - Test full sync job execution with mocked BC API
  - Test price upload end-to-end
  - Test item query with all data sources
  - Test list query with filters and pagination
  - _Requirements: All_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Run all unit tests
  - Run all property tests (minimum 100 iterations each)
  - Run all integration tests
  - Verify logging works correctly
  - Ask user if any questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties (minimum 100 iterations)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Use Python with FastAPI for API endpoints
- Use SQLAlchemy for ORM
- Use APScheduler for job scheduling
- Use hypothesis for property-based testing
- Use pytest for unit testing
