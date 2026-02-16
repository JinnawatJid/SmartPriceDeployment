# Requirements Document

## Introduction

This feature enables automatic creation of Sales Orders (not Sales Quotes) in Dynamics 365 Business Central when a customer confirms a quotation in our system. When a quotation is confirmed, the system will automatically send the order data to BC to create a Sales Order document, eliminating the need for manual data re-entry. The system will integrate with the existing quotation confirmation workflow and use the existing BC API client.

## Glossary

- **Quotation**: A document in our system containing proposed items and prices for a customer (this is NOT a BC Sales Quote)
- **Sales_Order**: A Sales Order document in Business Central (not a Sales Quote) that represents a confirmed customer order ready for fulfillment
- **BC_API_Client**: The existing Business Central OData API client (bc_client.py and bc_sales_order.py)
- **Quotation_Confirmation_Handler**: The backend component that processes quotation confirmations
- **BC_Authentication_Service**: The authentication mechanism using HTTPBasicAuth with user KMITL2
- **Sales_Header**: The main Sales Order document in Business Central
- **Sales_Line**: Individual line items within a Sales Order

## Requirements

### Requirement 1: Automatic Sales Order Creation

**User Story:** As a sales administrator, I want Sales Orders (not Sales Quotes) to be created automatically in Business Central when quotations are confirmed in our system, so that I don't have to manually re-enter order data into BC.

#### Acceptance Criteria

1. WHEN a quotation is confirmed by a customer, THE Quotation_Confirmation_Handler SHALL invoke the BC_API_Client to create a Sales Order
2. WHEN creating a Sales Order, THE System SHALL use the customer number from the quotation as the Sell-to Customer number
3. WHEN creating a Sales Order, THE System SHALL use the quotation reference number as the External Document number
4. WHEN the Sales Header is created successfully, THE System SHALL add all quotation line items as Sales Lines
5. WHEN all Sales Lines are added successfully, THE System SHALL mark the quotation as processed

### Requirement 2: Sales Order Line Item Mapping

**User Story:** As a sales administrator, I want all quotation line items to be transferred to the Sales Order, so that the order matches what the customer confirmed.

#### Acceptance Criteria

1. FOR EACH line item in the confirmed quotation, THE System SHALL create a corresponding Sales Line in the Sales Order
2. WHEN creating a Sales Line, THE System SHALL map the item number from the quotation to the BC item number
3. WHEN creating a Sales Line, THE System SHALL map the quantity from the quotation to the Sales Line quantity
4. WHEN creating a Sales Line, THE System SHALL map the unit price from the quotation to the Sales Line unit price
5. WHEN all line items are processed, THE System SHALL verify that the line count matches the quotation line count

### Requirement 3: Business Central Authentication

**User Story:** As a system administrator, I want the system to authenticate properly with Business Central, so that API calls can be executed successfully.

#### Acceptance Criteria

1. WHEN making API calls to Business Central, THE BC_Authentication_Service SHALL use HTTPBasicAuth with username KMITL2
2. WHEN the BC user account is disabled, THE System SHALL return a clear authentication error message
3. WHEN authentication fails, THE System SHALL log the error details for troubleshooting
4. THE BC_Authentication_Service SHALL use the configured password from bc_config.py

### Requirement 4: Error Handling and Recovery

**User Story:** As a sales administrator, I want to be notified when Sales Order creation fails, so that I can take corrective action.

#### Acceptance Criteria

1. WHEN the Sales Header creation fails, THE System SHALL log the error and return a failure status to the caller
2. WHEN a Sales Line creation fails, THE System SHALL log which line item failed and continue processing remaining lines
3. WHEN any BC API call times out, THE System SHALL retry the operation once before failing
4. WHEN authentication fails with a 401 status, THE System SHALL return an error message indicating the KMITL2 account may be disabled
5. WHEN a Sales Order is partially created, THE System SHALL log the BC document number for manual cleanup

### Requirement 5: Data Validation

**User Story:** As a system administrator, I want quotation data to be validated before sending to Business Central, so that invalid data doesn't cause API failures.

#### Acceptance Criteria

1. WHEN processing a quotation, THE System SHALL verify that the customer number is not empty
2. WHEN processing a quotation, THE System SHALL verify that at least one line item exists
3. WHEN processing line items, THE System SHALL verify that each item has a valid item number
4. WHEN processing line items, THE System SHALL verify that each item has a quantity greater than zero
5. WHEN validation fails, THE System SHALL return a descriptive error message without calling the BC API

### Requirement 6: Integration with Existing Quotation Workflow

**User Story:** As a developer, I want the Sales Order creation to integrate seamlessly with the existing quotation confirmation flow, so that minimal changes are needed to the current system.

#### Acceptance Criteria

1. WHEN a quotation confirmation is processed, THE System SHALL call the Sales Order creation function after the quotation status is updated
2. THE System SHALL use the existing create_sales_header() function from bc_sales_order.py
3. THE System SHALL use the existing add_sales_line() function from bc_sales_order.py
4. WHEN Sales Order creation succeeds, THE System SHALL store the BC document number with the quotation record
5. WHEN Sales Order creation fails, THE System SHALL not prevent the quotation from being marked as confirmed

### Requirement 7: Logging and Auditability

**User Story:** As a system administrator, I want detailed logs of Sales Order creation attempts, so that I can troubleshoot issues and maintain an audit trail.

#### Acceptance Criteria

1. WHEN a Sales Order creation is initiated, THE System SHALL log the quotation ID and customer number
2. WHEN the BC API returns a response, THE System SHALL log the HTTP status code and response body
3. WHEN a Sales Order is created successfully, THE System SHALL log the BC document number
4. WHEN an error occurs, THE System SHALL log the error type, message, and stack trace
5. THE System SHALL include timestamps in all log entries
