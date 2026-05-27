# Project Proposal — Microsoft Dynamics 365 Business Central Migration
**Prepared for:** RetailPro Balkans d.o.o.
**Prepared by:** NovaTech Consulting
**Date:** 2022-11-25
**Version:** 2.0
**Valid until:** 2022-12-31

---

## Executive Summary

NovaTech Consulting recommends Option B: full migration from Microsoft Dynamics NAV 2016 to Dynamics 365 Business Central (cloud). This proposal covers the complete migration for RetailPro's 47 locations and approximately 180 users.

---

## Option Comparison

### Option A: Lift and Shift to Azure VM
Move existing NAV 2016 to Azure virtual machine.
- **One-time cost:** €45,000
- **Monthly cost:** €2,800 (Azure infrastructure)
- **Duration:** 6 weeks
- **Pros:** Minimal disruption, fast
- **Cons:** Does not address end-of-support, no new features, technical debt continues

### Option B: Full Migration to BC Cloud (RECOMMENDED)
Complete migration to Dynamics 365 Business Central.
- **Implementation cost:** €120,000
- **Monthly licensing:** €3,200 (180 users × €17.78 Essential license)
- **Duration:** 4 months
- **Pros:** Modern platform, cloud benefits, full support, mobile access
- **Cons:** Higher upfront cost, more disruption, training required

### Option C: Phased Migration
HQ first, then stores in waves.
- **Implementation cost:** €95,000
- **Monthly cost:** Mixed (€1,400 BC + €900 NAV licenses during transition)
- **Duration:** 6-8 months
- **Pros:** Lower risk per wave, spread disruption
- **Cons:** Complex dual-system period, higher total cost over time

---

## Recommended Approach: Option B Details

### Project Timeline
| Phase | Duration | Key Activities |
|-------|----------|---------------|
| Discovery & Design | 3 weeks | Gap analysis, data mapping, customization audit |
| Configuration | 5 weeks | BC setup, master data, workflows |
| Data Migration | 3 weeks | Customer, vendor, item, open transactions |
| Testing | 3 weeks | UAT with key users from 5 pilot stores |
| Training | 2 weeks | Train-the-trainer for store managers |
| Go-Live | 1 week | Cutover, hypercare |

**Target Go-Live:** April 2023 (avoiding December peak season)

### Key Assumptions
1. Client provides 2 dedicated key users for UAT
2. POS integration scoped separately (not included in this proposal)
3. Serbian tax compliance customization: €8,000 additional (included in total)
4. Historical data migration: last 2 years only

### NovaTech Team
- Project Manager: Sarah Chen
- Technical Lead: Riku Tanaka (2 previous NAV-to-BC migrations)
- Functional Consultant: Anna Wolff
- Junior Consultant: Lisa Park

---

## Investment Summary (Option B)

| Item | Cost |
|------|------|
| Implementation consulting | €98,000 |
| Serbian tax compliance | €8,000 |
| Training materials & delivery | €7,000 |
| Project management | €7,000 |
| **Total implementation** | **€120,000** |
| Monthly BC licensing (180 users) | €3,200/month |

**Note:** Monthly licensing is paid directly to Microsoft. NovaTech earns partner margin of 10%.

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Store staff resistance | Change management plan, champion network |
| POS incompatibility | Separate assessment recommended before contract |
| Serbian compliance gaps | Scoped and included in proposal |
| December peak season conflict | Go-live planned April 2023 |

---

## Why NovaTech for This Project
- Riku Tanaka: 2 successful NAV-to-BC migrations (MediaGroup 2021, FoodDist WMS 2022)
- Microsoft Partner status (Gold ERP)
- Local presence in Slovenia, Croatia — on-site support feasible

*NovaTech Consulting d.o.o. | Ljubljana, Slovenia*
