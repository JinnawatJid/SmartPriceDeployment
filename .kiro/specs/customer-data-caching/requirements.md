# Requirements Document: Customer Data Caching System

## Introduction

The current system loads all 30,000+ customer records from the D365 API and calculates analytics (6-month sales, frequency, category sales) in real-time for every search request. This causes significant performance issues and repeated API calls that strain both the application and the external API service.

This feature introduces a database-backed caching layer that pre-calculates and stores customer master data and analytics in an MSSQL database table. A scheduled job will refresh this data daily at 21:00 (9 PM), and the existing search endpoints will be modified to read from the database instead of making real-time API calls.

## Glossary

- **Customer_Cache_System**: The complete system including database table, scheduled job, and modified API endpoints
- **Customer_Table**: The MSSQL database table storing customer master data and pre-calculated analytics
- **Scheduled_Job**: The daily background process that refreshes customer data and analytics at 21:00
- **D365_API**: The external Dynamics 365 API that provides customer and invoice data
- **Invoice_API**: The external API endpoint that provides invoice transaction data
- **Search_Endpoint**: The FastAPI endpoints `/api/customer/search` and `/api/customer/search-list`
- **Analytics**: Pre-calculated metrics including 6-month sales totals, frequency, and category-specific sales
- **SKU_Group**: Product category classification (G, A, S, Y, C, E) based on the first character of the SKU
- **Upsert**: Database operation that inserts a new record or updates an existing one if it already exists
- **Lookback_Period**: The 6-month time window used for calculating sales analytics
- **Calculation_Date**: The anchor date used as the reference point for the 6-month lookback calculation

## Requirements

### Requirement 1: Database Table Creation

**User Story:** As a system administrator, I want a dedicated database table to store customer data and analytics, so that the system can serve search requests without calling external APIs.

#### Acceptance Criteria

1. THE Customer_Cache_System SHALL create a Customer_Table in the MSSQL database with the following columns:
   - customer_code (VARCHAR, primary key)
   - customer_name (NVARCHAR)
   - phone (VARCHAR)
   - tax_no (VARCHAR)
   - gen_bus (VARCHAR)
   - payment_terms (VARCHAR)
   - customer_date (DATE)
   - accum_6m (DECIMAL for total sales including VAT)
   - frequency (INTEGER for unique invoice count)
   - sales_g_cust (DECIMAL for SKU group G sales)
   - sales_a_cust (DECIMAL for SKU group A sales)
   - sales_s_cust (DECIMAL for SKU group S sales)
   - sales_y_cust (DECIMAL for SKU group Y sales)
   - sales_c_cust (DECIMAL for SKU group C sales)
   - sales_e_cust (DECIMAL for SKU group E sales)
   - relevant_sales (DECIMAL for maximum category sales)
   - price_level (DECIMAL, currently equals sales_e_cust)
   - last_updated (DATETIME for record update timestamp)
   - calculation_date (DATE for the anchor date used in 6-month calculation)

2. WHEN the Customer_Table is created, THE Customer_Cache_System SHALL set customer_code as the primary key with a unique constraint

3. THE Customer_Cache_System SHALL use appropriate data types and precision for DECIMAL columns to store monetary values without loss of precision

### Requirement 2: Scheduled Data Refresh Job

**User Story:** As a system administrator, I want customer data and analytics to be automatically refreshed daily, so that the cached data remains current without manual intervention.

#### Acceptance Criteria

1. THE Scheduled_Job SHALL execute daily at 21:00 (9 PM) server time

2. WHEN the Scheduled_Job executes, THE Customer_Cache_System SHALL load all customer records from the D365_API

3. WHEN the Scheduled_Job executes, THE Customer_Cache_System SHALL calculate the Calculation_Date as the current date at job execution time

4. FOR ALL customers loaded from D365_API, THE Scheduled_Job SHALL retrieve invoice data from the Invoice_API for the Lookback_Period (6 months before Calculation_Date)

