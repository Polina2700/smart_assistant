# Technical Note: ABAP Development Standards
**Author:** Riku Tanaka
**Date:** 2022-03-01
**Version:** 1.0

---

## Purpose
Short reference for ABAP development standards at NovaTech. All custom development must follow these standards.

## Naming Conventions
- Programs: ZNT_[PROJECT]_[DESCRIPTION] (e.g., ZNT_FOOD_GOODS_MOVEMENT)
- Function groups: ZNT_[AREA]
- Classes: ZCL_NT_[DESCRIPTION]
- Interfaces: ZIF_NT_[DESCRIPTION]
- Enhancement implementations: ZEI_NT_[DESCRIPTION]

## Development Principles
1. **No modifications to SAP standard** — use enhancement framework (BADIs, User Exits, Enhancement Spots)
2. **Performance first** — avoid SELECT inside loops, use JOIN or FOR ALL ENTRIES
3. **Error handling** — all programs must handle exceptions and log errors to SLG1
4. **Transport management** — all objects in development transport, no manual changes in production
5. **Code review** — Riku Tanaka reviews all ABAP before transport to QA

## Who Can Write ABAP at NovaTech
- Riku Tanaka: Expert
- Jure Kovač: Intermediate (under supervision)
- Mark Horvat: Basic (configuration ABAP only)
- Others: Not authorized

## When Custom ABAP is NOT Allowed
- SAP S/4HANA Public Cloud: no ABAP allowed (cloud restrictions)
- Dynamics 365/BC projects: AL language, not ABAP

## Code Documentation Requirements
Every custom program must have:
- Header comment: author, date, description, change history
- Inline comments for complex logic
- Technical specification document in project SharePoint
