# Implementation Plan: Special Price Request System

## Overview

This implementation plan breaks down the Special Price Request System into discrete, incremental tasks that build upon each other. The workflow follows a layered approach: database schema → backend API → business logic → frontend components → testing and integration.

## Tasks

- [ ] 1. Verify and update database schema for multi-level approval tracking
  - [ ] 1.1 Check if special_price_requests table has required columns
    - Verify columns: status, approver_employee_id, approver_branch, approver_region, employee_id, branch
    - Add missing columns if needed:
      - `approver_branch` (nvarchar(10)) - Approver's branch
      - `approver_region` (nvarchar(10)) - Approver's region
      - `employee_id` (nvarchar(50)) - Original requester's employee ID
    - Add indexes on: status, approver_employee_id, employee_id, branch
    - _Requirements: 4.1, 4.3_

  - [ ] 1.2 Verify special_price_request_items table structure
    - Verify columns: request_id, item_code, quantity, normal_price, requested_price, original_amount, requested_amount
    - Verify foreign key to special_price_requests with CASCADE delete
    - Verify indexes on request_id and item_code
    - _Requirements: 4.2_

  - [ ] 1.3 Create special_price_request_audit table for audit trail
    - Create table: audit_id (PK), request_id (FK), action, old_status, new_status, action_by, action_date, details_json
    - Add foreign key to special_price_requests with CASCADE delete
    - Add indexes on request_id and action_date
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 1.4 Create special_price_request_routing table for routing history
    - Create table: routing_id (PK), request_id (FK), routing_level, approver_id, approver_branch, approver_region, routing_timestamp, approval_timestamp, approval_status
    - Add foreign key to special_price_requests with CASCADE delete
    - Add indexes on request_id and approver_id
    - _Requirements: 2.5, 7.7_

  - [ ]* 1.5 Write property test for data persistence
    - **Property 7: Data Persistence Round-Trip**
    - **Validates: Requirements 4.1, 4.2, 4.4**
    - Test: Create request with items → Store → Retrieve → Verify all fields match

- [ ] 2. Implement backend API router and core endpoints
  - [ ] 2.1 Create special_price_request_router.py with FastAPI endpoints
    - Implement POST /api/special-price-requests (create new request)
    - Implement GET /api/special-price-requests (list requests with role-based filtering)
    - Implement GET /api/special-price-requests/{request_id} (get request details)
    - Implement PUT /api/special-price-requests/{request_id} (update Draft request)
    - _Requirements: 1.1, 1.3, 6.1_

  - [ ] 2.2 Implement request creation logic
    - Extract employee info from JWT token (employee_id, branch_code)
    - Validate required fields: customer_code, items, requested_prices
    - Create request with Draft status
    - Store request and items in database
    - _Requirements: 1.1, 1.3, 4.3, 5.2_

  - [ ]* 2.3 Write property test for required field validation
    - **Property 10: Required Field Validation**
    - **Validates: Requirements 1.4**
    - Test: Generate requests with missing fields → Verify validation rejects them

  - [ ] 2.4 Implement request listing with role-based filtering
    - For Sales employees: Show only their own requests
    - For Branch Managers: Show requests from their branch
    - For Regional Managers: Show requests from their region
    - _Requirements: 6.1, 7.1, 7.4_

  - [ ]* 2.5 Write unit tests for endpoint responses
    - Test successful request creation
    - Test error responses for invalid inputs
    - Test role-based filtering in list endpoint

- [ ] 3. Implement price validation and threshold checking
  - [ ] 3.1 Create validation engine for price thresholds
    - Retrieve R1, W2, W1 thresholds from Item_Price table based on branch_code and sku
    - Validate requested_price >= R1 (reject if below minimum)
    - Validate requested_price <= W1 (reject if above maximum)
    - Calculate price_difference and price_difference_pct
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 1.2_

  - [ ]* 3.2 Write property test for price threshold validation
    - **Property 4: Price Threshold Validation**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    - Test: Generate prices at/around thresholds → Verify validation passes/fails correctly

  - [ ] 3.3 Implement price validation in request submission
    - Call validation engine before allowing submission
    - Return error message with acceptable price range if validation fails
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 3.4 Write unit tests for price validation edge cases
    - Test prices at exact thresholds (R1, W2, W1)
    - Test prices just below/above thresholds
    - Test with different SKUs and branches

