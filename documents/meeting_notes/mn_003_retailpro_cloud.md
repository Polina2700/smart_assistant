# Meeting Notes — RetailPro Cloud Migration Planning
**Client:** RetailPro Balkans d.o.o.
**Date:** 2022-11-08
**Location:** NovaTech Office, Ljubljana
**Attendees:** Sarah Chen (NovaTech PM), Riku Tanaka (NovaTech Technical Lead), Petra Novak (Client Operations Director), Andrej Zupan (Client Head of IT)

## Context
RetailPro operates 47 retail locations across Slovenia, Croatia, Serbia. Currently running on-premise Microsoft Dynamics NAV 2016. Considering migration to Dynamics 365 Business Central (cloud).

## Discussion

### Why Cloud Migration Now
Client reasons:
1. On-premise server lease expires March 2023
2. IT team reduced from 8 to 3 people (cost cutting)
3. COVID accelerated need for remote access
4. Microsoft ending mainstream support for NAV 2016 in 2023 (NOTE: mainstream support actually ended in 2018, extended support until 2023)

### Migration Approach Options Discussed

**Option A: Lift and Shift**
- Move existing NAV 2016 to Azure VM
- Minimal disruption
- Cost: ~€45,000 one-time + €2,800/month Azure
- Does NOT solve support issue long-term

**Option B: Upgrade to Business Central Cloud**
- Full migration to BC cloud
- 3-4 month project
- Cost: €120,000 implementation + €3,200/month BC licenses (47 users)
- Recommended by NovaTech

**Option C: Phased Migration**
- Start with HQ on BC, keep stores on NAV temporarily
- 6-8 months
- Cost: €95,000 + mixed licensing costs
- Most complex to manage

Client leaning toward Option B but concerned about store disruption during peak season (December).

### Key Risks
1. 47 locations need simultaneous cutover or careful phasing
2. Store staff tech literacy low — training critical
3. Serbian locations have local tax compliance requirements not standard in BC
4. POS integration — current POS systems (Casio V-R200) not natively supported by BC

### Team Experience Note
Riku Tanaka has done 2 previous Dynamics NAV to BC migrations (MediaGroup 2021, FoodDist 2022). Sarah Chen has not worked with Dynamics before — this is her first non-SAP project.

## Decision
Client requested formal proposal with all three options by 2022-11-25.

## Next Meeting
After proposal delivery, target 2022-12-06
