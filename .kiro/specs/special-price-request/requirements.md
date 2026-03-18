# Requirements Document: Special Price Request System

## Introduction

ระบบขอราคาพิเศษ (Special Price Request System) เป็นระบบที่ช่วยให้พนักงานขายสามารถขอราคาพิเศษสำหรับลูกค้าได้ โดยมีกระบวนการอนุมัติแบบลำดับชั้นตามเงื่อนไขราคา ระบบนี้ช่วยให้การจัดการราคาพิเศษเป็นไปอย่างเป็นระเบียบและมีการควบคุมที่เหมาะสม

## Glossary

- **Special_Price_Request**: ใบขอราคาพิเศษที่สร้างขึ้นเพื่อขอราคาต่ำกว่าราคาปกติ
- **Special_Price_Request_Item**: รายการสินค้าในใบขอราคาพิเศษ
- **Branch_Manager**: ผู้จัดการสาขา (Role: Branch Manager)
- **Regional_Manager**: ผู้จัดการภาค (Role: Regional Manager)
- **Employee**: พนักงาน (มีรหัส, สาขา, และ Role)
- **Draft_Status**: สถานะร่างของใบขอราคาพิเศษ (ยังไม่ได้ส่ง)
- **Submitted_Status**: สถานะที่ส่งแล้ว (รอการอนุมัติ)
- **Approved_Status**: สถานะที่ได้รับการอนุมัติแล้ว
- **Rejected_Status**: สถานะที่ถูกปฏิเสธ
- **Price_Threshold_R1**: ราคาขั้นต่ำ (ไม่ต้องขออนุมัติ)
- **Price_Threshold_W2**: ราคาขั้นกลาง (ต้องอนุมัติจากผู้จัดการสาขา)
- **Price_Threshold_W1**: ราคาขั้นสูง (ต้องอนุมัติจากผู้จัดการสาขาและผู้จัดการภาค)
- **Quote_Document**: เอกสารใบเสนอราคา
- **System**: ระบบขอราคาพิเศษ

## Requirements

### Requirement 1: Create Special Price Request

**User Story:** As a sales employee, I want to create a special price request, so that I can request special prices for customers below the standard pricing.

#### Acceptance Criteria

1. WHEN a sales employee accesses the special price request creation page, THE System SHALL display a form to enter customer information, items, and requested prices
2. WHEN the employee selects items and enters requested prices, THE System SHALL calculate the price difference from the standard price
3. WHEN the employee saves the request as Draft, THE System SHALL store the request with Draft_Status and allow further editing
4. THE System SHALL validate that all required fields (customer, items, requested prices) are filled before allowing save

### Requirement 2: Route Special Price Request Based on Price Threshold

**User Story:** As a system administrator, I want the system to automatically route special price requests to the appropriate approver, so that approval workflows are efficient and follow the organizational hierarchy.

#### Acceptance Criteria

1. WHEN a special price request is submitted with price lower than R1 but not exceeding W2, THE System SHALL route the request to the Branch_Manager of the requesting employee's branch ONLY
2. WHEN a special price request is submitted with price lower than W2 but not exceeding W1, THE System SHALL route the request to the Branch_Manager of the requesting employee's branch first for review
3. WHEN a Branch_Manager approves a request with price between W2 and W1, THE System SHALL forward the request to the Regional_Manager of the same region as the Branch_Manager ONLY (not to other regional managers)
4. WHEN a special price request is submitted with price at or above W1, THE System SHALL reject the request and notify the employee that the price is outside the acceptable range
5. THE System SHALL store the routing information including approver details, approver branch, approver region, and routing timestamp

### Requirement 3: Prevent Quote Opening Without Approval

**User Story:** As a system administrator, I want to prevent users from opening quotes until approval is granted, so that special prices are only used after proper authorization.

#### Acceptance Criteria

1. WHEN a special price request is in Draft_Status, THE System SHALL allow the employee to save and edit the request but SHALL NOT allow opening/confirming the quote
2. WHEN a special price request is in Submitted_Status, THE System SHALL prevent all users from opening the quote and SHALL display a message indicating approval is pending
3. WHEN a special price request receives Approved_Status, THE System SHALL allow the quote to be opened and confirmed
4. IF a special price request is in Rejected_Status, THEN THE System SHALL prevent quote opening and SHALL display the rejection reason