- [ ] 4. Implement routing engine and approval workflow
  - [ ] 4.1 Create routing engine for price-based approval routing
    - IF price < R1: Reject request
    - IF R1 ≤ price ≤ W2: Route to Branch_Manager of employee's branch (single-level)
    - IF W2 < price < W1: Route to Branch_Manager first, then Regional_Manager (multi-level)
    - IF price ≥ W1: Reject request
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 4.2 Implement regional consistency check
    - Verify Regional_Manager's region matches Branch_Manager's region
    - Prevent cross-region approvals
    - _Requirements: 2.3, 2.5_

  - [ ]* 4.3 Write property test for price threshold routing
    - **Property 1: Price Threshold Routing Correctness**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    - Test: Generate random prices, branches, regions → Verify routing destination matches rules

  - [ ] 4.4 Implement request submission endpoint
    - POST /api/special-price-requests/{request_id}/submit
    - Validate prices using validation engine
    - Route request using routing engine
    - Update status based on routing (APPROVED for single-level, PENDING_BRANCH_APPROVAL for multi-level)
    - Record routing information in special_price_request_routing table
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 4.5 Write unit tests for routing logic
    - Test single-level routing (R1 ≤ price ≤ W2)
    - Test multi-level routing (W2 < price < W1)
    - Test rejection cases (price < R1, price ≥ W1)
    - Test region consistency

- [ ] 5. Implement approval and rejection endpoints
  - [ ] 5.1 Implement approve endpoint
    - POST /api/special-price-requests/{request_id}/approve
    - Verify approver is correct Branch_Manager or Regional_Manager
    - For Branch_Manager approval of single-level: Set status to APPROVED
    - For Branch_Manager approval of multi-level: Set status to PENDING_REGIONAL_APPROVAL, route to Regional_Manager
    - For Regional_Manager approval: Set status to APPROVED
    - Record approval in audit trail and routing table
    - _Requirements: 7.2, 7.3, 7.5, 7.7_

  - [ ] 5.2 Implement reject endpoint
    - POST /api/special-price-requests/{request_id}/reject
    - Verify approver is correct Branch_Manager or Regional_Manager
    - Set status to REJECTED
    - Record rejection reason in database
    - Record rejection in audit trail
    - _Requirements: 7.6, 7.7_

  - [ ] 5.3 Implement pending approvals endpoint
    - GET /api/special-price-requests/pending/approvals
    - For Branch_Manager: Show requests with status SUBMITTED or PENDING_BRANCH_APPROVAL
    - For Regional_Manager: Show requests with status PENDING_REGIONAL_APPROVAL
    - _Requirements: 7.1, 7.4_

  - [ ]* 5.4 Write property test for status transitions
    - **Property 2: Status Transition Correctness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    - Test: Generate random status sequences → Verify only valid transitions occur

  - [ ]* 5.5 Write unit tests for approval/rejection logic
    - Test successful approval at each level
    - Test rejection with reason
    - Test unauthorized approver rejection
    - Test multi-level approval flow

- [ ] 6. Implement audit trail and logging
  - [ ] 6.1 Create audit logging function
    - Log all state changes: DRAFT → SUBMITTED → APPROVED/REJECTED
    - Log all modifications with timestamp and modified_by
    - Log all approval/rejection actions with approver_id and reason
    - Store details_json with additional context
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 6.2 Implement audit trail retrieval endpoint
    - GET /api/special-price-requests/{request_id}/audit
    - Return complete history of all actions on request
    - Include timestamps, user_ids, status changes, and reasons
    - _Requirements: 9.4_

  - [ ]* 6.3 Write property test for audit trail completeness
    - **Property 6: Audit Trail Completeness**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
    - Test: Generate random state changes → Verify all changes logged with complete info

  - [ ]* 6.4 Write unit tests for audit logging
    - Test audit entry creation for each action type
    - Test audit trail retrieval and ordering
    - Test immutability of audit entries

