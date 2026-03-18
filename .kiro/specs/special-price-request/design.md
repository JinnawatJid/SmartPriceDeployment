# Design Document: Special Price Request System

## Overview

The Special Price Request System enables sales employees to request special prices for customers below standard pricing, with an automated approval workflow based on price thresholds and organizational hierarchy. The system ensures proper authorization before special prices are used in quotes, maintaining audit trails for compliance.

### Key Design Principles

1. **Hierarchical Approval**: Routing based on price thresholds and organizational structure (Branch Manager → Regional Manager)
2. **Quote Protection**: Quotes cannot be opened/confirmed until all special price requests are approved
3. **Audit Compliance**: Complete audit trail of all state changes, approvals, and modifications
4. **Data Integrity**: Automatic population of employee information from authenticated sessions
5. **Regional Isolation**: Regional managers only approve requests from their region; no cross-region approvals

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Request Creator  │  │ Approval Manager │                 │
│  │ (Sales Employee) │  │ (BM/RM)          │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Special Price Request Router                         │   │
│  │ - Create/Update/List Requests                        │   │
│  │ - Submit for Approval                                │   │
│  │ - Approve/Reject Requests                            │   │
│  │ - Validate Price Thresholds                          │   │
│  │ - Route Based on Hierarchy                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ Routing Engine   │  │ Validation Engine│                 │
│  │ - Price-based    │  │ - Thresholds     │                 │
│  │ - Hierarchy      │  │ - Required fields│                 │
│  │ - Region check   │  │ - Price bounds   │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Access Layer                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Database (MSSQL)                                     │   │
│  │ - special_price_requests                             │   │
│  │ - special_price_request_items                        │   │
│  │ - special_price_request_audit                        │   │
│  │ - special_price_request_routing                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Request Creation**: Sales employee creates request → System validates → Stores as Draft
2. **Request Submission**: Employee submits → System validates prices → Routes to approver
3. **Approval Workflow**: 
   - Single-level: R1 ≤ price ≤ W2 → Branch Manager approves → Approved
   - Multi-level: W2 < price < W1 → Branch Manager approves → Regional Manager approves → Approved
4. **Quote Opening**: System checks all requests approved → Allows quote confirmation

---

## Components and Interfaces

### 1. Special Price Request Router (`special_price_request_router.py`)

**Endpoints:**

```
POST   /api/special-price-requests              - Create new request
GET    /api/special-price-requests              - List requests (filtered by user role)
GET    /api/special-price-requests/{request_id} - Get request details
PUT    /api/special-price-requests/{request_id} - Update request (Draft only)
POST   /api/special-price-requests/{request_id}/submit - Submit for approval
POST   /api/special-price-requests/{request_id}/approve - Approve request
POST   /api/special-price-requests/{request_id}/reject  - Reject request
GET    /api/special-price-requests/{request_id}/audit   - Get audit trail
GET    /api/special-price-requests/pending/approvals    - Get pending approvals (for BM/RM)
```

### 2. Request Validation Engine

**Validates:**
- Required fields: customer_code, items, requested_prices
- Price thresholds: R1 ≤ price ≤ W1
- Employee role: Only sales employees can create
- Item existence: SKU must exist in Item_Master

### 3. Routing Engine

**Logic:**
```
IF price < R1:
  REJECT request
ELSE IF R1 ≤ price ≤ W2:
  Route to Branch_Manager of employee's branch
  Set status = APPROVED (single-level)
ELSE IF W2 < price < W1:
  Route to Branch_Manager of employee's branch
  Set status = PENDING_BRANCH_APPROVAL
  After BM approval:
    Route to Regional_Manager of same region as BM
    Set status = PENDING_REGIONAL_APPROVAL
ELSE IF price ≥ W1:
  REJECT request
```

### 4. Quote Opening Validator

**Checks before allowing quote confirmation:**
- All special_price_requests linked to quote have status = APPROVED
- If any request not approved: Display list of unapproved requests
- Link quote to approved requests for audit trail

---

## Data Models

### Database Schema

#### Table: special_price_requests (Existing)

