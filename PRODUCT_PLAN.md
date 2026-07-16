# PRODUCT_PLAN.md — ConfusionLayer platform (multi-tenant EdTech + School ERP)

> **Status: DRAFT plan for review — nothing is being built yet.**
> Confirmed direction (2026-07-16). This is the single source of truth for product scope and
> supersedes the hackathon framing in `PROJECT_SPEC.md` (which stays as the record of what the
> current demo does). Read and approve/adjust this before any code changes.

## 0. Confirmed decisions
- **Real, multi-tenant SaaS platform**, timeline flexible.
- **One Organization engine**, three go-to-market **segments**, each with its own marketing
  pages, its own plans, and its own enabled feature modules: **School**, **Tuition Institute**,
  **Individual**.
- **Full ERP is committed scope** (not optional): Admissions, Accounting/Fees, HR/Payroll —
  in addition to the learning product. Modules are feature-flagged so any segment (even an
  individual) can enable what applies.
- **Roles:** Owner, School Admin, Accountant, HR/Staff Manager, Teacher, Student, Parent
  (per-org) + **Platform Admin** (cross-org, separate).
- **Billing:** full plumbing (plans, subscriptions, feature-gating, pricing/checkout UI) but
  **every plan is priced $0** for now. No real charges; provider-swappable later if ever.
- **Rewrite in place on `main`**, keeping each milestone deployable.
- **Sequencing:** foundation (design system, tenancy, auth) → shared learning core → segment
  packaging + marketing → ERP modules → platform admin → polish. Full ERP is in scope but
  sequenced after the foundation it depends on. **ERP starts with Admissions** (front of the
  student lifecycle everything else hangs off), then Accounting/Fees, then HR/Payroll.
- **Curriculum is dynamic and org-authorable** (not just the fixed seed): three sources —
  (a) the shared platform library (CBSE Class 10 Science) as an optional starter, (b) **manual
  authoring** of Subject → Chapter → Topic, (c) **PDF import** that auto-extracts subject/
  chapters/topics from an uploaded document into a reviewable structure. Curriculum management
  is **hierarchy-gated** (Owner / School Admin / Teacher only — never Student/Parent).
- **Brand:** **ConfusionLayer** names the **AI learning engine**. The wider platform gets its
  own umbrella brand (proposal in Section 12) with a distinctive, non-generic-AI identity per
  `DESIGN.md`.

---

## 1. Segments (feature bundles over one engine)

Segments are **presets of enabled modules**, selected at signup and enforced by the org's plan.
The underlying engine is identical; segments differ in which modules/screens/roles are on and
in their marketing.

| Segment | Roles enabled | Modules enabled |
|---|---|---|
| **School** | Owner, School Admin, Accountant, HR/Staff, Teacher, Student, Parent | Learning + Admissions + Accounting/Fees + HR/Payroll + Parent portal |
| **Tuition Institute** | Owner, Teacher, Student (optional Accountant, Parent) | Learning (+ optional light Fees) |
| **Individual** | Owner=Student (self) | Learning for self (optional personal Fees/records) |

Each segment gets its **own promotional pages** (Section 5) and its **own plan catalog**
(Section 7).

---

## 2. Roles & permissions

Per-org roles with a permission matrix by module. High level:

| Role | Curriculum | Learning | Admissions | Accounting | HR/Payroll | Org/Members | Billing |
|---|---|---|---|---|---|---|---|
| **Owner** | full | full | full | full | full | full | full |
| **School Admin** | manage | manage | full | view | view | manage (not billing) | — |
| **Accountant** | — | — | view | full | view | — | — |
| **HR/Staff Manager** | — | — | — | view | full | staff only | — |
| **Teacher** | author/import | teach + briefs + own classes/students | view own students | — | — | — | — |
| **Student** | — | learn (own) | own record | own fees/dues | — | — | — |
| **Parent** | — | view child's progress | view child's admission | view child's fees | — | — | — |
| **Platform Admin** | shared library | cross-org support/management + usage + audit (never self-granted) | | | | | |

Curriculum authoring/import is hierarchy-gated (Owner / School Admin / Teacher). Students and
Parents can never create or import curriculum.

**Hard rules:** frontend route guards + backend authorization on every route; **all queries
org-scoped** (strict tenant isolation, tested); Platform Admin is a separate elevated role.

---

## 3. Architecture

### Frontend (Vue 3 + TS + Pinia + vue-router + Tailwind)
- Multi-route SPA. Layout shells: `PublicLayout` (marketing/auth), `AppLayout` (authed,
  role- and module-aware nav), `AdminLayout` (platform admin).
- Real component library (Section 8). Module screens rendered only when the org's plan enables
  the module and the role permits it.

### Backend (FastAPI + SQLAlchemy + Alembic + Postgres)
- Routers per domain: `auth`, `orgs`, `members`, `billing`, `learning` (existing AI/forecast/
  briefs/progress), `admissions`, `accounting`, `hr`, `parent`, `admin`, `content`.
- `current_context` dependency → `(user, org, role, subscription, enabled_modules)`; enforces
  org-scoping, role, and module-enabled on every protected endpoint.

