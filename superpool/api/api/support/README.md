# Support - Ticket management system

This module is Superpool's internal dispute resolution system designed to
address merchant disputes on behalf of a customer. The system can expose APIs
for ticket creation, updates, status checks, etc., which can be consumed by
other services or front-end applications.

## Architecture

The system should be designed to handle the following:

1. **Ticket Creation**: Merchant should be able to raise a ticket for any
   dispute.
2. **Ticket Assignment**: Tickets should be assigned to support agents based on
   their availability and workload.
3. **Ticket Resolution**: Support agents should be able to update the ticket
   status and resolve the dispute.
4. **Ticket Tracking**: Merchants should be able to track the status of their
   tickets.
5. **Ticket Escalation**: Tickets should be escalated to higher authorities if
   not resolved within a certain time frame - I think i would leverage, the
   priority field to determine when a ticket should be escalated, such that, we
   would mail the ADMINS or MANAGER_ADMINS.

### Types of Disputes

1. **Policy-related**: Issues with the purchased insurance (e.g., incorrect
   policy, coverage disputes, incorrect premium charges, etc).
2. **Claim disputes**: Disagreements over claims, including claim denials,
   delays, or underpayments.
3. **Platform-level disputes**: Technical or transaction errors due to the
   platform (e.g., internal failures, policy issuance delays, etc)
4. **Other**: General or any other disputes not covered by the above categories.

### Nice to have

Automated Ticket Creation:

- Based on certain triggers, such as failed claims processing, a dispute could
  automatically generate a ticket. This ensures no manual oversight is required
  for common issues.
- Email-to-ticket conversion: If users send an email to support, an automatic
  ticket is generated, capturing all necessary data.

Platform Notifications:

- Real-time notifications for all parties involved in the dispute, including the
  merchant, and support team.
- Notifications for ticket status changes, such as when a ticket is created,
  assigned, or resolved.

### Proposed API Endpoints

- **Create Ticket**: POST /dispute/tickets
- **Update Ticket**: PUT /dispute/tickets/:ticket_id
- **Get Ticket**: GET /dispute/tickets/:ticket_id
- **Get All Tickets**: GET /dispute/tickets
- **Assign Ticket**: PUT /dispute/tickets/:ticket_id/assign
- **Resolve Ticket**: PUT /dispute/tickets/:ticket_id/resolve
- **Escalate Ticket**: PUT /dispute/tickets/:ticket_id/escalate

### Data Structure

```json
{
  "ticket_id": "uuid",
  "ticket_type": "string", // choices: 'Policy', 'Claim', 'Merchant', 'Platform'
  "customer": {
    "customer_id": "uuid",
    "name": "string",
    "contact_info": "object"
  },
  "merchant": {
    "merchant_short_code": "string",
    "name": "string"
  },
  "insurer": {
    "insurer_id": "uuid",
    "name": "string"
  },
  "policy_id": "uuid", // If the ticket is related to a policy
  "claim_id": "uuid", // If the ticket is related to a claim
  "description": "string",
  "status": "string", // Current status of the ticket, Enum: Open, In Progress,
  // Resolved, Closed
  "priority": "string", // Enum: Low, Medium, High, Critical
  "attachments": ["file_path"], // List of file paths for documents, at the moment
  // we shouldn't support this
  "assigned_to": "user_id", // The agent handling the ticket
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "history": [
    {
      "timestamp": "timestamp",
      "action": "string", // 'Created', 'Updated', 'Escalated'
      "by": "user_id"
    }
  ]
}
```
