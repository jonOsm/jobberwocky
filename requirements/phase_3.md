# /specs/requirements_phase_M5_M6_SaaS_Beta.md
Title: Phase M5-M6 “Multi-Tenant SaaS Beta”  
Status: Draft  
Owner: Engineering Lead  
Updated: 2025-07-29  

## 1. Purpose  
Offer zero-ops hosted service at $19/mo or 10 % of post revenue.

## 2. Scope
1. Tenant sign-up onboarding (domain = `<slug>.nichejobs.dev`).
2. Row-Level Security Postgres schema.
3. Central Stripe Connect billing (per-tenant).
4. Daily encrypted backups (S3).
5. Email relay (SendGrid) for receipts & web-hook failures.
6. Uptime monitoring & status page.

## 3. Functional Requirements
ID | User Story | Acceptance Criteria
---|------------|--------------------
S-1 | *Community owner* signs up | • Wizard collects slug, logo, payment method → board live in < 2 min.
S-2 | *Owner* sets custom domain | • CNAME verify, SSL auto (Let’s Encrypt) within 5 min.
S-3 | *System* auto-patches | • Deploy script updates containers without >60 s downtime.
S-4 | *Owner* restores from backup | • “Restore” dropdown lists last 7 backups; applies in staging mode first.

## 4. Non-Functional
N-1 Multi-tenant isolation: row-level policies; no cross-tenant query possible (verified by integration tests).  
N-2 Uptime SLA 99.5 %.  
N-3 GDPR: Data Processing Addendum auto-emailed on signup.

## 5. Out of Scope
✗ SOC-2 certification (planned after GA).  
✗ Candidate résumé storage.

## 6. Open Questions
• Pricing toggle per post vs. flat monthly—both or forced choice?  
• Free tier with ads?