**Columns:**
- `id` (PK, int) - Primary key
- `request_number` (nvarchar(50)) - Request identifier
- `quote_no` (nvarchar(50)) - Link to Quote_Header
- `customer_code` (nvarchar(50)) - Customer identifier
- `customer_name` (nvarchar(255)) - Customer name
- `customer_type` (nvarchar(50)) - Customer type
- `requester_name` (nvarchar(255)) - Employee who created request
- `request_reason` (nvarchar(max)) - Reason for special price
- `original_total` (decimal(18,2)) - Original total amount
- `requested_total` (decimal(18,2)) - Requested total amount
- `discount_percentage` (decimal(5,2)) - Discount percentage
- `status` (nvarchar(20)) - DRAFT, SUBMITTED, PENDING_BRANCH_APPROVAL, PENDING_REGIONAL_APPROVAL, APPROVED, REJECTED
- `approver_employee_id` (nvarchar(50)) - Approver's employee ID
- `approved_by` (nvarchar(255)) - Approver's name
- `approved_at` (datetime) - Approval timestamp
- `rejection_reason` (nvarchar(max)) - Rejection reason
- `approval_pdf_files` (nvarchar(max)) - PDF file paths
- `branch` (nvarchar(50)) - Branch code
- `valid_from` (nvarchar(50)) - Valid from date
- `valid_to` (nvarchar(50)) - Valid to date
- `created_at` (datetime) - Creation timestamp
- `updated_at` (datetime) - Last update timestamp
- `attached_documents` (nvarchar(max)) - Attached document paths

**Note:** Table already exists. Need to add columns for multi-level approval tracking if not present:
- `approver_branch` (nvarchar(10)) - Approver's branch
- `approver_region` (nvarchar(10)) - Approver's region
- `employee_id` (nvarchar(50)) - Original requester's employee ID

#### Table: special_price_request_items (Existing)

**Columns:**
- `id` (PK, int) - Primary key
- `request_id` (FK, int) - Reference to special_price_requests
- `item_code` (nvarchar(50)) - Item/SKU code
- `item_name` (nvarchar(255)) - Item name
- `quantity` (decimal(18,2)) - Quantity
- `unit` (nvarchar(50)) - Unit of measurement
- `normal_price` (decimal(18,2)) - Standard unit price
- `requested_price` (decimal(18,2)) - Requested unit price
- `original_amount` (decimal(18,2)) - Original total (quantity × normal_price)
- `requested_amount` (decimal(18,2)) - Requested total (quantity × requested_price)
- `is_below_normal` (bit) - Flag if price is below normal
- `created_at` (datetime) - Creation timestamp

**Note:** Table already exists. Columns map to design as follows:
- `item_code` = SKU
- `normal_price` = standard_unit_price
- `requested_price` = requested_unit_price
- `original_amount` = standard total
- `requested_amount` = requested total

#### Table: special_price_request_audit

```sql
CREATE TABLE special_price_request_audit (
  audit_id                INT PRIMARY KEY IDENTITY(1,1),
  request_id              INT NOT NULL,
  action                  VARCHAR(50) NOT NULL,  -- CREATED, SUBMITTED, APPROVED, REJECTED, MODIFIED
  old_status              VARCHAR(50),
  new_status              VARCHAR(50),
  action_by               VARCHAR(20) NOT NULL,
  action_date             DATETIME NOT NULL,
  action_reason           VARCHAR(500),
  details_json            NVARCHAR(MAX),  -- JSON with additional details
  FOREIGN KEY (request_id) REFERENCES special_price_requests(request_id) ON DELETE CASCADE,
  INDEX idx_request_id (request_id),
  INDEX idx_action_date (action_date)
);
```

#### Table: special_price_request_routing

```sql
CREATE TABLE special_price_request_routing (
  routing_id              INT PRIMARY KEY IDENTITY(1,1),
  request_id              INT NOT NULL,
  routing_level           INT NOT NULL,  -- 1 for BM, 2 for RM
  approver_id             VARCHAR(20) NOT NULL,
  approver_branch         VARCHAR(10),
  approver_region         VARCHAR(10),
  routing_timestamp       DATETIME NOT NULL,
  approval_timestamp      DATETIME,
  approval_status         VARCHAR(50),  -- PENDING, APPROVED, REJECTED
  FOREIGN KEY (request_id) REFERENCES special_price_requests(request_id) ON DELETE CASCADE,
  INDEX idx_request_id (request_id),
  INDEX idx_approver_id (approver_id)
);
```

### API Request/Response Models

#### Create Request

```json
{
  "customer_code": "CUST001",
  "customer_name": "Customer Name",
  "items": [
    {
      "sku": "SKU001",
      "quantity": 100,
      "unit": "PCS",
      "requested_unit_price": 50.00,
      "standard_unit_price": 60.00
    }
  ],
  "note": "Special project discount"
}
```

#### Request Response