### Requirement 4: Store Special Price Request Data

**User Story:** As a system administrator, I want to persist special price request data in the database, so that all requests are tracked and auditable.

#### Acceptance Criteria

1. THE System SHALL store special price request data in the special_price_requests table with fields: request_id, employee_id, branch_code, customer_code, requested_price, status, created_date, submitted_date, approved_date, approver_id
2. THE System SHALL store special price request items in the special_price_request_items table with fields: item_id, request_id, sku, quantity, requested_unit_price, standard_unit_price, price_difference
3. WHEN a special price request is created, THE System SHALL automatically populate employee information (employee_id, branch_code) from the authenticated user's session
4. WHEN a special price request is submitted, THE System SHALL record the submission timestamp and set status to Submitted_Status

### Requirement 5: Retrieve Employee Information

**User Story:** As a system administrator, I want to retrieve employee information from the database, so that the system can properly identify and route requests.

#### Acceptance Criteria

1. THE System SHALL retrieve employee information including employee_id, branch_code, and role from the employee database
2. WHEN an employee logs in, THE System SHALL load their employee information and make it available for request creation
3. THE System SHALL validate that the employee has the appropriate role to create special price requests
4. THE System SHALL use employee branch_code to determine the appropriate Branch_Manager for routing

### Requirement 6: Display Special Price Request Status

**User Story:** As a sales employee, I want to view the status of my special price requests, so that I can track the approval progress.

#### Acceptance Criteria

1. WHEN an employee views their special price requests, THE System SHALL display a list showing request_id, customer_name, requested_price, current_status, and submission_date
2. WHEN a request is in Submitted_Status, THE System SHALL display the current approver's name and expected approval timeframe
3. WHEN a request is in Approved_Status, THE System SHALL display the approval date and approver's name
4. WHEN a request is in Rejected_Status, THE System SHALL display the rejection reason and date

### Requirement 7: Approve or Reject Special Price Request

**User Story:** As a branch manager or regional manager, I want to approve or reject special price requests, so that I can control which special prices are authorized.

#### Acceptance Criteria

1. WHEN a Branch_Manager views pending requests, THE System SHALL display only requests routed to their branch
2. WHEN a Branch_Manager approves a request with price between R1 and W2, THE System SHALL set status to Approved_Status and allow quote opening
3. WHEN a Branch_Manager approves a request with price between W2 and W1, THE System SHALL forward the request to the Regional_Manager of the same region as the Branch_Manager and set status to Pending_Regional_Approval
4. WHEN a Regional_Manager views pending requests, THE System SHALL display only requests forwarded from Branch_Managers in their region
5. WHEN a Regional_Manager approves a forwarded request, THE System SHALL set status to Approved_Status and notify the original employee
6. WHEN an approver rejects a request, THE System SHALL set status to Rejected_Status, record the rejection reason, and notify the employee
7. THE System SHALL record the approver_id, approver_branch, approver_region, approval_date, and approval_timestamp for all approval actions

### Requirement 8: Validate Price Thresholds

**User Story:** As a system administrator, I want to validate that requested prices fall within acceptable thresholds, so that only reasonable special prices are requested.

#### Acceptance Criteria

1. WHEN an employee submits a special price request, THE System SHALL validate that the requested price is not lower than R1
2. IF the requested price is lower than R1, THEN THE System SHALL reject the request and display an error message indicating the minimum acceptable price
3. WHEN an employee submits a special price request, THE System SHALL validate that the requested price does not exceed W1
4. IF the requested price exceeds W1, THEN THE System SHALL reject the request and display an error message indicating the maximum acceptable price
5. THE System SHALL retrieve R1, W2, and W1 price thresholds from the Item_Price table based on branch_code and sku

### Requirement 9: Audit Trail for Special Price Requests

**User Story:** As a compliance officer, I want to maintain an audit trail of all special price request activities, so that I can track all changes and approvals.

#### Acceptance Criteria

1. THE System SHALL log all state changes (Draft → Submitted → Approved/Rejected) with timestamp and user_id
2. WHEN a special price request is modified, THE System SHALL record the modification timestamp and modified_by user_id
3. THE System SHALL store all approval/rejection actions with approver_id, action_date, and action_reason
4. THE System SHALL provide an audit report showing the complete history of each special price request

