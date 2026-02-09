# Implementation Plan: Customer Data Caching System

## Overview

This implementation plan transforms the current real-time API-based customer search into a database-backed caching system. The work is organized into discrete phases: database setup, scheduled job implementation, endpoint modification, and testing. Each task builds incrementally to ensure the system remains functional throughout development.

## Tasks

- [x] 1. Database schema and migration setup
  - Create SQL migration script for Customer_Cache table with all required columns, indexes, and constraints
  - Create Python script to verify schema and run migrations
  - Test migration script is idempotent (can run multiple times safely)
  - _Requirements: 1.1, 1.2, 1.3, 9.1, 9.2, 9.3_

- [ ]* 1.1 Write unit tests for schema verification
  - Test table exists after migration
  - Test all columns exist with correct data types
  - Test primary key constraint on customer_code
  - Test indexes exist on customer_name, phone, last_updated
  - _Requirements: 1.1, 1.2, 1.3, 9.4_

- [x] 2. Create configuration module
  - Create `backend/config/cache_config.py` with feature flags, scheduler settings, batch sizes, and logging configuration
  - Add USE_DATABASE_CACHE flag for rollback capability
  - _Requirements: 7.1, 7.2, 10.3_

- [x] 3. Implement logging infrastructure
  - Create `backend/jobs/cache_logger.py` with daily rotating file handler
  - Configure logger for customer_cache with appropriate format
  - Set up log directory structure
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 4. Implement core analytics calculation functions
  - [ ] 4.1 Create `backend/jobs/customer_cache_refresh.py` module
    - Implement classify_group function (reuse logic from customer.py)
    - Implement calculate_analytics function to process invoice data
    - Calculate accum_6m, frequency, and all category sales (G, A, S, Y, C, E)
    - Calculate relevant_sales (max of category sales) and price_level
    - _Requirements: 2.5, 2.8, 5.1, 5.5_

  - [ ]* 4.2 Write property test for analytics calculation correctness
    - **Property 1: Analytics Calculation Correctness**
    - Generate random invoice lists with varying sizes and amounts
    - Verify accum_6m, frequency, category sales, relevant_sales, and price_level calculations
    - Run minimum 100 iterations
    - **Validates: Requirements 2.5, 5.1**

  - [ ]* 4.3 Write property test for SKU group classification
    - **Property 2: SKU Group Classification**
    - Generate random SKU strings with different first characters
    - Verify uppercase conversion and None handling for empty/null values
    - Run minimum 100 iterations
    - **Validates: Requirements 2.8, 5.5**

  - [ ]* 4.4 Write unit tests for analytics edge cases
    - Test with empty invoice list (should return all zeros)
    - Test with invoices outside 6-month window (should be excluded)
    - Test with NULL amounts (should treat as zero)
    - Test with missing SKU fields
    - _Requirements: 5.3, 5.4_

- [ ] 5. Checkpoint - Verify analytics calculations
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement data loading functions
  - [ ] 6.1 Implement load_all_customers_from_d365 function
    - Use existing CUSTOMER_API_URL and headers from config
    - Implement pagination with page size 500
    - Handle timeouts, connection errors, and HTTP errors gracefully
    - Return list of customer dictionaries
    - _Requirements: 2.2, 3.1, 3.6, 8.3_

  - [ ] 6.2 Implement load_invoices_for_customer function
    - Accept customer_code and calculation_date parameters
    - Calculate 6-month date range (calculation_date - 180 days)
    - Use existing INVOICE_API_URL and headers
    - Apply filters for customer_code and date range
    - Handle pagination and errors per customer
    - _Requirements: 2.4, 3.2_

  - [ ]* 6.3 Write unit tests for data loading error handling
    - Test API timeout handling with mock
    - Test connection error handling
    - Test HTTP error handling
    - Test invoice API failure for specific customer (should continue processing)
    - _Requirements: 3.1, 3.2, 3.6_