5. FOR ALL customers with invoice data, THE Scheduled_Job SHALL calculate the following Analytics:
   - accum_6m: sum of "Amount Including VAT" for all invoices in the Lookback_Period
   - frequency: count of unique "Document No." values in the Lookback_Period
   - sales_g_cust: sum of "Amount Including VAT" for invoices where SKU_Group equals "G"
   - sales_a_cust: sum of "Amount Including VAT" for invoices where SKU_Group equals "A"
   - sales_s_cust: sum of "Amount Including VAT" for invoices where SKU_Group equals "S"
   - sales_y_cust: sum of "Amount Including VAT" for invoices where SKU_Group equals "Y"
   - sales_c_cust: sum of "Amount Including VAT" for invoices where SKU_Group equals "C"
   - sales_e_cust: sum of "Amount Including VAT" for invoices where SKU_Group equals "E"
   - relevant_sales: maximum value among all category sales
   - price_level: value equal to sales_e_cust

6. WHEN Analytics are calculated for a customer, THE Scheduled_Job SHALL upsert the customer record into the Customer_Table with last_updated set to the current timestamp

7. WHEN the Scheduled_Job completes successfully, THE Customer_Cache_System SHALL log the total number of customers processed and the execution duration

8. THE Scheduled_Job SHALL use the existing classify_group function logic to determine SKU_Group from the first character of the SKU

### Requirement 3: Error Handling and Resilience

**User Story:** As a system administrator, I want the scheduled job to handle errors gracefully, so that partial failures don't prevent the system from functioning with available data.

#### Acceptance Criteria

1. IF the D365_API fails to respond during the Scheduled_Job execution, THEN THE Customer_Cache_System SHALL log the error with timestamp and error details

2. IF the Invoice_API fails for a specific customer during the Scheduled_Job execution, THEN THE Customer_Cache_System SHALL log the error and continue processing remaining customers

3. WHEN a customer record fails to upsert into the Customer_Table, THE Scheduled_Job SHALL log the error with customer_code and continue processing remaining customers

4. IF the Scheduled_Job fails completely, THEN THE Search_Endpoint SHALL continue serving requests using existing data in the Customer_Table

5. WHEN the Customer_Table is empty and the Search_Endpoint receives a request, THE Customer_Cache_System SHALL return an appropriate error message indicating the system is initializing

6. THE Scheduled_Job SHALL implement a timeout mechanism for API calls to prevent indefinite hanging

### Requirement 4: Search Endpoint Modification

**User Story:** As a developer, I want the search endpoints to read from the database table instead of calling external APIs, so that search requests are fast and don't strain external services.

#### Acceptance Criteria

1. WHEN the `/api/customer/search` endpoint receives a request with code, phone, or name parameters, THE Search_Endpoint SHALL query the Customer_Table instead of calling the D365_API

2. WHEN the `/api/customer/search-list` endpoint receives a request with a query parameter, THE Search_Endpoint SHALL query the Customer_Table instead of calling the D365_API

3. THE Search_Endpoint SHALL maintain the exact same response format as the current implementation to ensure backward compatibility

4. WHEN searching by customer code, THE Search_Endpoint SHALL perform an exact match on the customer_code column

5. WHEN searching by phone, THE Search_Endpoint SHALL normalize phone numbers (remove non-digit characters) and perform a match on the normalized phone column

6. WHEN searching by name, THE Search_Endpoint SHALL perform a case-insensitive partial match on the customer_name column

7. WHEN the `/api/customer/search-list` endpoint returns results, THE Search_Endpoint SHALL limit results to 15 records maximum

8. THE Search_Endpoint SHALL return all required fields in the response including id, name, tax_no, phone, gen_bus, customer_date, payment_terms, accum_6m, frequency, all category sales fields, price_level, and relevantSales

9. THE Search_Endpoint SHALL map database column names to response field names to maintain API contract compatibility

### Requirement 5: Data Consistency and Integrity

**User Story:** As a system administrator, I want the cached data to accurately reflect the source data, so that users receive correct information in their searches.

#### Acceptance Criteria

1. WHEN the Scheduled_Job calculates Analytics, THE Customer_Cache_System SHALL use the same calculation logic as the current real-time implementation

2. THE Customer_Cache_System SHALL store the Calculation_Date with each customer record to enable audit and troubleshooting

