# Technical Report: SAP Fiori Implementation Guide
**Author:** Riku Tanaka
**Date:** 2023-02-10
**Version:** 1.2

---

## What is SAP Fiori
SAP Fiori is the modern UX layer for SAP S/4HANA. Replaces traditional SAP GUI for most end-user transactions. Browser-based, mobile-compatible, role-based launchpad.

---

## When to Use Fiori vs SAP GUI

| User Type | Recommended Interface |
|-----------|----------------------|
| End users (transactional) | Fiori |
| Power users (complex transactions) | SAP GUI + Fiori mix |
| Basis/Admin | SAP GUI |
| Developers | SAP GUI + Eclipse |

NovaTech standard: Deploy Fiori for all end-user transactions by default. SAP GUI as fallback for transactions not yet Fiori-enabled.

---

## Fiori Architecture Components

1. **SAP Gateway** — OData service layer between Fiori apps and backend
2. **Fiori Launchpad** — Browser-based entry point, shows user's assigned apps
3. **SAPUI5** — JavaScript framework for Fiori apps
4. **Role-based access** — Fiori roles determine which apps a user sees

---

## Implementation Checklist

### Infrastructure
- [ ] SAP Gateway configured (on same or separate system)
- [ ] HTTPS configured (Fiori requires HTTPS)
- [ ] Browser compatibility tested (Chrome, Edge recommended; IE not supported)
- [ ] Mobile device testing if required

### Configuration
- [ ] Fiori roles assigned to users
- [ ] Launchpad groups configured per user group
- [ ] App-specific backend configurations (varies per app)
- [ ] System alias configured in SAP Gateway

### Performance
- [ ] CDN configured for SAPUI5 resources (or local cache)
- [ ] Database indices reviewed for OData performance
- [ ] Load testing with expected concurrent users

---

## NovaTech Experience with Fiori

### FoodDist (2022) — Warehouse users
- Deployed 8 Fiori apps for warehouse staff
- Used Fiori on shared tablets (10 tablets for 45 warehouse workers)
- Biggest challenge: slow WiFi in warehouse areas
- Solution: Pre-cached key apps, batch sync where possible

### Adriatic Petrochemical (2023)
- Fiori for all FI/CO users (approx. 25 users)
- Standard SAP Best Practices Fiori apps — minimal customization
- Training focus: launchpad navigation, adding bookmarks

---

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|---------|
| Blank screen on login | HTTPS not configured | Configure SSL certificate |
| App not visible in launchpad | Role not assigned | Check Fiori role assignment |
| Slow app loading | CDN not configured | Set up SAPUI5 CDN or local cache |
| Session timeout | Default 30 min | Adjust in system parameters |
| Mobile display issues | SAPUI5 version mismatch | Update to latest SAPUI5 |

---

## Fiori App Catalog
SAP provides 1,800+ standard Fiori apps. NovaTech top used apps:

| App Name | App ID | Use Case |
|----------|--------|---------|
| Post General Journal Entry | F0718 | FI accountants |
| Display Financial Statement | F0708 | Management reporting |
| Manage Purchase Orders | F2229 | Procurement |
| Approve Purchase Orders | F1048 | Approval workflow |
| Manage Goods Movements | F2347 | Warehouse |
| Monitor Deliveries | F1359 | Logistics |

---

## Customization Options
Fiori apps can be adapted without modifying standard code:
1. **UI Adaptation** — Hide/show fields, rename labels, reorder elements
2. **Key User Tools** — Add custom fields, change layouts
3. **Custom Apps** (SAPUI5) — Build new apps for unsupported processes

NovaTech capability: UI Adaptation and Key User Tools (Riku + Jure Kovač). Custom SAPUI5 apps: limited experience, subcontract if needed.
