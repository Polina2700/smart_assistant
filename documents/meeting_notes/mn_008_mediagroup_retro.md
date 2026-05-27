# Meeting Notes — MediaGroup Project Retrospective
**Client:** MediaGroup d.o.o.
**Date:** 2021-09-15
**Location:** Teams call
**Attendees:** Riku Tanaka, Sarah Chen, Petra Golob (Client IT), Marko Zupančič (Client CFO)

## Project Result: COMPLETED (slightly over budget)

Final cost: €152,000 vs €145,000 budget (+€7,000, +4.8%)

## Root Cause of Overrun
Custom report migration was significantly underestimated.

### Report Migration Reality
- Client had 23 custom reports in NAV
- Estimate at proposal: 8 hours per report = 184 hours
- Actual: average 18 hours per report for 19 reports (4 were simple)
- Simple reports (4): 3 hours each = 12 hours
- Complex reports (19): 18 hours each = 342 hours
- Total actual: 354 hours vs 184 hours estimated = 170 hours overrun = ~€25,500
- Partially covered by contingency — net overrun €7,000

### Why Estimates Were Wrong
1. NAV reports used NAV-specific data structures not directly mappable to BC
2. Client had undocumented business logic in several reports
3. BC reporting tool (Report Builder) has different paradigm than NAV's RDLC

### Fix for Future Projects
Riku's new rule: "Never estimate NAV report migration without seeing the report first."
Standard assumption now: **80% of NAV custom reports require full redesign** (not migration).

## What Worked Well
- Data migration was excellent: 99.8% accuracy
- Timeline: Delivered on schedule despite report issues (used contingency budget, not time)
- Client communication: weekly status reports, no surprises

## Client Satisfaction Score: 4.0/5.0
Client was satisfied with outcome but disappointed by cost overrun.
Marko: "The system works well. We just wish the budget had been more accurate."

## Lessons Applied to Future Projects
1. Report audit mandatory before signing contract
2. Add explicit line item for "report redesign" in proposals (not hidden in migration)
3. Show client examples of BC reports early to align expectations

## Technology Notes
- Dynamics NAV 2018 → Dynamics 365 Business Central 2021
- Migration tool: RapidStart Services + custom AL scripts
- Hosting: Microsoft Azure (client's existing Azure subscription)