### Requirement 10: Prevent Quote Confirmation Until Approval

**User Story:** As a system administrator, I want to ensure that quotes cannot be confirmed until special price requests are approved, so that only authorized prices are used in transactions.

#### Acceptance Criteria

1. WHEN a user attempts to confirm/open a quote with special prices, THE System SHALL check if all associated special price requests have Approved_Status
2. IF any special price request is not in Approved_Status, THEN THE System SHALL prevent quote confirmation and display a message indicating which requests need approval
3. WHEN all special price requests are approved, THE System SHALL allow quote confirmation and set the quote status to Confirmed
4. THE System SHALL link the quote to the approved special price request for audit purposes

## Correctness Properties

### Property 1: Price Threshold Routing Correctness

**Property:** For any special price request, the routing destination is determined correctly based on price thresholds and organizational hierarchy.

**Invariant:** 
- IF price < R1 THEN request is rejected
- IF R1 ≤ price ≤ W2 THEN request routes to Branch_Manager of requesting employee's branch ONLY
- IF W2 < price < W1 THEN request routes to Branch_Manager of requesting employee's branch first, then to Regional_Manager of the same region as Branch_Manager ONLY
- IF price ≥ W1 THEN request is rejected
- Regional_Manager receiving forwarded request must be from the same region as the Branch_Manager

**Test Strategy:** Property-based testing with random prices, branches, and regions to verify routing logic respects organizational hierarchy.

### Property 2: Status Transition Correctness

**Property:** Special price request status transitions follow the defined workflow and no invalid transitions occur.

**Invariant:**
- Draft → Submitted (valid)
- Submitted → Approved (valid)
- Submitted → Rejected (valid)
- Submitted → Draft (valid, for editing)
- Any other transition is invalid

**Test Strategy:** State machine testing to verify all valid and invalid transitions.

### Property 3: Quote Opening Prevention

**Property:** Quotes cannot be opened or confirmed unless all associated special price requests are in Approved_Status.

**Invariant:**
- IF any special_price_request.status ≠ Approved_Status THEN quote.can_open = false
- IF all special_price_request.status = Approved_Status THEN quote.can_open = true

**Test Strategy:** Round-trip testing: create request → submit → attempt open (should fail) → approve → attempt open (should succeed).

### Property 4: Employee Information Consistency

**Property:** Employee information (employee_id, branch_code, role) is consistently retrieved and used throughout the request lifecycle.

**Invariant:**
- employee_id from request = employee_id from authenticated session
- branch_code from request = branch_code from employee database
- role from request is valid (Sales, Branch Manager, Regional Manager)

**Test Strategy:** Metamorphic property testing comparing employee data from different sources.

### Property 5: Audit Trail Completeness

**Property:** Every state change and approval action is recorded in the audit trail with complete information.

**Invariant:**
- FOR EACH state change: audit_log entry exists with timestamp, user_id, old_status, new_status
- FOR EACH approval: audit_log entry exists with approver_id, approval_date, approval_reason
- No audit_log entries are missing or incomplete

**Test Strategy:** Model-based testing comparing expected audit entries with actual database records.

### Property 6: Price Threshold Validation

**Property:** Requested prices are validated against R1, W2, and W1 thresholds correctly.

**Invariant:**
- IF requested_price < R1 THEN validation fails
- IF requested_price > W1 THEN validation fails
- IF R1 ≤ requested_price ≤ W1 THEN validation passes

**Test Strategy:** Boundary value testing with prices at and around thresholds.

### Property 7: Data Persistence

**Property:** All special price request data is correctly persisted to the database and can be retrieved without loss.

**Invariant:**
- FOR EACH created request: request can be retrieved from database with all fields intact
- FOR EACH modified request: modifications are persisted and retrievable
- No data corruption or loss occurs during storage

**Test Strategy:** Round-trip property: create → store → retrieve → verify equality.

### Property 8: Routing Information Accuracy

**Property:** Routing information (approver details, routing timestamp, organizational hierarchy) is accurately recorded for all requests.

