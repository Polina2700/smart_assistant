# Technical Report: Data Migration Methodology
**Author:** Riku Tanaka & Tomasz Kowalski
**Date:** 2022-06-10
**Version:** 2.3
**Classification:** Internal

---

## Overview
This document defines NovaTech's standard data migration approach for ERP implementations. Based on lessons from 12 completed migrations.

---

## Standard Migration Process

### Phase 1: Discovery (Week 1-2)
1. Inventory all source data objects
2. Assess data quality (completeness, accuracy, consistency)
3. Identify data owners on client side
4. Map source fields to target fields
5. Identify transformation rules

**Key deliverable:** Data Migration Scope document

### Phase 2: Design (Week 2-4)
1. Design migration programs/templates
2. Define validation rules
3. Plan cutover sequence
4. Define data volume and performance expectations

### Phase 3: Development (Weeks 4-8, varies by project)
Tool selection:
- **SAP LSMW** (Legacy System Migration Workbench): Standard SAP tool, good for simple migrations, no coding required
- **SAP BAPI/IDoc**: For complex objects requiring business logic
- **ABAP direct input**: For high-volume migrations where performance is critical
- **SAP Migration Cockpit** (S/4HANA): Newer tool, preferred for S/4HANA projects
- **Custom scripts (Python/SQL)**: For data transformation and cleansing pre-SAP

NovaTech standard: Use Migration Cockpit first. Fall back to BAPI if Cockpit doesn't support object. Custom ABAP only as last resort.

### Phase 4: Testing (3 iterations minimum)
| Mock | Timing | Purpose |
|------|--------|---------|
| Mock 1 | Month 2 | Test tools, identify gaps |
| Mock 2 | Month 3 | Full volume test, performance |
| Mock 3 (Dress Rehearsal) | 2 weeks before go-live | Final timing validation |
| Cutover | Go-live weekend | Production migration |

**Acceptance criteria:** Error rate < 0.5%, all critical objects 100% complete

### Phase 5: Cutover
Standard cutover approach:
- Friday 18:00: Legacy system locked for new entries
- Friday 18:00 - Saturday 12:00: Final delta migration
- Saturday 12:00 - Sunday 18:00: Validation and sign-off
- Monday 08:00: Go-live

If validation fails Saturday: decision point — go/no-go.
**Always have rollback plan documented.**

---

## Common Data Objects by ERP Module

### FI (Financial Accounting)
- G/L Account Master
- Customer Master (FI view)
- Vendor Master (FI view)
- Open items (AR, AP)
- Asset master + asset values
- **Typically most complex:** open items with partial payments, asset depreciation history

### MM (Materials Management)
- Material Master (multiple views)
- Vendor Master (MM view)
- Purchase info records
- Open purchase orders
- **Typically most complex:** material master with many plant/storage location extensions

### Historical Data Cutoff
NovaTech recommendation: Migrate open items only (not closed). Historical closed items: archive in legacy or migrate as balance carryforward.
Exception: if client has legal requirement (e.g., tax audit) — migrate last 7 years.

---

## Lessons Learned from Past Projects

### FoodDist (2022) — Success
- Material master: 4,200 records, 99.2% clean migration
- Used SAP Migration Cockpit throughout
- Data quality pre-work: 3 weeks by client team — key to success

### BioMed (2023) — Problems
- Cost center codes: alphanumeric 12-char in Oracle EBS vs numeric 10-char SAP
- 340 cost centers needed manual remapping
- **Not caught in blueprinting — added 3 weeks to project**
- Root cause: insufficient discovery of source system data structures

### Adriatic Petrochemical (2023 — ongoing)
- 4,200 materials identified in scope
- Initial data quality assessment showed 23% of materials missing UoM data
- Client agreed to data cleansing sprint before migration

---

## Tools & Technologies

| Tool | Use Case | NovaTech Experience |
|------|---------|-------------------|
| SAP Migration Cockpit | S/4HANA standard objects | High |
| SAP LSMW | ECC legacy migrations | High |
| Python (pandas) | Data cleansing, transformation | Medium |
| Excel/VBA | Simple transformations, client use | High |
| SQL | Database-level extraction | Medium |
| SAP BAPI | Complex business objects | High |

---

## Data Quality Scorecard Template
Used for every project. Client must sign off before migration begins.

| Object | Total Records | Complete | Accurate | Valid | Action Required |
|--------|--------------|----------|----------|-------|----------------|
| Material Master | TBD | TBD% | TBD% | TBD% | TBD |
| Vendor Master | TBD | TBD% | TBD% | TBD% | TBD |
| Customer Master | TBD | TBD% | TBD% | TBD% | TBD |
| Open AR items | TBD | TBD% | TBD% | TBD% | TBD |
| Open AP items | TBD | TBD% | TBD% | TBD% | TBD |

*Minimum acceptable: 95% complete, 98% accurate for go-live*