```json
{
  "request_id": 1,
  "employee_id": "10027",
  "branch_code": "12CM",
  "customer_code": "CUST001",
  "status": "DRAFT",
  "created_date": "2024-01-15T10:30:00Z",
  "items": [
    {
      "item_id": 1,
      "sku": "SKU001",
      "quantity": 100,
      "requested_unit_price": 50.00,
      "standard_unit_price": 60.00,
      "price_difference": -10.00,
      "price_difference_pct": -16.67
    }
  ]
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Price Threshold Routing Correctness

For any special price request with a given price and employee branch, the routing destination is determined correctly based on price thresholds and organizational hierarchy.

**Invariant:**
- IF price < R1 THEN request is rejected
- IF R1 ≤ price ≤ W2 THEN request routes to Branch_Manager of requesting employee's branch ONLY
- IF W2 < price < W1 THEN request routes to Branch_Manager first, then to Regional_Manager of same region as Branch_Manager ONLY
- IF price ≥ W1 THEN request is rejected
- Regional_Manager receiving forwarded request must be from same region as Branch_Manager

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Status Transition Correctness

For any special price request, status transitions follow the defined workflow and no invalid transitions occur.

**Invariant:**
- DRAFT → SUBMITTED (valid)
- SUBMITTED → APPROVED (valid for single-level)
- SUBMITTED → PENDING_BRANCH_APPROVAL (valid for multi-level)
- PENDING_BRANCH_APPROVAL → PENDING_REGIONAL_APPROVAL (valid)
- PENDING_REGIONAL_APPROVAL → APPROVED (valid)
- SUBMITTED/PENDING_* → REJECTED (valid)
- DRAFT → DRAFT (valid, for editing)
- Any other transition is invalid

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 3: Quote Opening Prevention

For any quote with associated special price requests, the quote cannot be opened or confirmed unless all requests are in Approved status.

**Invariant:**
- IF any special_price_request.status ≠ APPROVED THEN quote.can_open = false
- IF all special_price_request.status = APPROVED THEN quote.can_open = true
- Attempting to open unapproved quote returns error with list of unapproved requests

**Validates: Requirements 3.1, 3.2, 3.3, 10.1, 10.2, 10.3**

### Property 4: Price Threshold Validation

For any special price request, requested prices are validated against R1, W2, and W1 thresholds correctly.

**Invariant:**
- IF requested_price < R1 THEN validation fails with error message
- IF requested_price > W1 THEN validation fails with error message
- IF R1 ≤ requested_price ≤ W1 THEN validation passes
- Thresholds are retrieved from Item_Price table based on branch_code and sku

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 5: Employee Information Consistency

For any special price request, employee information (employee_id, branch_code, role) is consistently retrieved and used throughout the request lifecycle.

**Invariant:**
- employee_id from request = employee_id from authenticated session
- branch_code from request = branch_code from employee database
- role from request is valid (Sales, Branch Manager, Regional Manager)
- Employee information is automatically populated from session, not user input

**Validates: Requirements 4.3, 5.1, 5.2, 5.3, 5.4**

### Property 6: Audit Trail Completeness

For any special price request, every state change and approval action is recorded in the audit trail with complete information.

**Invariant:**
- FOR EACH state change: audit_log entry exists with timestamp, user_id, old_status, new_status
- FOR EACH approval: audit_log entry exists with approver_id, approval_date, approval_reason
- FOR EACH modification: audit_log entry exists with modified_by, modified_date, change details
- No audit_log entries are missing or incomplete
- Audit trail is immutable (no deletions or modifications)

**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

### Property 7: Data Persistence Round-Trip

For any special price request, all data is correctly persisted to the database and can be retrieved without loss or corruption.

**Invariant:**
- FOR EACH created request: request can be retrieved from database with all fields intact
- FOR EACH modified request: modifications are persisted and retrievable
- FOR EACH item in request: item data matches what was stored
- No data corruption or loss occurs during storage or retrieval

**Validates: Requirements 4.1, 4.2, 4.4**

### Property 8: Routing Information Accuracy

For any special price request, routing information (approver details, routing timestamp, organizational hierarchy) is accurately recorded.

**Invariant:**
- routing_approver_id matches correct Branch_Manager of requesting employee's branch
- For multi-level approvals: Regional_Manager's region matches Branch_Manager's region
- routing_timestamp is recorded at submission time
- routing_history shows all intermediate approvers for multi-level approvals
- No cross-region routing occurs (Regional_Manager from different region cannot approve)

**Validates: Requirements 2.5, 7.1, 7.4, 7.7**

### Property 9: Price Difference Calculation

For any special price request item, the price difference is calculated correctly as the difference between standard and requested prices.

**Invariant:**
- price_difference = requested_unit_price - standard_unit_price
- price_difference_pct = (price_difference / standard_unit_price) * 100
- Calculation is accurate for all price combinations

**Validates: Requirements 1.2**

### Property 10: Required Field Validation

For any special price request, all required fields must be filled before allowing submission.

**Invariant:**
- customer_code is not empty
- items list is not empty
- For each item: sku, quantity, requested_unit_price are not empty
- Requests with missing fields are rejected with error message

**Validates: Requirements 1.4**

### Property 11: Approver Access Control

For any approver (Branch Manager or Regional Manager), they can only view and approve requests routed to them based on their branch/region.

**Invariant:**
- Branch_Manager can only see requests for their branch
- Regional_Manager can only see requests forwarded from their region
- Approvers cannot see requests from other branches/regions
- Approvers cannot approve requests not routed to them

**Validates: Requirements 7.1, 7.4**

### Property 12: Approval Notification

For any special price request approval or rejection, the original employee is notified with appropriate details.

**Invariant:**
- Employee is notified when request is approved
- Employee is notified when request is rejected with rejection reason
- Notification includes request details and approver information
- Notification is sent immediately after approval/rejection

**Validates: Requirements 7.5, 7.6**

---

## Error Handling

### Validation Errors

| Error | Trigger | Response |
|-------|---------|----------|
| Missing required fields | Customer/items/prices not provided | 400 Bad Request with field list |
| Price below R1 | requested_price < R1 | 400 Bad Request with minimum price |
| Price above W1 | requested_price > W1 | 400 Bad Request with maximum price |
| Invalid SKU | SKU not found in Item_Master | 400 Bad Request with SKU list |
| Unauthorized role | Non-sales employee creates request | 403 Forbidden |
| Invalid status transition | Attempt invalid state change | 400 Bad Request with valid transitions |

### Business Logic Errors

| Error | Trigger | Response |
|-------|---------|----------|
| Request not found | Invalid request_id | 404 Not Found |
| Cannot edit submitted request | Attempt to modify non-Draft request | 400 Bad Request |
| Cannot approve own request | Approver is same as requester | 400 Bad Request |
| Cross-region approval | RM from different region approves | 400 Bad Request |
| Quote already confirmed | Attempt to modify linked quote | 400 Bad Request |

### Database Errors

| Error | Trigger | Response |
|-------|---------|----------|
| Database connection failed | DB unavailable | 500 Internal Server Error with retry message |
| Constraint violation | Duplicate request_id | 500 Internal Server Error |
| Transaction rollback | Partial data write | 500 Internal Server Error with rollback message |

---

## Testing Strategy

### Unit Testing

**Test Categories:**

1. **Validation Tests**
   - Test price threshold validation (below R1, between R1-W2, between W2-W1, above W1)
   - Test required field validation (missing customer, items, prices)
   - Test SKU validation against Item_Master
   - Test role-based access control

2. **Routing Logic Tests**
   - Test single-level routing (R1 ≤ price ≤ W2 → Branch Manager)
   - Test multi-level routing (W2 < price < W1 → Branch Manager → Regional Manager)
   - Test region consistency (Regional Manager from same region as Branch Manager)
   - Test rejection cases (price < R1, price ≥ W1)

3. **Status Transition Tests**
   - Test valid transitions (DRAFT → SUBMITTED → APPROVED)
   - Test invalid transitions (APPROVED → DRAFT, REJECTED → SUBMITTED)
   - Test multi-level approval transitions

4. **Data Persistence Tests**
   - Test request creation and retrieval
   - Test item storage and retrieval
   - Test audit trail logging
   - Test routing information storage

5. **Quote Opening Tests**
   - Test quote opening prevention when requests not approved
   - Test quote opening allowed when all requests approved
   - Test error message with list of unapproved requests

6. **Edge Cases**
   - Test with zero quantity items
   - Test with very large prices
   - Test with special characters in customer names
   - Test concurrent request submissions
   - Test approval after request modification

### Property-Based Testing

**Configuration:**
- Minimum 100 iterations per property test
- Use fast-check (JavaScript) or Hypothesis (Python) for generators
- Tag format: `Feature: special-price-request, Property {number}: {property_text}`

**Property Tests:**

1. **Property 1: Price Threshold Routing** (100+ iterations)
   - Generate: random prices, branches, regions
   - Verify: routing destination matches price threshold rules
   - Tag: `Feature: special-price-request, Property 1: Price Threshold Routing Correctness`

2. **Property 2: Status Transitions** (100+ iterations)
   - Generate: random status sequences
   - Verify: only valid transitions occur
   - Tag: `Feature: special-price-request, Property 2: Status Transition Correctness`

3. **Property 3: Quote Opening Prevention** (100+ iterations)
   - Generate: random approval states
   - Verify: quote opening only allowed when all approved
   - Tag: `Feature: special-price-request, Property 3: Quote Opening Prevention`

4. **Property 4: Price Validation** (100+ iterations)
   - Generate: random prices at/around thresholds
   - Verify: validation passes/fails correctly
   - Tag: `Feature: special-price-request, Property 4: Price Threshold Validation`

5. **Property 5: Employee Info Consistency** (100+ iterations)
   - Generate: random employees from different branches/regions
   - Verify: employee info matches session and database
   - Tag: `Feature: special-price-request, Property 5: Employee Information Consistency`

6. **Property 6: Audit Trail** (100+ iterations)
   - Generate: random state changes and approvals
   - Verify: all changes logged with complete information
   - Tag: `Feature: special-price-request, Property 6: Audit Trail Completeness`

7. **Property 7: Data Persistence** (100+ iterations)
   - Generate: random requests with various data
   - Verify: create → store → retrieve → equality
   - Tag: `Feature: special-price-request, Property 7: Data Persistence Round-Trip`

8. **Property 8: Routing Information** (100+ iterations)
   - Generate: random routing scenarios
   - Verify: routing info accurate and region-consistent
   - Tag: `Feature: special-price-request, Property 8: Routing Information Accuracy`

9. **Property 9: Price Calculation** (100+ iterations)
   - Generate: random standard and requested prices
   - Verify: price_difference calculated correctly
   - Tag: `Feature: special-price-request, Property 9: Price Difference Calculation`

10. **Property 10: Required Fields** (100+ iterations)
    - Generate: requests with missing fields
    - Verify: validation rejects incomplete requests
    - Tag: `Feature: special-price-request, Property 10: Required Field Validation`

11. **Property 11: Approver Access** (100+ iterations)
    - Generate: random approvers and requests
    - Verify: approvers only see their branch/region requests
    - Tag: `Feature: special-price-request, Property 11: Approver Access Control`

12. **Property 12: Notifications** (100+ iterations)
    - Generate: random approval/rejection scenarios
    - Verify: notifications sent with correct details
    - Tag: `Feature: special-price-request, Property 12: Approval Notification`

### Integration Testing

1. **End-to-End Workflow**
   - Create request → Submit → Approve → Open quote
   - Create request → Submit → Reject → Cannot open quote

2. **Multi-Level Approval**
   - Create request (W2 < price < W1) → Branch Manager approves → Regional Manager approves → Quote opens

3. **Concurrent Operations**
   - Multiple employees creating requests simultaneously
   - Multiple approvers approving requests simultaneously

4. **Audit Trail Verification**
   - Verify complete history for each request
   - Verify no audit entries are missing

---

## Implementation Notes

### Backend Implementation

1. **Database Initialization**
   - Create tables: special_price_requests, special_price_request_items, special_price_request_audit, special_price_request_routing
   - Add indexes for performance
   - Add foreign key constraints

2. **API Implementation**
   - Create `special_price_request_router.py` with all endpoints
   - Implement validation engine
   - Implement routing engine
   - Implement audit logging

3. **Integration Points**
   - Integrate with existing authentication (get employee info from JWT)
   - Integrate with Item_Price table (get thresholds)
   - Integrate with Quote_Header (check approval before opening)
   - Integrate with Employee database (get branch/region info)

### Frontend Implementation

1. **Request Creation Component**
   - Form for customer selection
   - Item picker with quantity and price inputs
   - Price difference display
   - Save as Draft / Submit buttons

2. **Request List Component**
   - List view with filtering by status
   - Display request details, customer, prices, status
   - Show approver info for submitted requests
   - Show rejection reason for rejected requests

3. **Approval Component**
   - List of pending approvals (for BM/RM)
   - Request details with items and prices
   - Approve/Reject buttons
   - Rejection reason input

4. **Quote Integration**
   - Check special price request status before opening quote
   - Display warning if requests not approved
   - Link quote to approved requests

---

## Security Considerations

1. **Authentication**: All endpoints require valid JWT token with employee info
2. **Authorization**: Role-based access control (Sales, Branch Manager, Regional Manager)
3. **Data Validation**: All inputs validated before processing
4. **Audit Trail**: Immutable audit log for compliance
5. **Regional Isolation**: Regional managers cannot approve requests from other regions
6. **Approval Integrity**: Employees cannot approve their own requests

---

## Performance Considerations

1. **Database Indexes**: Indexes on employee_id, branch_code, status, approver_id for fast queries
2. **Caching**: Cache employee hierarchy and price thresholds
3. **Pagination**: List endpoints support pagination for large datasets
4. **Batch Operations**: Support bulk request creation/approval if needed

