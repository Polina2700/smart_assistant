# Technical Report: SAP S/4HANA Cloud vs On-Premise — Decision Framework
**Author:** Riku Tanaka (Technical Lead, NovaTech Consulting)
**Date:** 2023-01-20
**Version:** 1.1
**Classification:** Internal + Client-facing

---

## Purpose
This report provides NovaTech's standard framework for recommending SAP deployment model to clients. It should be used during presales and blueprinting phases.

---

## Deployment Models Overview

### 1. SAP S/4HANA On-Premise
Client owns and operates the system on their own infrastructure or hosted in a data center.

**Best for:**
- Companies with existing SAP investment and IT team
- Heavy customization requirements
- Regulated industries with strict data residency requirements
- Large enterprises (>1,000 SAP users)

**Key considerations:**
- Higher upfront cost (hardware + licenses)
- Full control over upgrade schedule
- Customization freedom (ABAP, user exits, BADIs)
- IT team required for basis administration

**Typical NovaTech project cost:** €200,000 - €500,000+

### 2. SAP S/4HANA Cloud (Public Edition)
Multi-tenant SaaS. SAP manages infrastructure and upgrades.

**Best for:**
- Greenfield implementations (no legacy SAP)
- Companies wanting minimal IT overhead
- Subsidiaries of larger groups standardizing globally
- Fast implementation timeline needed

**Key considerations:**
- Limited customization (extensibility framework only, no ABAP)
- Quarterly upgrades mandatory — cannot delay
- Data in SAP data centers (compliance check needed)
- Lower upfront, predictable monthly cost

**Typical NovaTech project cost:** €80,000 - €180,000

### 3. SAP S/4HANA Cloud (Private Edition / formerly RISE)
Single-tenant cloud. SAP manages infrastructure, client gets more control.

**Best for:**
- Mid-to-large companies wanting cloud benefits + customization
- Companies migrating from ECC who need transition period
- Clients with complex integrations

**Key considerations:**
- Higher cost than public edition
- More customization allowed than public
- SAP manages infrastructure but client manages upgrades timing (within limits)

**Typical NovaTech project cost:** €150,000 - €400,000

---

## Decision Matrix

| Factor | On-Premise | Private Cloud | Public Cloud |
|--------|-----------|--------------|-------------|
| Customization needs | High | Medium | Low |
| IT team size | Large | Small-Medium | Minimal |
| Budget (upfront) | High | Medium | Low |
| Budget (ongoing) | Low | Medium | High |
| Implementation speed | Slow | Medium | Fast |
| Upgrade control | Full | Partial | None |
| Data residency control | Full | Partial | Limited |

---

## NovaTech Recommendation Guidelines

**Recommend On-Premise when:**
- Client has existing SAP with significant customizations
- Manufacturing with complex PP requirements
- Client IT team has SAP basis skills

**Recommend Private Cloud when:**
- Client wants cloud but has complex integrations
- Migration from ECC with many custom objects
- Medium-large company (200-500 users)

**Recommend Public Cloud when:**
- Greenfield, no legacy
- Client explicitly wants "standard processes"
- Small-medium company (<200 users)
- Fast go-live required (<6 months)

---

## NovaTech Team Cloud Capabilities (as of January 2023)

| Technology | Certified Consultants | Projects Delivered |
|-----------|----------------------|-------------------|
| SAP ECC 6.0 | 4 | 8 |
| SAP S/4HANA On-Premise | 3 | 5 |
| SAP S/4HANA Public Cloud | 1 (Anna Wolff) | 1 |
| SAP S/4HANA Private Cloud | 2 | 2 |
| Microsoft Dynamics 365 BC | 2 (Riku, Anna) | 3 |
| Microsoft Dynamics NAV | 2 | 4 |

**Gap identified:** No team member certified in SAP BTP (Business Technology Platform). Relevant for cloud integration scenarios. Recommend training investment in 2023.

---

## Integration Considerations for Cloud Deployments

Cloud deployments require API-first integration approach. NovaTech's experience:
- SAP Integration Suite: used on 2 projects
- MuleSoft: used on 1 project (RetailPro assessment)
- Custom REST APIs: used on multiple projects

**Lesson learned (BioMed, 2023):** Always verify exact SAP version in discovery. Client RFPs often say "SAP" or "latest SAP" without specifying version. This caused 3-week delay on BioMed project.

---

*Document maintained by Riku Tanaka. Review annually or after each relevant project.*
