# Requirements Document: Branch-Based Product Filtering

## Introduction

This feature migrates the product data source from the legacy Items_Test table to the normalized Item_Master + Item_Price tables with branch-based filtering. The system currently serves product data from a single Items_Test table without branch separation. The new system will filter products, prices, and inventory based on the employee's branch, ensuring users only see items available in their location.

## Glossary

- **Item_Master**: Normalized table containing core product information (SKU, description, product groups, unit of measure)
- **Item_Price**: Normalized table containing branch-specific pricing (composite primary key: SKU + BranchCode)
- **Items_Test**: Legacy table containing all product data in a single denormalized structure
- **Product_Router**: FastAPI router handling all product-related endpoints (products_router.py)
- **BC_API**: Business Central API providing real-time inventory data via Item Ledger Entries
- **JWT_Token**: JSON Web Token containing employee authentication data (employeeId, name, branchCode)
- **Branch_Code**: Unique identifier for a branch location (e.g., "BS" for Bangkok South)
- **SKU**: Stock Keeping Unit - unique product identifier
- **Category_Prefix**: First character of SKU indicating product category (G=Glass, A=Aluminium, C=C-Line, S=Sealant, Y=Gypsum, E=Accessories)
- **Auth_Middleware**: Middleware component that extracts and validates JWT tokens from HTTP requests
- **Inventory_Service**: Service layer handling branch-specific inventory queries and caching

## Requirements

### Requirement 1: JWT Token Extraction

**User Story:** As a system, I want to extract branch_code from JWT tokens, so that I can filter products by the employee's branch.

#### Acceptance Criteria

1. WHEN an authenticated request is received, THE Auth_Middleware SHALL extract the JWT token from the Authorization header
2. WHEN a JWT token is decoded, THE Auth_Middleware SHALL extract the branchId claim and make it available to route handlers
3. IF the JWT token is missing or invalid, THEN THE Auth_Middleware SHALL return a 401 Unauthorized error
4. IF the branchId claim is missing from the token, THEN THE Auth_Middleware SHALL return a 400 Bad Request error with a descriptive message
5. THE Auth_Middleware SHALL validate that the extracted branch_code exists in the Branch table before proceeding

### Requirement 2: Product Data Source Migration

**User Story:** As a developer, I want to replace Items_Test queries with Item_Master + Item_Price joins, so that the system uses normalized tables.

#### Acceptance Criteria

1. WHEN loading product data, THE Product_Router SHALL query Item_Master for core product information
2. WHEN loading product prices, THE Product_Router SHALL LEFT JOIN Item_Price filtered by branch_code
3. WHEN a product has no price record for the requested branch, THE Product_Router SHALL return the product with null price fields
4. THE Product_Router SHALL maintain the existing response format to ensure backward compatibility
5. THE Product_Router SHALL map Item_Master columns to the existing response field names (No. → sku, Description → name, etc.)

### Requirement 3: Branch-Based Price Filtering

**User Story:** As an employee, I want to see prices specific to my branch, so that I can quote accurate prices to customers.

#### Acceptance Criteria

1. WHEN fetching product prices, THE Product_Router SHALL filter Item_Price records by the employee's branch_code
2. WHEN multiple price records exist for a SKU, THE Product_Router SHALL return only the record matching the employee's branch_code
3. WHEN no price record exists for the employee's branch, THE Product_Router SHALL return null for all price fields (SDM, R1, R2, W1, W2)
4. THE Product_Router SHALL include the UpdatedAt timestamp from Item_Price in the response
5. THE Product_Router SHALL return price fields with the same names as the legacy system (priceR1, priceR2, priceW1, priceW2)

### Requirement 4: Branch-Based Inventory Filtering

**User Story:** As an employee, I want to see inventory quantities for my branch only, so that I know what products are available at my location.

#### Acceptance Criteria

1. WHEN fetching inventory data, THE Inventory_Service SHALL query BC_API Item Ledger Entries filtered by Branch_Code
2. WHEN aggregating inventory, THE Inventory_Service SHALL sum quantities only for the employee's branch_code
3. WHEN inventory data is unavailable from BC_API, THE Inventory_Service SHALL return an empty inventory list and log the error
4. THE Inventory_Service SHALL cache branch-specific inventory data to minimize API calls
5. WHEN inventory cache is stale, THE Inventory_Service SHALL refresh data from BC_API