3. WHEN a customer has no invoices in the Lookback_Period, THE Scheduled_Job SHALL store zero values for all Analytics fields

4. THE Scheduled_Job SHALL handle NULL and missing values in API responses by converting them to empty strings or zero values as appropriate

5. WHEN calculating SKU_Group, THE Customer_Cache_System SHALL use the first character of the SKU in uppercase

### Requirement 6: Monitoring and Observability

**User Story:** As a system administrator, I want comprehensive logging and monitoring of the scheduled job, so that I can troubleshoot issues and verify correct operation.

#### Acceptance Criteria

1. WHEN the Scheduled_Job starts, THE Customer_Cache_System SHALL log the start time and Calculation_Date

2. WHEN the Scheduled_Job processes customers, THE Customer_Cache_System SHALL log progress at regular intervals (e.g., every 1000 customers)

3. WHEN the Scheduled_Job completes, THE Customer_Cache_System SHALL log the completion time, total customers processed, total customers updated, and any error count

4. WHEN API calls fail, THE Customer_Cache_System SHALL log the customer_code, API endpoint, error message, and timestamp

5. WHEN database operations fail, THE Customer_Cache_System SHALL log the customer_code, operation type, error message, and timestamp

6. THE Customer_Cache_System SHALL maintain a separate log file for the Scheduled_Job with daily rotation

### Requirement 7: Scheduler Configuration

**User Story:** As a system administrator, I want the scheduled job to be configurable and manageable, so that I can adjust timing or trigger manual runs when needed.

#### Acceptance Criteria

1. THE Customer_Cache_System SHALL use a Python-based scheduler (APScheduler or similar) to manage the Scheduled_Job

2. THE Scheduled_Job SHALL be configured to run at 21:00 (9 PM) server time using a cron expression or equivalent

3. THE Customer_Cache_System SHALL provide a mechanism to manually trigger the Scheduled_Job outside the regular schedule

4. THE Scheduled_Job SHALL prevent concurrent executions (if a job is still running at the next scheduled time, skip the new execution)

5. THE Customer_Cache_System SHALL log a warning if a scheduled execution is skipped due to a previous job still running

### Requirement 8: Performance Optimization

**User Story:** As a system administrator, I want the scheduled job to complete efficiently, so that it doesn't consume excessive resources or take too long to execute.

#### Acceptance Criteria

1. THE Scheduled_Job SHALL process customers in batches to optimize database upsert operations

2. THE Scheduled_Job SHALL reuse database connections within a single execution to minimize connection overhead

3. WHEN loading data from D365_API, THE Scheduled_Job SHALL use pagination with a page size of at least 500 records to minimize API calls

4. THE Scheduled_Job SHALL implement connection pooling for database operations

5. WHEN the Scheduled_Job completes, THE Customer_Cache_System SHALL log the average processing time per customer

### Requirement 9: Database Migration and Initialization

**User Story:** As a developer, I want a database migration script to create the Customer_Table, so that the system can be deployed consistently across environments.

#### Acceptance Criteria

1. THE Customer_Cache_System SHALL provide a SQL migration script to create the Customer_Table with all required columns and constraints

2. THE migration script SHALL be idempotent (safe to run multiple times without errors)

3. THE migration script SHALL include appropriate indexes on customer_code, customer_name, and phone columns to optimize search queries

4. THE Customer_Cache_System SHALL provide a mechanism to verify the Customer_Table schema matches the expected structure

### Requirement 10: Backward Compatibility and Rollback

**User Story:** As a developer, I want the ability to rollback to the previous implementation if issues arise, so that the system remains operational during troubleshooting.

#### Acceptance Criteria

1. THE Search_Endpoint SHALL maintain the exact same API contract (request parameters and response format) as the current implementation

2. THE Customer_Cache_System SHALL preserve the existing API endpoint paths and HTTP methods

3. THE Customer_Cache_System SHALL provide a configuration flag to switch between database-backed and API-backed implementations

4. WHEN the configuration flag is set to API-backed mode, THE Search_Endpoint SHALL use the original load_customer_from_api function

5. THE Customer_Cache_System SHALL not remove the existing API-based implementation code to enable quick rollback