**Invariant:**
- routing_approver_id matches the correct Branch_Manager of the requesting employee's branch
- For multi-level approvals: Regional_Manager's region matches the Branch_Manager's region
- routing_timestamp is recorded at submission time
- routing_history shows all intermediate approvers for multi-level approvals
- No cross-region routing occurs (Regional_Manager from different region cannot approve)

**Test Strategy:** Metamorphic testing comparing routing information with employee hierarchy data and verifying region consistency.


### Requirement 11: Special Price Validity Period

**User Story:** As a sales employee, I want to specify the validity period for special prices, so that approved prices can be used within a defined timeframe without requesting approval again.

#### Acceptance Criteria

1. WHEN creating a special price request, THE System SHALL allow the employee to specify valid_from and valid_to dates
2. THE System SHALL validate that valid_from date is not after valid_to date
3. THE System SHALL store the validity period in the special_price_requests table
4. WHEN displaying special price requests, THE System SHALL show the validity period to all users
5. THE System SHALL set default validity period to 30 days from the current date if not specified

### Requirement 12: Reuse Approved Special Prices

**User Story:** As a sales employee, I want to automatically use previously approved special prices that are still valid, so that I don't need to request approval again for the same customer and items.

#### Acceptance Criteria

1. WHEN creating a quote for a customer, THE System SHALL check if there are approved special prices for that customer that are currently valid (current date is between valid_from and valid_to)
2. IF valid special prices exist for items in the quote, THE System SHALL display a notification showing which items have active special prices
3. WHEN an item has an active special price and the requested price is equal to or higher than the approved special price, THE System SHALL NOT require a new approval request
4. THE System SHALL display the active special price information including: item name, approved price, validity period, and request number
5. IF the requested price is lower than the active special price, THE System SHALL require a new approval request
6. THE System SHALL retrieve active special prices using the endpoint `/api/special-price-requests/active-prices/{customer_code}`
7. THE System SHALL filter active prices based on: status = 'APPROVED', current date BETWEEN valid_from AND valid_to
8. IF multiple approved prices exist for the same item, THE System SHALL use the most recently approved price

### Requirement 13: Display Active Special Prices

**User Story:** As a sales employee, I want to see which items have active special prices when creating a quote, so that I can utilize approved prices without requesting new approvals.

#### Acceptance Criteria

1. WHEN viewing the quote summary page, THE System SHALL display a notification if active special prices exist for the customer
2. THE notification SHALL show: number of items with active prices, item names, approved prices, and validity end dates
3. THE System SHALL display up to 5 items in the notification, with an indicator if more items exist
4. THE notification SHALL use a green color scheme to indicate approved/active status
5. WHEN checking prices below R1, THE System SHALL exclude items that have active special prices at or below the requested price
6. THE System SHALL log in console when an item uses an active special price instead of requiring new approval

## Updated Correctness Properties

### Property 9: Validity Period Correctness

**Property:** Special prices are only considered active if the current date falls within the validity period.

**Invariant:**
- IF current_date < valid_from THEN price is not active
- IF current_date > valid_to THEN price is not active
- IF valid_from ≤ current_date ≤ valid_to AND status = 'APPROVED' THEN price is active

**Test Strategy:** Time-based property testing with various date ranges and current dates.

### Property 10: Price Reuse Logic Correctness

**Property:** Previously approved special prices are correctly reused when applicable, and new approvals are only required when necessary.

**Invariant:**
- IF active_special_price exists AND requested_price ≥ active_special_price THEN no new approval required
- IF active_special_price exists AND requested_price < active_special_price THEN new approval required
- IF no active_special_price exists AND requested_price < R1 THEN new approval required
- IF multiple active prices exist for same item THEN most recent approval is used

**Test Strategy:** Scenario-based testing with various combinations of active prices and requested prices.

### Property 11: Active Price Retrieval Correctness

**Property:** The system correctly retrieves and filters active special prices for a given customer.

**Invariant:**
- Retrieved prices must have status = 'APPROVED'
- Retrieved prices must have current_date BETWEEN valid_from AND valid_to
- Retrieved prices must match the specified customer_code
- IF multiple prices exist for same item, only the most recent is returned

**Test Strategy:** Database query testing with various customer codes, dates, and approval statuses.