- [ ] 7. Implement quote opening prevention
  - [ ] 7.1 Create quote opening validator function
    - Check if quote has associated special_price_requests
    - Verify all associated requests have status = APPROVED
    - Return error with list of unapproved requests if validation fails
    - _Requirements: 3.1, 3.2, 3.3, 10.1, 10.2_

  - [ ] 7.2 Integrate validator with quote opening endpoint
    - Modify existing quote opening logic to call validator
    - Prevent quote confirmation if any request not approved
    - Display error message with unapproved request details
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ] 7.3 Link quote to approved special price requests
    - Store quote_no in special_price_requests table when quote is confirmed
    - Create link for audit trail purposes
    - _Requirements: 10.4_

  - [ ]* 7.4 Write property test for quote opening prevention
    - **Property 3: Quote Opening Prevention**
    - **Validates: Requirements 3.1, 3.2, 3.3, 10.1, 10.2, 10.3**
    - Test: Create request → Submit → Attempt open (should fail) → Approve → Attempt open (should succeed)

  - [ ]* 7.5 Write unit tests for quote opening validation
    - Test quote opening blocked when requests not approved
    - Test quote opening allowed when all requests approved
    - Test error message with unapproved request list

- [ ] 8. Implement employee information retrieval and consistency
  - [ ] 8.1 Create employee info retrieval function
    - Extract employee_id, branch_code, role from JWT token
    - Retrieve employee details from Employees table
    - Validate employee role (Sales, Branch Manager, Regional Manager)
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 8.2 Implement role-based access control
    - Only Sales employees can create requests
    - Only Branch Managers can approve single-level requests
    - Only Regional Managers can approve multi-level requests
    - _Requirements: 5.3, 7.1, 7.4_

  - [ ]* 8.3 Write property test for employee information consistency
    - **Property 5: Employee Information Consistency**
    - **Validates: Requirements 4.3, 5.1, 5.2, 5.3, 5.4**
    - Test: Generate random employees → Verify info matches session and database

  - [ ]* 8.4 Write unit tests for employee info retrieval
    - Test employee info extraction from JWT
    - Test role validation
    - Test access control for different roles

- [ ] 9. Implement request status display and tracking
  - [ ] 9.1 Create request status display endpoint
    - GET /api/special-price-requests/{request_id}/status
    - Return current status, approver info, approval dates
    - For Submitted requests: Show current approver and expected timeframe
    - For Approved requests: Show approval date and approver name
    - For Rejected requests: Show rejection reason and date
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 9.2 Implement request list with status filtering
    - GET /api/special-price-requests?status=DRAFT,SUBMITTED,APPROVED
    - Support filtering by status, date range, customer
    - Return paginated results with request details
    - _Requirements: 6.1_

  - [ ]* 9.3 Write unit tests for status display
    - Test status display for each status type
    - Test approver info display
    - Test rejection reason display

- [ ] 10. Checkpoint - Ensure all backend tests pass
  - Ensure all backend unit tests and property tests pass
  - Verify database schema is correctly created
  - Verify all API endpoints are working
  - Ask the user if questions arise

- [ ] 11. Implement frontend request creation component
  - [ ] 11.1 Create request creation form component
    - Customer search/selection field
    - Item picker with quantity and price inputs
    - Display standard price and calculate price difference
    - Show price difference percentage
    - _Requirements: 1.1, 1.2_

  - [ ] 11.2 Implement form validation
    - Validate required fields (customer, items, prices)
    - Show validation errors inline
    - Disable submit button until form is valid
    - _Requirements: 1.4_

  - [ ] 11.3 Implement save as Draft functionality
    - POST request to /api/special-price-requests
    - Store request with Draft status
    - Allow user to continue editing
    - Show success message
    - _Requirements: 1.3_

  - [ ] 11.4 Implement submit for approval functionality
    - POST request to /api/special-price-requests/{request_id}/submit
    - Validate prices before submission
    - Show error message if validation fails
    - Show success message with routing info
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 11.5 Write unit tests for request creation component
    - Test form rendering and field validation
    - Test save as Draft functionality
    - Test submit for approval functionality