### Deployment
- Same Oracle VM + nginx + Docker Compose. Add an explicit **migrate step** to the redeploy
  flow (schema changes stop being manual). No infra change otherwise.

---

## 4. Data model (by module — key entities)

**Tenancy/auth:** Organization `{id,name,slug,segment}` · **(M1 decision)** membership is modeled
directly on `User` (`org_id` + `role` + `status`, single org per user) rather than a separate
Membership table; a Membership table is only needed if multi-org-per-user is ever required ·
Plan `{code,segment,name,price_cents=0,limits(json),features[]}` · Subscription
`{org,plan,status,current_period_end,provider=null}` · Invitation · PasswordReset · AuditLog.
User gains `email_verified`, `status`; profile links generalized. Platform Admin = user with
no org + elevated role.

**Curriculum:** Subject/Chapter/Concept/ConceptEdge/Taxonomy gain an optional `org_id`
(`null` = shared platform library; set = org-authored). Sources: shared library (opt-in),
manual authoring, or **PDF import** → `CurriculumImport {id, org, filename, status, extracted
(json draft tree)}` holding only the *extracted structure* for review; the **raw PDF is parsed
in memory and never persisted** (same discipline as the old §5.1 importer, generalized to any
document). AI-assisted structuring uses the ConfusionLayer engine to turn headings into a
subject/chapter/topic tree; a human reviews/edits before it's saved as real curriculum rows.

**Learning (existing, made org-scoped):** Classroom(org) · enrollment · MasteryRecord ·
MasteryHistory · QuizAttempt · TeachBackAttempt · ForecastRecord · ConfusionBrief.

**Admissions:** Applicant · AdmissionApplication `{applicant,org,status,form(json)}` ·
AdmissionStatusHistory · (accepted → provisioned as Student + enrollment).

**Accounting/Fees:** FeeStructure · FeeItem · Invoice · InvoiceLine · Payment/Receipt ·
LedgerEntry · Dues view. (This is the *org's* fee management for its students; recording-based
now, real gateway optional later.)

**HR/Payroll:** Employee · Designation · EmploymentRecord · SalaryStructure · PayrollRun ·
Payslip · (Attendance optional).

**Parent:** Guardian link (Parent user ↔ Student(s)) with read-only scopes.

Migration/backfill: create a default demo org (segment=school), attach existing users/
classrooms/content, seed Free plans + subscription. No data loss.

> Every entity here is a schema change, built via reviewed Alembic migrations per milestone.

---

## 5. URL / route map

**Public / marketing:** `/` (hub) · `/schools` · `/institutes` · `/students` (per-segment
promo) · `/pricing` · `/about` · `/login` · `/signup?segment=` · `/forgot-password` ·
`/reset-password/:token` · `/accept-invite/:token`

**App (authed, role+module gated):**
- Curriculum (Owner/Admin/Teacher): `/app/curriculum` (subjects/chapters/topics manager),
  `/app/curriculum/new`, `/app/curriculum/import` (PDF upload → extract → review → save)
- Learning — Student: `/app/learn`, `/app/learn/:conceptId`, `/app/explore`, `/app/progress`;
  Teacher: `/app/teacher`, `/app/teacher/classrooms[/:id[/unlocks]]`, `/app/teacher/students`,
  `/app/teacher/briefs/{forecast,confusion}`
- Admissions: `/app/admissions` (pipeline, applications, forms)
- Accounting: `/app/accounting` (fees, invoices, payments, dues, ledger)
- HR: `/app/hr` (employees, designations, payroll, payslips)
- Parent: `/app/family` (children: progress, fees, admission)
- Org settings (Owner/Admin): `/app/settings/{org,members,billing}`

**Platform admin:** `/admin/{orgs,users,content,usage,audit}`

Backend API mirrors under `/api/{domain}/…`.

---

## 6. Auth & security
- Signup creates Organization (with chosen segment) + Owner + Free Subscription. Invite-accept
  creates a member in an existing org with a role.
- Login/logout (JWT cookie, existing), password reset (token; **email stubbed** → console/log),
  optional email verification (stubbed initially).