- [ ] 7. Implement database operations
  - [ ] 7.1 Create CustomerCacheRecord data model
    - Define dataclass with all customer fields and analytics
    - Implement to_api_response method for backward compatibility
    - Handle NULL value conversion to defaults
    - _Requirements: 4.3, 4.8, 5.4_

  - [ ] 7.2 Implement upsert_customer_batch function
    - Use MERGE statement for upsert operation
    - Process records in batches of 100
    - Handle errors per batch and continue processing
    - Use connection from get_mssql_conn()
    - _Requirements: 2.6, 3.3, 8.1, 8.2_

  - [ ]* 7.3 Write property test for database upsert idempotence
    - **Property 3: Database Upsert Idempotence**
    - Generate random customer records
    - Upsert same record multiple times
    - Verify only one record exists with latest timestamp
    - Verify updates work correctly
    - Run minimum 100 iterations
    - **Validates: Requirements 2.6**

  - [ ]* 7.4 Write property test for error resilience
    - **Property 4: Error Resilience in Batch Processing**
    - Generate batches with simulated random failures
    - Verify successful records are processed
    - Verify failure count is accurate
    - Run minimum 100 iterations
    - **Validates: Requirements 3.2, 3.3**

  - [ ]* 7.5 Write unit tests for database operations
    - Test upsert with new record (should insert)
    - Test upsert with existing record (should update)
    - Test batch upsert with mixed new/existing records
    - Test database connection failure handling
    - _Requirements: 2.6, 3.3_

- [ ] 8. Checkpoint - Verify database operations
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement main scheduled job orchestration
  - [ ] 9.1 Implement run_customer_cache_refresh function
    - Log start time and calculation_date
    - Call load_all_customers_from_d365
    - For each customer, call load_invoices_for_customer
    - Calculate analytics for each customer
    - Batch upsert to database
    - Log completion statistics (customers processed, updated, failed, duration)
    - Track errors and continue processing on failures
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 6.1, 6.2, 6.3, 8.5_

  - [ ] 9.2 Create JobExecutionResult data model
    - Track start_time, end_time, calculation_date
    - Track customers_processed, customers_updated, customers_failed
    - Track errors list
    - Calculate duration_seconds and avg_time_per_customer properties
    - _Requirements: 2.7, 8.5_

  - [ ]* 9.3 Write integration test for full job execution
    - Test full job against test database
    - Verify all customers processed
    - Verify analytics calculated correctly
    - Verify database populated with correct data
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [ ] 10. Implement scheduler configuration
  - [ ] 10.1 Set up APScheduler in main application
    - Configure BackgroundScheduler
    - Add job with CronTrigger for 21:00 daily
    - Set max_instances=1 to prevent concurrent runs
    - Start scheduler on application startup
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ] 10.2 Create manual trigger endpoint for testing
    - Add admin endpoint to manually trigger cache refresh
    - Add authentication/authorization check
    - Return job execution result
    - _Requirements: 7.3_

