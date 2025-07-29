# /specs/requirements_phase_M8_M9_Meta_Site_GA.md
Title: Phase M8-M9 “Meta-Site General Availability”  
Status: Draft  
Owner: Meta-Site PM  
Updated: 2025-07-29  

## 1. Purpose  
Aggregate all participating boards to solve the “traffic” problem and create network effects.

## 2. Scope
1. Crawler that ingests `/jobs/feed.json` from each site hourly.
2. Feed validator & error dashboard.
3. Central search (Typesense) with filters: keyword, tag, salary, remote, locale.
4. Ranking algorithm: freshness → tag score → paid Boost.
5. Boost upsell ($49/7-day) and revenue-share (30 % to originating board).
6. Weekly digest email.
7. Public API (rate-limited).

## 3. Functional Requirements
ID | User Story | Acceptance Criteria
---|------------|--------------------
M-1 | *Visitor* searches “godot ai” | • Results < 300 ms; links redirect to origin board.  
M-2 | *Board owner* opts in | • Toggle in admin panel sets `meta_opt_in=true`; feed picked up next crawl.  
M-3 | *Employer* buys Boost | • Stripe charge associates with job_id; job pinned on `/` and digest list.  
M-4 | *System* rev-shares | • Monthly payout via Stripe Connect transfer ≥ 30 % Boost revenue to board owner.

## 4. Non-Functional
N-1 Crawler concurrency: handle 2 000 feeds in < 5 min.  
N-2 API rate-limit: 60 req/min/IP.  
N-3 Email deliverability: bounce rate < 2 %.

## 5. Out of Scope
✗ Candidate profile accounts.  
✗ Programmatic ads (planned Phase M9-M10).

## 6. Open Questions
• How to prevent duplicate posts between multiple boards? (hash URL).  
• International tax on rev-share payouts?