- [ ] 12. Implement frontend request list and status display
  - [ ] 12.1 Create request list component
    - Display list of user's requests with status, customer, price, date
    - Support filtering by status
    - Show pagination controls
    - _Requirements: 6.1_

  - [ ] 12.2 Implement request detail view
    - Display full request details including items
    - Show current status and approver info
    - For Submitted: Show current approver and expected timeframe
    - For Approved: Show approval date and approver
    - For Rejected: Show rejection reason
    - _Requirements: 6.2, 6.3, 6.4_

  - [ ] 12.3 Implement request editing for Draft status
    - Allow editing of Draft requests
    - Prevent editing of Submitted/Approved/Rejected requests
    - Show edit button only for Draft status
    - _Requirements: 1.3_

  - [ ]* 12.4 Write unit tests for request list component
    - Test list rendering and filtering
    - Test detail view display
    - Test edit functionality for Draft requests

- [ ] 13. Implement frontend approval management component
  - [ ] 13.1 Create pending approvals list component
    - For Branch Managers: Show requests pending their approval
    - For Regional Managers: Show requests pending their approval
    - Display request details, customer, items, prices
    - _Requirements: 7.1, 7.4_

  - [ ] 13.2 Implement approval action component
    - Display request details for review
    - Implement Approve button with confirmation
    - Implement Reject button with reason input
    - Show success message after action
    - _Requirements: 7.2, 7.3, 7.5, 7.6_

  - [ ] 13.3 Implement multi-level approval flow display
    - Show approval status at each level
    - For multi-level requests: Show "Pending Regional Manager" after BM approval
    - Show approver names and dates at each level
    - _Requirements: 7.3, 7.5_

  - [ ]* 13.4 Write unit tests for approval component
    - Test pending approvals list display
    - Test approval action functionality
    - Test rejection with reason

- [ ] 14. Implement quote opening integration
  - [ ] 14.1 Integrate quote opening validator with quote UI
    - Check special price request status before opening quote
    - Display warning if requests not approved
    - Show list of unapproved requests
    - _Requirements: 3.1, 3.2, 3.3, 10.1, 10.2_

  - [ ] 14.2 Implement quote confirmation flow
    - Allow quote confirmation only when all requests approved
    - Link quote to approved requests
    - Show success message with quote number
    - _Requirements: 10.3, 10.4_

  - [ ]* 14.3 Write unit tests for quote integration
    - Test quote opening blocked when requests not approved
    - Test quote opening allowed when all requests approved
    - Test error message display

- [ ] 15. Implement notification system
  - [ ] 15.1 Create notification function for approvals
    - Send notification when request is approved
    - Send notification when request is rejected with reason
    - Include request details and approver info
    - _Requirements: 7.5, 7.6_

  - [ ] 15.2 Integrate notifications with approval endpoints
    - Call notification function after approval/rejection
    - Send to original employee
    - Include link to request details
    - _Requirements: 7.5, 7.6_

  - [ ]* 15.3 Write unit tests for notifications
    - Test notification creation for approval
    - Test notification creation for rejection
    - Test notification content

- [ ] 16. Implement approver access control
  - [ ] 16.1 Create access control validation function
    - Verify Branch_Manager can only see requests for their branch
    - Verify Regional_Manager can only see requests from their region
    - Prevent approvers from seeing requests not routed to them
    - _Requirements: 7.1, 7.4_

  - [ ] 16.2 Implement access control in list endpoints
    - Filter requests based on approver's branch/region
    - Return only requests routed to the approver
    - _Requirements: 7.1, 7.4_

  - [ ]* 16.3 Write property test for approver access control
    - **Property 11: Approver Access Control**
    - **Validates: Requirements 7.1, 7.4**
    - Test: Generate random approvers and requests → Verify approvers only see their branch/region requests

  - [ ]* 16.4 Write unit tests for access control
    - Test Branch_Manager sees only their branch requests
    - Test Regional_Manager sees only their region requests
    - Test unauthorized access is blocked