### Requirement 5: Product Endpoint Migration

**User Story:** As a developer, I want to migrate all product endpoints to use the new data source, so that the entire system uses normalized tables.

#### Acceptance Criteria

1. WHEN the /items/categories/{category_name} endpoint is called, THE Product_Router SHALL query Item_Master + Item_Price filtered by branch_code
2. WHEN the /items endpoint is called, THE Product_Router SHALL query Item_Master + Item_Price filtered by branch_code
3. WHEN category-specific endpoints are called (aluminium, glass, cline, accessories, sealant, gypsum), THE Product_Router SHALL query Item_Master + Item_Price filtered by branch_code
4. WHEN the full-text search endpoint is called, THE Product_Router SHALL search Item_Master and join with Item_Price filtered by branch_code
5. THE Product_Router SHALL extract branch_code from the JWT token for all product endpoints

### Requirement 6: Response Format Compatibility

**User Story:** As a frontend developer, I want the API response format to remain unchanged, so that existing frontend code continues to work without modifications.

#### Acceptance Criteria

1. WHEN returning product data, THE Product_Router SHALL use the same JSON field names as the legacy system
2. WHEN returning price data, THE Product_Router SHALL use the field names: priceR1, priceR2, priceW1, priceW2, cost
3. WHEN returning product metadata, THE Product_Router SHALL use the field names: sku, name, category, product_group, product_sub_group, pkg_size, isVariant
4. WHEN returning inventory data, THE Product_Router SHALL use the field name: Inventory (for backward compatibility)
5. THE Product_Router SHALL maintain the same HTTP status codes and error response formats

### Requirement 7: Performance Optimization

**User Story:** As a system administrator, I want product queries to perform efficiently, so that users experience fast response times.

#### Acceptance Criteria

1. WHEN joining Item_Master and Item_Price, THE Product_Router SHALL use indexed columns (SKU, BranchCode) in the JOIN condition
2. WHEN caching inventory data, THE Inventory_Service SHALL use a TTL (time-to-live) of 5 minutes
3. WHEN loading code-name mappings, THE Product_Router SHALL use the existing @lru_cache decorator to cache lookup tables
4. WHEN querying large result sets, THE Product_Router SHALL support pagination with limit and offset parameters
5. THE Product_Router SHALL maintain the existing glass product caching strategy

### Requirement 8: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that I can diagnose issues quickly.

#### Acceptance Criteria

1. WHEN a database query fails, THE Product_Router SHALL log the error with the SQL query and parameters
2. WHEN BC_API is unavailable, THE Inventory_Service SHALL log the error and return empty inventory (graceful degradation)
3. WHEN a branch_code is invalid, THE Auth_Middleware SHALL return a 400 error with a descriptive message
4. WHEN a SKU is not found, THE Product_Router SHALL return a 404 error with the requested SKU in the message
5. THE Product_Router SHALL log all branch-filtered queries with the branch_code for audit purposes

### Requirement 9: Gradual Migration Support

**User Story:** As a system administrator, I want to support gradual migration, so that I can test the new system before fully switching over.

#### Acceptance Criteria

1. WHERE a feature flag is enabled, THE Product_Router SHALL use Item_Master + Item_Price as the data source
2. WHERE a feature flag is disabled, THE Product_Router SHALL use Items_Test as the data source
3. THE Product_Router SHALL read the feature flag from environment variables
4. WHEN the feature flag changes, THE Product_Router SHALL not require a restart to apply the change
5. THE Product_Router SHALL log which data source is being used for each request

### Requirement 10: Data Validation

**User Story:** As a developer, I want to validate data integrity, so that the system returns consistent and accurate information.

#### Acceptance Criteria

1. WHEN loading product data, THE Product_Router SHALL validate that SKU fields are non-empty strings
2. WHEN loading price data, THE Product_Router SHALL validate that price fields are numeric and non-negative
3. WHEN loading inventory data, THE Inventory_Service SHALL validate that quantity fields are numeric
4. WHEN a product has invalid data, THE Product_Router SHALL log a warning and skip the record
5. THE Product_Router SHALL validate that branch_code matches the pattern [A-Z]{2,4} (2-4 uppercase letters)
