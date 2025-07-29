# /specs/requirements_phase_M0_M1_MVP.md
Title: Job-Board-in-a-Box — Phase M0-M1 “OSS MVP”  
Status: Draft  
Owner: Product Lead (You)  
Last Updated: 2025-07-29  

## 1. Purpose  
Deliver a minimal, self-hostable job board that charges a flat fee per post via Stripe Checkout.

## 2. Scope
In Scope for MVP
1. CRUD for Jobs, Employers, Categories.
2. Admin authentication (single super-user).
3. Stripe Checkout → on success publish Job.
4. Search & tag filter.
5. Auto-archive after 30 days.
6. SEO: sitemap.xml + JSON-LD JobPosting.
7. One-click deploy buttons (Render, Fly, Railway).
8. JSON feed `/jobs/feed.json` (meta-site prep).

Out of Scope
✗ Candidate application forms.  
✗ Multi-tenant hosting.  
✗ Analytics dashboard.  
✗ Web-hooks.

## 3. Functional Requirements
ID | User Story | Acceptance Criteria
---|------------|--------------------
F-1 | *As an admin* I can create a job | • POST `/admin/jobs/new` returns HTTP 302 to detail page.<br>• Job card visible on index within 1 s.
F-2 | *As an admin* I can edit/expire a job | • PATCH sets `status = expired`, removes from `/` within 60 s.
F-3 | *As an employer* I can pay $10 to publish | • Stripe Checkout session must use product “standard-post” price_id.<br>• Web-hook `payment_intent.succeeded` triggers job publish.
F-4 | *As a visitor* I can search for “flutter” | • GET `/?q=flutter` returns jobs whose `title` or `tags` contains “flutter” case-insensitive.
F-5 | *As a crawler* I can read SEO schema | • `/sitemap.xml` lists all `published` jobs.<br>• Each job page has `<script type="application/ld+json">` conforming to Google JobPosting.

## 4. Non-Functional Requirements
N-1 Security: OWASP Top-10 baseline; CSRF token on all POST.  
N-2 Performance: P95 full-page HTML ≤ 300 ms on 512 MB fly.io VM.  
N-3 Accessibility: WCAG 2.1 AA for public pages.  
N-4 Code Coverage: ≥ 80 % unit tests.  
N-5 License: MIT for all files in phase M0-M1.

## 5. Test Data / Examples
| Field      | Example                           |
|------------|-----------------------------------|
| Title      | Senior Flutter Developer          |
| Tags       | flutter, mobile, dart             |
| Salary_Min | 90000                             |
| Apply_URL  | https://company.com/careers/12345 |

## 6. Open Questions
• Should salary range be required in MVP?  
• Use SQLite vs. Postgres for local dev? (default = SQLite).