- [ ] 17. Implement price calculation and display
  - [ ] 17.1 Create price calculation function
    - Calculate price_difference = requested_unit_price - standard_unit_price
    - Calculate price_difference_pct = (price_difference / standard_unit_price) * 100
    - Handle edge cases (zero prices, negative prices)
    - _Requirements: 1.2_

  - [ ]* 17.2 Write property test for price calculation
    - **Property 9: Price Difference Calculation**
    - **Validates: Requirements 1.2**
    - Test: Generate random standard and requested prices → Verify calculation is correct

  - [ ] 17.3 Implement price display in frontend
    - Show standard price, requested price, and difference
    - Show difference as percentage
    - Highlight large discounts
    - _Requirements: 1.2_

  - [ ]* 17.4 Write unit tests for price calculation
    - Test calculation with various price combinations
    - Test percentage calculation accuracy
    - Test edge cases

- [ ] 18. Implement routing information storage and retrieval
  - [ ] 18.1 Create routing information storage function
    - Store routing_level (1 for BM, 2 for RM)
    - Store approver_id, approver_branch, approver_region
    - Store routing_timestamp at submission time
    - Store approval_timestamp when approved
    - _Requirements: 2.5, 7.7_

  - [ ] 18.2 Implement routing history retrieval
    - GET /api/special-price-requests/{request_id}/routing
    - Return complete routing history with all levels
    - Show approver info at each level
    - _Requirements: 2.5_

  - [ ]* 18.3 Write property test for routing information accuracy
    - **Property 8: Routing Information Accuracy**
    - **Validates: Requirements 2.5, 7.1, 7.4, 7.7**
    - Test: Generate random routing scenarios → Verify routing info accurate and region-consistent

  - [ ]* 18.4 Write unit tests for routing storage
    - Test routing info storage for single-level
    - Test routing info storage for multi-level
    - Test routing history retrieval

- [ ] 19. Checkpoint - Ensure all frontend tests pass
  - Ensure all frontend unit tests pass
  - Verify all components render correctly
  - Verify all user interactions work as expected
  - Ask the user if questions arise

- [ ] 20. Implement integration tests
  - [ ] 20.1 Write end-to-end test for single-level approval workflow
    - Create request → Submit → Branch Manager approves → Quote opens
    - Verify status changes at each step
    - Verify audit trail is complete
    - _Requirements: 1.1, 2.1, 7.2, 10.3_

  - [ ] 20.2 Write end-to-end test for multi-level approval workflow
    - Create request (W2 < price < W1) → Submit → Branch Manager approves → Regional Manager approves → Quote opens
    - Verify status changes at each step
    - Verify routing to Regional Manager
    - Verify region consistency
    - _Requirements: 2.2, 2.3, 2.5, 7.3, 7.5_

  - [ ] 20.3 Write end-to-end test for rejection workflow
    - Create request → Submit → Approver rejects with reason → Cannot open quote
    - Verify rejection reason is stored
    - Verify employee is notified
    - _Requirements: 7.6, 10.2_

  - [ ] 20.4 Write end-to-end test for price validation
    - Create request with price < R1 → Verify rejection
    - Create request with price > W1 → Verify rejection
    - Create request with valid price → Verify acceptance
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 20.5 Write end-to-end test for concurrent operations
    - Multiple employees create requests simultaneously
    - Multiple approvers approve requests simultaneously
    - Verify no data corruption or conflicts
    - _Requirements: 4.1, 4.2_

  - [ ] 20.6 Write end-to-end test for audit trail
    - Create request → Submit → Approve → Verify complete audit history
    - Verify all state changes logged
    - Verify all approvals logged
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 21. Final checkpoint - Ensure all tests pass
  - Ensure all unit tests pass
  - Ensure all property tests pass
  - Ensure all integration tests pass
  - Verify database integrity
  - Verify audit trail completeness
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all valid inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Checkpoints ensure incremental validation and allow early feedback
- All backend tasks should be completed before frontend tasks
- All frontend tasks should be completed before integration tests
- Database schema must be created before any API endpoints
- Routing engine must be implemented before approval endpoints
- Quote opening validator must be implemented before quote integration
