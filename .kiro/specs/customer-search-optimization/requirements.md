# Requirements Document

## Introduction

The current customer search system loads all 30,000+ customer records from the D365 API into memory before performing local searches. This approach causes significant performance issues, particularly slow initial load times where users must wait for all data to load before they can search. This specification defines requirements for implementing server-side search that queries the D365 API directly with search parameters, returning only matching results instead of loading the entire dataset.

## Glossary

- **D365 API**: Microsoft Dynamics 365 API that provides customer data
- **Search_Service**: Backend service responsible for handling customer search requests
- **Customer_Record**: A single customer entity containing code, name, phone, and other attributes
- **Search_Query**: User input containing search terms (customer code, name, or phone number)
- **Result_Set**: Collection of Customer_Records matching the Search_Query
- **Frontend_Client**: React-based user interface with autocomplete search functionality
- **Backend_API**: Python FastAPI service that interfaces with D365 API

## Requirements

### Requirement 1: Server-Side Search Implementation

**User Story:** As a system user, I want the search to query the D365 API directly with filters, so that I don't have to wait for all 30,000+ customer records to load before searching.

#### Acceptance Criteria

1. WHEN a Search_Query is submitted, THE Search_Service SHALL send a filtered request to the D365 API with search parameters
2. THE Search_Service SHALL use D365 API filter operators ($eq, $contains) to filter results at the API level
3. THE Search_Service SHALL NOT load all Customer_Records into memory before performing searches
4. WHEN the D365 API returns filtered results, THE Search_Service SHALL process only the returned Customer_Records

### Requirement 2: Search Functionality Preservation

**User Story:** As a system user, I want to search by customer code, name, or phone number, so that I can find customers using any identifying information I have.

#### Acceptance Criteria

1. WHEN a Search_Query contains a customer code, THE Search_Service SHALL filter by customer_code field using exact match
2. WHEN a Search_Query contains a customer name, THE Search_Service SHALL filter by customer_name field using partial match
3. WHEN a Search_Query contains a phone number, THE Search_Service SHALL filter by phone field using normalized digit comparison
4. THE Search_Service SHALL support searching with any combination of code, name, or phone parameters

### Requirement 3: Result Limiting

**User Story:** As a system user, I want search results limited to a reasonable number, so that the response is fast and manageable.

#### Acceptance Criteria

1. WHEN the Search_Service queries the D365 API for autocomplete results, THE Search_Service SHALL limit results to 15 Customer_Records
2. WHEN the Search_Service queries the D365 API for exact match searches, THE Search_Service SHALL return the first matching Customer_Record
3. THE Search_Service SHALL use D365 API pagination parameters to limit the number of records retrieved

### Requirement 4: Response Format Compatibility

**User Story:** As a frontend developer, I want the API response format to remain unchanged, so that existing frontend code continues to work without modifications.

#### Acceptance Criteria

1. THE Search_Service SHALL return Customer_Records with fields: id, name, phone, tax_no
2. WHEN returning full customer details, THE Search_Service SHALL include all existing fields (accum_6m, frequency, sales data, payment terms)
3. THE Search_Service SHALL maintain the same JSON structure for both /api/customer/search and /api/customer/search-list endpoints
4. THE Search_Service SHALL preserve all data transformation logic (phone normalization, field mapping)

### Requirement 5: Performance Improvement

**User Story:** As a system user, I want significantly faster search response times, so that I can find customers quickly without waiting.

#### Acceptance Criteria

1. WHEN a Search_Query is submitted, THE Search_Service SHALL return results without loading all 30,000+ Customer_Records
2. THE Search_Service SHALL eliminate the initial data loading delay for first-time searches
3. WHEN the D365 API responds, THE Search_Service SHALL process and return results within the API response time plus minimal processing overhead

### Requirement 6: Cache Strategy Optimization

**User Story:** As a system administrator, I want intelligent caching that doesn't cache all customer data, so that memory usage is optimized.

#### Acceptance Criteria

1. THE Search_Service SHALL remove the global customer data cache that stores all 30,000+ Customer_Records
2. WHERE search result caching is implemented, THE Search_Service SHALL cache individual search results with appropriate TTL
3. THE Search_Service SHALL limit cache size to prevent unbounded memory growth
4. WHEN cache size exceeds limits, THE Search_Service SHALL evict oldest entries

### Requirement 7: Error Handling and Fallback

**User Story:** As a system user, I want graceful error handling when the D365 API is unavailable, so that I receive clear error messages.

#### Acceptance Criteria

1. WHEN the D365 API request times out, THE Search_Service SHALL return an appropriate error message to the Frontend_Client
2. WHEN the D365 API returns an error, THE Search_Service SHALL log the error and return a user-friendly message
3. IF a search returns no results, THEN THE Search_Service SHALL return an empty Result_Set with HTTP 200 status
4. THE Search_Service SHALL NOT fall back to loading all customer data when API queries fail

### Requirement 8: Backward Compatibility

**User Story:** As a system maintainer, I want the existing endpoints to continue working, so that the frontend requires no changes.

#### Acceptance Criteria

1. THE Search_Service SHALL maintain the /api/customer/search endpoint with existing query parameters
2. THE Search_Service SHALL maintain the /api/customer/search-list endpoint with existing query parameters
3. THE Search_Service SHALL support both GET and POST methods for search endpoints
4. WHEN the Frontend_Client calls existing endpoints, THE Search_Service SHALL return responses in the same format as before
