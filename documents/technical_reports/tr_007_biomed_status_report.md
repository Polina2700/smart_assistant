# Project Status Report — BioMed Solutions GmbH
**Report Type:** Monthly Status Report #8
**Period:** May 2023
**Author:** Mark Horvat
**Date:** 2023-05-31

---

## Executive Summary
Project status: RED. Budget overrun confirmed. Go-live delayed.

---

## Budget Status

| Category | Original | Spent | Remaining | EAC |
|----------|---------|-------|-----------|-----|
| Consulting | €180,000 | €138,000 | €42,000 | €201,000 |
| Travel | €8,000 | €6,200 | €1,800 | €8,500 |
| Training | €7,000 | €1,200 | €5,800 | €7,000 |
| **Total** | **€195,000** | **€145,400** | **€49,600** | **€216,500** |

**Estimate at Completion (EAC): €216,500 — overrun of €21,500 (11%)**

Note: This does NOT include the pending change request for data migration (€22,000). If approved, total EAC would be €238,500 — overrun of €43,500 (22%).

*[Contradiction with mn_002: meeting notes from May 10 stated spent €142,000 and remaining €53,000. This report from May 31 shows €145,400 spent and €49,600 remaining — consistent with 3 more weeks of work. The earlier notes predated this report.]*

---

## Schedule Status

| Milestone | Original | Revised | Status |
|-----------|---------|---------|--------|
| Blueprinting complete | 2022-12-15 | 2022-12-15 | Done |
| Configuration complete | 2023-02-28 | 2023-03-15 | Done (2 weeks late) |
| Data migration complete | 2023-04-30 | 2023-06-30 | Delayed |
| UAT complete | 2023-05-31 | 2023-07-31 | Delayed |
| Go-Live | 2023-07-01 | 2023-08-15 | Revised |

---

## Key Issues

### Issue 1: Data Migration — Cost Center Remapping (CRITICAL)
**Status:** In progress
**Details:** 340 cost centers require manual remapping from Oracle alphanumeric to SAP numeric format. 
**Impact:** 6-week delay, €22,000 additional cost
**Resolution:** Change request submitted to client on 2023-05-15. Client has not approved as of report date.

### Issue 2: System Version Mismatch (RESOLVED)
**Status:** Resolved in week 2 of project
**Details:** Project scoped for SAP S/4HANA based on RFP. Actual system is SAP ECC 6.0 Enhancement Pack 8.
**Impact:** Project re-scoped to ECC. Some S/4HANA-specific features removed from scope.
**Resolution:** Change order signed by client in November 2022. Project proceeded on ECC basis.

### Issue 3: LIMS Integration Scope (OPEN)
**Status:** Under discussion
**Details:** Client wants real-time integration with LIMS system. Original scope assumed batch integration.
**Impact:** Estimated €15,000 additional if real-time required
**Resolution:** Technical assessment scheduled for June 2023.

---

## Resource Status
- Mark Horvat: 70% (was 80% in proposal — reduced due to Adriatic Petrochemical demands)
- Lisa Park: 100% (testing support)
- Anna Wolff: 20% (FI remote support)

---

## Forecast
If change request approved: Go-live August 15, 2023 — within client's hard deadline (September 30, 2023).
If change request NOT approved: Significant risk. Cannot complete data migration without additional resources.

---

## Recommendation
Escalate change request to NovaTech director and client board level. Decision required by June 7, 2023.
