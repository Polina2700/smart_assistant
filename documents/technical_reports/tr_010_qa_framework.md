# Technical Report: Quality Assurance Framework
**Author:** Tomasz Kowalski
**Date:** 2022-11-01
**Version:** 1.1

---

## NovaTech QA Standards for ERP Implementations

### Test Types Required on Every Project

| Test Type | Who Performs | When | Pass Criteria |
|-----------|-------------|------|--------------|
| Unit Testing | NovaTech consultant | During config | Each config item works in isolation |
| Integration Testing | NovaTech team | After full config | End-to-end process works |
| User Acceptance Testing (UAT) | Client key users | 4 weeks before go-live | Client sign-off |
| Performance Testing | Riku Tanaka | 2 weeks before go-live | Response <3 sec under load |
| Regression Testing | NovaTech + Client | After each fix | No new defects introduced |
| Cutover Testing (Dress Rehearsal) | Full team | 2 weeks before go-live | Cutover completes in time window |

### Defect Classification

| Severity | Definition | Must Fix Before Go-Live? |
|----------|-----------|------------------------|
| Critical | System crash, data loss, cannot complete core process | Yes |
| High | Core process works but with significant workaround | Yes |
| Medium | Non-core process affected, workaround exists | Recommended |
| Low | Cosmetic, minor inconvenience | No (post go-live) |

### Go-Live Criteria
System can go live only when:
- Zero Critical defects open
- Zero High defects open (or documented exception approved by client)
- UAT sign-off document signed by client project sponsor
- Data migration validation completed (>99% accuracy)
- Hypercare plan agreed

---

## SAP-Specific Testing Notes

### Test Scripts
NovaTech maintains test script library for standard SAP processes.
Available: FI (45 scripts), CO (23 scripts), MM (67 scripts), PP (34 scripts), QM (28 scripts)
Reuse rate: approximately 60% of scripts can be reused across projects.

### Transport Strategy
- Development system: all configuration done here
- Quality system: testing done here — never go-live without QA system
- Production: go-live only

Exception: Some clients don't have QA system (budget). Risk must be documented and client must sign waiver.

### Regression Testing After Patches
SAP delivers support packages and patches. Before applying to production:
1. Apply to QA system
2. Run regression test suite (minimum critical processes)
3. Document results
4. Apply to production only if no new defects

---

## Lessons from Projects

### FoodDist (2022) — Good QA
- Full test script library developed
- 3 rounds of integration testing
- Client ran UAT for 3 weeks with 15 key users
- Result: Go-live with only 2 High defects (both had workarounds, fixed week 1)

### Balkans Steel (2020) — Poor QA
- Testing compressed into 2 weeks due to timeline pressure
- Only 4 key users involved in UAT (insufficient for large scope)
- Performance testing skipped
- Result: Multiple issues at go-live, 6-month stabilization period needed