- Route guards (frontend) + role/module authorization (backend) on everything.
- **Tenant isolation is a tested security requirement:** cross-org access → 403/404, with
  explicit tests (org A can't read org B). Platform Admin actions audited.
- Mailer interface with a console/stub implementation now (no external email dependency yet).

---

## 7. Plans (all $0)
Per segment, all `price = 0`, differing by enabled modules + limits (tiers shown to exercise
gating; upgrade path is real, charges are not):
- **Individual:** `individual_free` (learning for self).
- **Institute:** `institute_free` (learning, generous class/student limits) · optionally
  `institute_plus_free` (adds light fees).
- **School:** `school_free` (all modules, all roles).

Billing UI shows current plan, module/limit usage, upgrade path; checkout uses a **StubProvider**
that activates instantly at $0. A real `StripeProvider` remains a later, opt-in item (likely
unnecessary while everything is free).

---

## 8. Design system (defined variables)
Promote `DESIGN.md` to code: Tailwind theme + CSS variables (palette, type scale, spacing,
radius, elevation), webfonts wired (confirm the dependency at M0), and a reusable component
library: `Button, Input, Select, Card, Badge, Modal, Toast, Table, Tabs, Nav/Sidebar,
StatCard, PageHeader, EmptyState, LoadingState, ErrorState, DataGrid`. Every screen composes
these. The teal migration lands here.

---

## 9. Milestones (sequenced; each keeps the app deployable)

- **M0 — Design system + routing shell.** Tailwind theme/CSS vars from DESIGN.md, component
  library, vue-router route map + layout shells + guard scaffolding.
- **M1 — Tenancy data model + migration.** Org/Membership/Plan/Subscription/Invitation/
  PasswordReset/AuditLog + User/Classroom changes; backfill demo org; `current_context` +
  org-scoping + isolation tests.
- **M2 — Real auth & onboarding.** Segment-aware signup (org+owner+free plan), login, logout,
  password reset (stub mail), invite-accept; guards enforced; demo auto-login removed.
- **M3 — Segment marketing sites.** Hub + `/schools` `/institutes` `/students` + `/pricing` +
  `/about`, real UI/UX, linked to segment signup.
- **M4 — Learning core in the new shell.** Teacher + Student apps on real routes, org-scoped;
  migrate all existing learning features (unlocks, tutorial/doubt/quiz/teach-back, forecast,
  briefs, progress, self-start) into the component library + guards.
- **M5 — Curriculum module.** Manual Subject → Chapter → Topic authoring (+ prereq edges,
  taxonomy) and **PDF import** (upload → in-memory structural extraction → AI-assisted
  subject/chapter/topic tree → human review/edit → save). Org-scoped curriculum + shared
  library; hierarchy-gated. Raw PDF never persisted.
- **M6 — Org admin, members & billing (stub, $0).** Members/roles management, plan catalog,
  subscription lifecycle, pricing/checkout (stub), module + limit gating.
- **M7 — Admissions module (ERP starts here).** Applicant intake → review → accept → provision
  student/enroll.
- **M8 — Accounting/Fees module.** Fee structures, invoices, payments/receipts, dues, ledger.
- **M9 — HR/Payroll module.** Employees, designations, salary structures, payroll runs,
  payslips.
- **M10 — Parent portal.** Guardian links; read-only child progress/fees/admission.
- **M11 — Platform admin backend.** Orgs/users/content/usage/audit dashboards.
- **M12 — Migrate/verify/polish.** Seeded demo runs in the full multi-tenant model, richer
  Codex tutorial prompts (standard explanation + everyday analogy + ASCII visual), accessibility
  touch-ups, and **migrate-on-deploy** (backend entrypoint runs `alembic upgrade head` before
  uvicorn — no more manual migrate step). **Done.**
- ~~M13 — Real payment gateway~~ **Removed.** All plans are free; no real payments planned.

Each milestone: build → fresh-subagent diff review → deploy per AGENTS.md → verify live.

---

## 10. Risks
- **In-place on main** ⇒ the live site is in-flux during M0–M4; each milestone kept deployable,
  never deploy a broken state without telling you.
- **Very large scope** (full ERP + 3 segments) ⇒ many sessions; strictly one milestone at a
  time, reviewed + deployed.
- **Tenant isolation** is the top security risk ⇒ explicit cross-org tests before shipping
  M1/M2.
- **Email + payments stubbed** ⇒ real providers are later, opt-in, separately reviewed.
- **ERP depth** (esp. payroll/accounting) is domain-heavy ⇒ we'll build usable module versions
  and iterate, not boil the ocean in one pass.

---

## 11. Resolved calls
1. **Institute segment:** learning core by default with **optional light Fees** (module can be
   toggled on for institutes that collect fees). My call.
2. **Curriculum:** dynamic and org-authorable (shared library optional + manual authoring +
   PDF import), hierarchy-gated. Resolved (Section 4, M5).
3. **ERP start:** Admissions first (M7). My call.
4. **Marketing copy:** I'll draft placeholder positioning/copy per segment; you edit.

## 12. Brand & identity (proposal — rename freely)
- **ConfusionLayer** = the AI learning engine (tutoring, misconception diagnosis, teach-back,
  the Confusion Forecast Engine). Keeps the name and the `confusionlayer.znova.in` equity.
- **Umbrella platform brand (proposal): "Slate."** A school-heritage word (the classroom
  slate) that fits the calm paper-and-ink design language, reads institutional and warm, and is
  deliberately **not** generic-AI (no "AI/GPT/Neural/Smart"). Framing: *"Slate — run your
  school, powered by ConfusionLayer."* Product areas: Slate **Learn** (ConfusionLayer),
  **Admissions**, **Fees**, **People** (HR), **Family** (parent).
- If you'd rather keep **ConfusionLayer as the umbrella** too, that's a clean alternative — say
  the word and I'll drop the separate umbrella.
- Visual identity follows `DESIGN.md` (teal/clay/paper/ink, Fraunces + Public Sans) — distinct,
  textbook-warm, explicitly avoiding the default AI-app look.
