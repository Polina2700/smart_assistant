# Meeting Notes — BioMed Solutions ERP Status Review
**Client:** BioMed Solutions GmbH
**Date:** 2023-05-10
**Location:** Teams call
**Attendees:** Mark Horvat (NovaTech), Lisa Park (NovaTech Junior Consultant), Dr. Werner Schmidt (Client CFO), Hans Müller (Client IT Director)

## Project Status: YELLOW

Project is currently at risk due to data migration issues discovered during UAT.

## Key Discussion Points

### Data Migration Problems
During UAT week 3, team discovered that client's legacy Oracle EBS system uses non-standard cost center codes (alphanumeric, up to 12 chars). SAP standard is numeric 10-char. Approximately 340 cost centers need manual remapping.

Lisa estimated 3 weeks additional work. Mark thinks 2 weeks if client provides dedicated resource. **Client is not willing to provide internal resource.**

This is a scope gap — not in original SOW. NovaTech position: change request required.
Client position: "This should have been discovered in blueprinting."

### Budget Impact
Original budget: €195,000
Spent to date: €142,000
Remaining: €53,000
Estimated cost to complete (original scope): €61,000 — **already over budget by €8,000**

Change request for data migration fix: additional €22,000 estimated.
Client CFO Werner Schmidt refused to approve. Escalation to NovaTech management required.

### Go-Live Date
Original target: 2023-07-01
Revised target (discussed): 2023-08-15
Client hard deadline (annual audit): 2023-09-30

### Technology Stack Note
Client is running SAP ECC 6.0, NOT S/4HANA as originally stated in RFP. This was discovered during technical assessment in week 1. Project is proceeding with ECC 6.0 — migration to S/4HANA deferred to future project.

## Decisions Made
1. Mark will escalate budget dispute to NovaTech director by 2023-05-12
2. Data migration workaround (custom ABAP program) to be scoped by Riku Tanaka
3. Go-live date officially moved to 2023-08-15

## Lessons Learned (preliminary)
- Always verify exact system version in discovery phase, not RFP
- Cost center mapping must be part of standard blueprinting checklist

## Next Meeting
2023-05-17, 14:00 CET
