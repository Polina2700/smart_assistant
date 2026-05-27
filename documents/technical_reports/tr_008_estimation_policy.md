# Internal Policy: Project Estimation Guidelines
**Author:** Lena Bauer (Director)
**Date:** 2023-08-01
**Version:** 3.0 (updated after Q2 2023 lessons learned)
**Applies to:** All NovaTech project estimates and proposals

---

## Overview
This policy establishes mandatory requirements for project estimation. Non-compliance will result in proposal review rejection.

---

## Mandatory Risk Buffer
Effective immediately (2023-08-01):
- All estimates must include minimum **15% contingency buffer**
- Projects with new technology (first/second time): **20% contingency**
- Projects with split consultant allocation: add **10% additional risk buffer**

Previous policy (pre-August 2023) required only 10% contingency. This was insufficient — see BioMed and Balkans Steel lessons.

---

## Estimation Process

### Step 1: Work Breakdown Structure
Every estimate must be broken down to task level (max 40-hour tasks).
No "lump sum" estimates for phases larger than €20,000.

### Step 2: Three-Point Estimation
For each task, estimate:
- **Optimistic (O):** Best case
- **Most Likely (M):** Expected
- **Pessimistic (P):** Worst case

Use PERT formula: **(O + 4M + P) / 6**

### Step 3: Technical Discovery Before Proposal
**Mandatory for all projects >€50,000:**
- Technical discovery call/meeting with client IT
- Verify exact system versions (never trust RFP alone — BioMed lesson)
- Review sample data if data migration involved
- Identify custom objects count (reports, developments)

### Step 4: Data Migration Specific Rules
- Never estimate data migration without seeing actual data sample
- Minimum: 3 hours per object type for assessment
- Custom report rule: assume 70% require full redesign, only 30% can migrate
- Cost center/master data: always ask for sample to check field lengths and formats

### Step 5: Approval
| Proposal Value | Approval Required |
|---------------|------------------|
| <€50,000 | PM + one Senior Consultant |
| €50,000 - €150,000 | PM + Senior + Lena Bauer review |
| >€150,000 | Full leadership review + external risk review |

---

## What Cannot Be Estimated Without Discovery
1. Integration complexity (must see actual APIs)
2. Custom report count (must audit existing system)
3. Data quality (must see data sample)
4. Change management effort (must assess org readiness)

If client refuses discovery access before signing: **increase contingency to 25%** and document explicitly in proposal.

---

## Lessons This Policy Was Built On
- Balkans Steel (2019): +€45,000 overrun — scope creep, no proper WBS
- LogiHub (2020): +€15,000 — COVID + underestimated remote work complexity  
- MediaGroup (2021): +€7,000 — report migration underestimated (70% rule now codified)
- BioMed (2023): overrun risk — data migration, system version mistake (discovery now mandatory)