- [ ] 11. Modify search endpoints to use database
  - [ ] 11.1 Implement search_customer_from_db function
    - Connect to MSSQL using get_mssql_conn()
    - Build WHERE clause based on code, phone, or name parameters
    - Execute query and fetch customer record
    - Map database columns to CustomerCacheRecord
    - Convert to API response format using to_api_response()
    - Handle empty table scenario (return 503 error)
    - _Requirements: 4.1, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9, 3.5_

  - [ ] 11.2 Implement search_customer_list_from_db function
    - Connect to MSSQL
    - Normalize phone query (remove non-digits)
    - Build WHERE clause with OR conditions for code, name, phone
    - Limit results to 15 records
    - Return list of customer summaries
    - _Requirements: 4.2, 4.5, 4.6, 4.7_

  - [ ] 11.3 Modify search_customer endpoint
    - Check USE_DATABASE_CACHE flag
    - If True, call search_customer_from_db
    - If False, use original load_customer_from_api (preserve for rollback)
    - Maintain exact same response format
    - Handle database connection failures
    - _Requirements: 4.1, 4.3, 10.3, 10.4, 10.5_

  - [ ] 11.4 Modify search_customer_list endpoint
    - Check USE_DATABASE_CACHE flag
    - If True, call search_customer_list_from_db
    - If False, use original implementation
    - Maintain exact same response format
    - _Requirements: 4.2, 10.3, 10.4_

  - [ ]* 11.5 Write property test for response format compatibility
    - **Property 5: Response Format Backward Compatibility**
    - Generate random customer records
    - Convert to API response format
    - Verify all required fields present (id, name, tax_no, phone, gen_bus, customer_date, payment_terms, creditTerm, accum_6m, frequency, all category sales, price_level, relevantSales)
    - Verify data types match specification
    - Run minimum 100 iterations
    - **Validates: Requirements 4.3, 4.8, 4.9, 10.1**

  - [ ]* 11.6 Write property test for customer code exact match
    - **Property 6: Customer Code Exact Match**
    - Generate random customer codes and insert into test database
    - Search by exact code
    - Verify correct customer returned and only that customer
    - Run minimum 100 iterations
    - **Validates: Requirements 4.4**

  - [ ]* 11.7 Write property test for phone normalization
    - **Property 7: Phone Number Normalization**
    - Generate random phone numbers with various formats
    - Normalize and search
    - Verify matches work correctly regardless of formatting
    - Run minimum 100 iterations
    - **Validates: Requirements 4.5**

  - [ ]* 11.8 Write property test for case-insensitive name search
    - **Property 8: Case-Insensitive Name Search**
    - Generate random customer names
    - Generate random case variations of queries
    - Verify case-insensitive substring matching works
    - Run minimum 100 iterations
    - **Validates: Requirements 4.6**

  - [ ]* 11.9 Write property test for result limit enforcement
    - **Property 9: Result Limit Enforcement**
    - Generate test databases with varying customer counts
    - Generate queries that match different numbers of customers
    - Verify exactly 15 results returned when more than 15 match
    - Run minimum 100 iterations
    - **Validates: Requirements 4.7**

  - [ ]* 11.10 Write property test for NULL value handling
    - **Property 10: NULL Value Handling**
    - Generate customer/invoice data with random NULL values
    - Process through system
    - Verify no errors raised and appropriate defaults applied
    - Run minimum 100 iterations
    - **Validates: Requirements 5.4**

  - [ ]* 11.11 Write unit tests for search endpoint edge cases
    - Test search with no parameters (should return 400 error)
    - Test search with no results (should return 404 error)
    - Test search with empty table (should return 503 error)
    - Test exact match on customer code
    - Test phone normalization with formatted numbers
    - Test case-insensitive name search
    - _Requirements: 3.5, 4.4, 4.5, 4.6_

- [ ] 12. Checkpoint - Verify search endpoints
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Integration and end-to-end testing
  - [ ]* 13.1 Write integration tests for API endpoints
    - Test search endpoints against populated database
    - Verify response format matches original implementation
    - Test with various search parameters (code, phone, name)
    - Test error handling scenarios
    - _Requirements: 4.1, 4.2, 4.3, 10.1, 10.2_

  - [ ]* 13.2 Write integration tests for rollback capability
    - Test switching between database and API modes using USE_DATABASE_CACHE flag
    - Verify both modes produce equivalent results
    - Test configuration flag behavior
    - _Requirements: 10.3, 10.4, 10.5_

- [ ] 14. Documentation and deployment preparation
  - [ ] 14.1 Create deployment documentation
    - Document database migration steps
    - Document scheduler setup and configuration
    - Document monitoring and logging locations
    - Document rollback procedure
    - _Requirements: 9.1, 9.2, 7.1, 7.2, 10.3_

  - [ ] 14.2 Create operational runbook
    - Document how to manually trigger cache refresh
    - Document how to check job execution status
    - Document how to troubleshoot common issues
    - Document how to verify data freshness
    - _Requirements: 7.3, 6.1, 6.2, 6.3_

- [ ] 15. Final checkpoint - Complete system verification
  - Run all tests (unit, property, integration)
  - Verify scheduler is configured correctly
  - Verify logging is working
  - Verify database migration is ready
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis library with minimum 100 iterations per test
- Unit tests focus on specific examples and edge cases
- Integration tests verify end-to-end flows
- Checkpoints ensure incremental validation throughout development
- The USE_DATABASE_CACHE flag enables quick rollback to original implementation if needed
- All database operations use the existing get_mssql_conn() from backend/config/db_mssql.py
- The scheduled job runs at 21:00 daily to refresh data during low-traffic hours
