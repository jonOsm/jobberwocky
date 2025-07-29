# /specs/requirements_phase_M3_Pro_Theme.md
Title: Phase M3 “Pro Theme & Add-Ons”  
Status: Draft  
Owner: Product Lead  
Updated: 2025-07-29  

## 1. Purpose  
Monetise via a one-off $49 theme that adds analytics and web-hooks.

## 2. Scope
1. Theme switcher (CSS variables, logo upload).
2. Analytics dashboard:
   • Page views / unique visitors / apply-clicks per job  
   • “Days-to-fill” calculated when admin marks job expired  
3. Web-hook editor supporting Discord, Slack, generic POST.
4. Featured listing toggle (upsell price configurable).
5. Salary-range required flag (env `REQUIRE_SALARY=true`).

## 3. Functional Requirements
ID | User Story | Acceptance Criteria
---|------------|--------------------
T-1 | *Admin* can activate Pro Theme | • Upload License Key → instant CSS swap, no restart.
T-2 | *Admin* sees analytics | • Dashboard graph loads < 1 s; data updated hourly via cron.
T-3 | *Admin* creates Discord web-hook | • Test ping returns HTTP 204; future job publishes POST JSON payload.
T-4 | *Admin* marks job “Featured” | • Job appears in index top section with gold border; Stripe charge uses price_id “featured-post”.

## 4. Non-Functional
N-1 Analytics queries ≤ 50 ms on 10 k rows.  
N-2 License verification offline-friendly (grace Period = 72 h).  
N-3 Backward compatibility with core MIT CSS disabled by flag.

## 5. Out of Scope
✗ Multi-tenant billing (belongs to SaaS phase).  
✗ A/B theme variants.

## 6. Open Questions
• Storage limit for logo file (default 250 KB)?  
• Which chart lib? (chart.js vs. ECharts).

