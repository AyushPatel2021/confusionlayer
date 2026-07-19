# PRODUCT_PLAN.md — Slate platform (multi-tenant EdTech + School ERP)

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

---

# PHASE 2 — Product hardening, UX overhaul & missing core (FIX SPEC)

> **Status: planning only — nothing built yet.** M0–M12 made the platform feature-complete on
> paper, but real use surfaced UX, layout, CRUD-completeness, and core-flow gaps. This is the
> spec to fix them. Grouped into workstreams P0–P10; each becomes its own milestone later. Every
> item lists the **problem**, the **fix**, and an **acceptance** bar.

## North Star — the winning feature (finalized 2026-07-18)

"An AI tutor" is commodity; a stateless answer-bot (ChatGPT) is free and faster. Slate wins on the
one thing a stateless bot structurally **cannot** do: keep a **persistent, curriculum-anchored model
of each learner**. Everything defensible stacks on that. The four pillars are **one product, not four
features** — build them as a stack, **schools-first**:

1. **Confusion Map + Forecast — the engine (the moat).** A live per-student knowledge map
   (mastered / decaying / at-risk) + the deterministic Confusion Forecast Engine that predicts the
   concepts a student is *about to get wrong* from decayed prerequisites. Stateful, predictive, and
   **compounding** — the more it's used, the better it knows you (data moat + switching cost).
2. **Exam-Outcome Engine — the promise.** The forecast framed around the board exam: "the concepts
   most likely to cost you marks," ranked, each with a targeted drill and an exam countdown.
3. **Proof-of-Understanding — the quality guarantee.** Socratic scaffolding (won't hand over the
   answer) + teach-back grading → real learning, not copy-paste. The anti-cheat / pro-mastery promise
   schools and parents actually buy.
4. **School Operating System — the delivery + business moat.** Teacher-gated, syllabus-aligned, with
   the whole school (admissions/fees/HR + learning) on one data model. **Schools first** — the buyer,
   the distribution, and the defensibility.

**Positioning (schools-first):** *"Slate is the school platform whose AI engine, ConfusionLayer,
forecasts each student's exam-costing gaps before they happen, proves understanding instead of
handing out answers, and runs the whole school on the same data."*
**Student hook (second):** *"Not another answer bot — Slate maps what you actually know, predicts the
exam concepts that'll cost you marks, and drills them."*

Brand: **Slate** = the platform; **ConfusionLayer** = the AI engine (pillars 1–3) only.

## P0 — Brand split: Slate vs ConfusionLayer
- **Problem:** the two names are used interchangeably across the UI.
- **Fix:** **Slate** = the whole platform/company brand (marketing, app shell, ERP — everywhere).
  **ConfusionLayer** = the name of the **AI learning engine ONLY** (tutoring, doubt-chat, forecast
  briefs, teach-back). It should appear only in the learning-feature context
  (e.g. "Learning · powered by ConfusionLayer"), never as app chrome. Audit every string,
  `<title>`, footer, and doc.
- **Accept:** "ConfusionLayer" appears only around the AI learning feature; all other chrome says Slate.

## P1 — App shell & layout overhaul (the "congested / sidebar not at left" fix)
- **Problems:** the app is centred at `max-w-content` (1120px), so on a laptop there are large empty
  side margins, the sidebar isn't flush to the left edge, content feels cramped and wastes space;
  sidebar/topbar aren't sticky/fixed; there is no user profile menu.
- **Fixes:**
  - Full-viewport shell: **fixed, full-height left sidebar** (own scroll, pinned to the edge),
    **sticky topbar**, fluid main content that uses the full remaining width (reading-heavy views
    keep a max-width, data views go full-width).
  - Collapsible sidebar (desktop collapse + mobile drawer).
  - **User profile menu** in the topbar (avatar → name/org/role, settings, sign out).
  - Standard page header + breadcrumbs; comfortable density; responsive 13" laptop → mobile.
- **Accept:** sidebar pinned to the left and sticky, topbar sticky, content fills the width, profile
  menu works, looks right on a laptop and on mobile.

## P2 — Role dashboards & charts (the "school needs an overview to land on" fix)
- **Problem:** after login you land on a bare screen (e.g. teacher → empty Classroom); no overview.
- **Fixes:** a **dashboard as each role's home**, with KPIs + charts (Chart.js):
  - **School owner/admin:** students, staff, fees collected vs outstanding, admissions funnel,
    this-week forecast risk; charts: fees-over-time (line), admissions funnel, headcount by
    department (bar), mastery distribution (donut).
  - **Teacher:** my classrooms, today's briefs, at-risk students.
  - **Student:** continue learning, mastery trend. **Parent:** children summary.
  - **Platform admin:** growth charts on top of the current usage totals.
- **Accept:** every role lands on a useful dashboard with real numbers and ≥1 chart, then navigates out.

## P3 — Classrooms & enrolment (the MISSING CORE: "signed up as a school, no way to create a classroom")
- **Problem:** classrooms exist only from the seed; a fresh org can't create one, so the whole
  learning loop is unreachable for a real new school.
- **Fixes:**
  - **Classroom CRUD:** create/edit/delete (name, **subject** [→ curriculum], **class teacher**
    [→ teacher member]); list + detail.
  - **Enrolment:** add/remove students (classroom ↔ students, many-to-many); enrol from Admissions
    *and* manually; unlocks + briefs bind to the selected classroom.
  - Backend: classroom + enrolment endpoints (org-scoped, role-gated).
- **Accept:** a brand-new school owner can create a classroom, assign subject + teacher, enrol
  students, and run the full learning loop.

## P4 — Members, roles & departments (RBAC UX + department-scoped access)
- **Problem:** onboarding is invite-by-email only; no clear "create a member, pick role + department";
  department-scoped access isn't surfaced; can't edit role / remove members from the UI.
- **Fixes:**
  - **Members hub (invite-only):** invite a member with **role + department** (Teaching/Learning,
    Admissions, Accounts, HR, Front-office). Edit role, deactivate/remove (with confirm). No
    direct-create with a temp password.
  - **Profile completion on accept:** accepting an invite is a short onboarding — the invitee sets
    their name/password and completes their profile (role-relevant fields) before entering the app.
  - **Departments:** map roles → departments; **owner + school-admin see everything**, a
    department member sees **only their department's** screens (accountant → Accounts, HR → HR,
    teacher → Teaching, parent → Family). Enforce in sidebar, **frontend route guards**, and backend.
  - Members list = proper table with search + filter by role/department/status.
- **Accept:** owner creates members and assigns role+department; each member only sees their
  department; owner/school-admin see all.

## P5 — CRUD completeness & standard view types (list / kanban / form / detail + edit + delete)
- **Problem:** modules are mostly create+list; no edit, no delete, no detail/form views, kanban only
  in Admissions; relational fields are free-text or raw IDs (e.g. invoice recipient is typed, guardian
  link needs a numeric student id).
- **Fixes (applied consistently to Admissions, Fees, HR, Curriculum, Classrooms, Members):**
  - **Standard views:** List (data-table: sort/search/paginate/row-actions), Kanban (status boards),
    Form (create/edit), Detail.
  - **Edit + Delete everywhere** (confirm dialog; void/soft-delete where destructive).
  - **Relational dropdowns (many-to-one):** searchable pickers for student / teacher / subject /
    employee / parent instead of typed names or IDs.
  - **Many-to-many where needed:** classroom↔students, fee-structure↔students (apply one fee to many),
    teacher↔classrooms.
  - **Richer fields:** student (roll no, section, DOB, guardian), employee (join date, phone),
    invoice (line items, due date), application (source, DOB).
- **Accept:** every module has list + form + detail (+ kanban where apt), full edit/delete, and
  relational dropdowns instead of IDs/free text.

## P6 — Curriculum & PDF import fix (413 + link-out; NO storage)
- **Problem:** **413 on upload** — confirmed root cause: nginx `client_max_body_size` is unset →
  defaults to **1MB**, so any PDF > 1MB is rejected by nginx before it reaches the backend (cap 15MB).
- **DECISION (finalized): do NOT store PDFs** — keeps the copyright caution intact and avoids the
  legal risk of a shared textbook library. No filestore, no shared library. Extraction stays
  **in-memory only** (as today).
- **Fixes:**
  - **413 fix:** set nginx `client_max_body_size 6m` (deploy-config) + backend cap **5MB**; add a
    client-side size check + friendly error.
  - **Link-out at the import step:** next to the upload control, show a "Get the official syllabus /
    contents PDF" link out to the source (e.g. NCERT / board site) so the user can download the right
    document and upload it — instead of us hosting copyrighted files.
  - Cleaner import-review UX (uses the P5 form patterns).
- **Accept:** a 5MB PDF imports without 413; a helpful source link is shown at the import step; no PDF
  is persisted anywhere.

## P7 — Design-system components to build (fills the gaps flagged in earlier reviews)
Build a reusable kit these views compose from: **DataTable** (sort/search/paginate/row-actions),
**Select/Combobox** (searchable, many-to-one), **MultiSelect** (many-to-many), **Modal/Dialog** +
**ConfirmDialog**, **Toast** notifications, **Tabs**, **Kanban board**, **FormField** wrappers
(label/error/help), **StatCard**, **Chart** wrappers (line/bar/donut/funnel over Chart.js),
**ProfileMenu**, **Drawer** (mobile nav), **Breadcrumbs**, **Pagination**, **DatePicker**.

## P8 — Feedback, validation, audit & polish
- **Toasts** for success/error (replace the single global error string); inline field validation;
  consistent loading/disabled states; confirm dialogs for destructive actions.
- Wire the existing **AuditLog** table (currently unused) for sensitive actions; surface in
  platform-admin.
- Real **accessibility** pass (focus order, aria, contrast, keyboard nav for tables/menus/dialogs).
- Fix the **mastery-history daily-duplication** seed bug (dedupe on re-seed).
- Consolidate the `admin` vs `platform_admin` role naming.

## P9 — Demo & seeding (so it reads as complete)
- **Problem today:** demo logins exist only for teacher + student — there is **no school demo**, so
  the whole school/ERP/dashboard story can't be seen in one click.
- Seed a richer **multi-org demo**: a full **school** org populated across every department — owner,
  school admin, accountant, HR, teachers, students, classrooms, curriculum, fees, payroll,
  admissions, and a linked parent — plus **per-role demo logins** (school owner, admin, accountant,
  HR, teacher, student, parent) so judges can explore every role and every module in one click.

---

## P10 — Differentiation features (make the winning feature undeniable)
The North Star, turned into things you can see and demo. Mostly new **views/framing** on top of the
existing engine + mastery/decay math (little new backend math):
- **Confusion Map view** (student *and* teacher): a visual knowledge graph per student — nodes
  coloured mastered / decaying / at-risk, edges = prerequisites. The tangible artifact ChatGPT can't
  produce; the hero of the demo.
- **Exam-Outcome forecast** (student-facing): a ranked "top N concepts most likely to cost you marks"
  with an exam-date countdown and a one-tap drill each. (Reframes the existing forecast toward the
  learner + outcome; the teacher already has the class version.)
- **Proactive decay drills** ("3 concepts are fading — 5 min to lock them back in"): surfaces
  decaying mastery as a habit loop, on the student dashboard.
- **Teach-back front-and-centre** as the proof-of-understanding gate (not buried in a tab).
- Note: exam *mode* as a full module stays in the "extra modules, last" bucket, but the exam-outcome
  *framing* of the forecast lands early because it's the headline promise.
- **Accept:** a school owner/teacher/student can each see a live confusion map + an exam-costing-gaps
  list; the demo lands the "predict & prevent, not another answer bot" story in under a minute.

## Extra fixes I recommend (beyond what you listed)
**Implementation status (2026-07-18):** delivered in the Phase 3 workspace milestone.

- Frontend role/route guards are enforced before a page renders; backend authorization remains the source of truth.
- Admissions, invoices, members, and employees accept bounded `q`, `offset`, and `limit` filters; global search finds members, learners, invoices, and classrooms.
- Organization settings now support a name, logo URL, timezone, and currency. Fee export, printable invoices/payslips, in-app notifications, activity feed, and optional SMTP delivery are available.
- Student report cards aggregate learning mastery, fees, and attendance. Attendance, exam practice, timetable, library inventory/loans, and transport routes/assignments are available as school modules.
- CSV exports and print views are intentionally generated on demand; no private student documents are committed to the repository.

- **Frontend role/route guards** (today only `requiresAuth`) — stop wrong-role users reaching pages
  the backend already 403s.
- **Server-side pagination + filtering** for large lists (fees, members, applications) — current
  lists are unbounded.
- **Global search** (jump to a student / invoice / member).
- **Org profile + logo upload** (per-org branding).
- **CSV export** (fees, members, payroll) and printable invoices/payslips.
- **Notifications / activity feed**; optional real **email** (currently stubbed).
- **Student profile / report-card page** aggregating learning + fees + attendance.
- Optional new modules if wanted: **attendance**, **exam mode**, **timetable**, **library/transport**.
- **Timezone + currency** settings per org (amounts are paise today).
- Harden the public AI path (rate-limit + graceful errors).

## Suggested execution order (schools-first)
Foundation — **P0 brand** + **P1 app-shell** + **P7 component kit** → **P2 dashboards** → **P3
classrooms** + **P4 members/departments** (these unblock the real school core) → **P10
differentiation views** (make the moat visible: confusion map + exam-costing gaps) → **P5 CRUD/views**
across modules → **P6 PDF fix (link-out)** → **P8 polish/feedback/audit** → **P9 demo seeding (incl.
school + per-role logins)** → **extra modules last** (attendance / exams / timetable / report cards /
transport).

## Decisions — finalized with the human (2026-07-18)
- **Winning feature:** all four pillars as one stack (Confusion Map + Forecast · Exam-Outcome ·
  Proof-of-Understanding · School OS), **schools-first**. See North Star above; P10 makes it visible.
- **PDF:** do **not** store PDFs (legal). Fix the 413 (nginx 6m + 5MB) and add a link-out to the
  official source at the import step. (P6.)
- **Departments:** Teaching/Learning · Admissions · Accounts · HR · Front-office — confirmed. (P4.)
- **Member onboarding:** invite-only, and the invitee **completes their profile** on accepting. (P4.)
- **Extra modules:** in scope but **last** (after the layout/core fixes) — attendance, exams,
  timetable, report cards, transport. (Order note above.)
- **Demo:** add a **school** demo + per-role logins (today only teacher/student exist). (P9.)

---

## Remaining Delivery Plan (2026-07-18)

This section is the execution queue for the work that remains after the currently deployed
Phase 2 and school-operations milestones. Each block must be tested, committed, and deployed as
one working flow before the next begins.

1. **Member lifecycle and departments (P4):** persist departments rather than deriving them from
   roles; select a department on invitation; complete a role-relevant profile on acceptance;
   support deactivation and safe removal; enforce department visibility in navigation and APIs.
2. **Core record completeness (P5):** add student identity/contact/guardian fields, richer
   applications, employee employment details, invoice line items, searchable relational pickers,
   and consistent detail/edit/delete flows across admissions, fees, HR, classrooms, and members.
3. **Reusable interface kit and quality pass (P7-P8):** finish combobox, multiselect, modal,
   kanban, date picker, stat/chart wrappers; apply them to high-use screens; complete accessibility,
   destructive-action confirmation, loading/error feedback, and platform-admin audit viewing.
4. **Learning-map fidelity (P10):** replace concept-card maps with a prerequisite-edge graph for
   student and teacher/owner contexts, with click-through to targeted review and forecast evidence.
5. **ERP depth and platform administration:** add fees receipts/ledger/line items; HR designation,
   employment and salary structures; complete platform-admin users/content/audit management.
6. **Hardening and documentation:** integration tests for the above flows, permission/tenant
   regression coverage, README/API/deployment updates, and a final responsive/accessibility review.




This below metioned all thing need to fix

1. on a sign in Page We need a slide different thing for a demo like we only want to show a School, institute and individual student need to display login. make sure this are our 4 models and and they can be individually purchased so each have its own thing like individual student can work himself and import the classeroom, subject and all individually and learn himself type. Inststitue need a teacher student type where it need a member access where they can make a more teacher or a Student and also teacher have its needed access where they can create a classrooms and subjects and topics and also we need a functionality of a individual topic based lock and unlock and in that when the teacher invite student it have a limited access like that his own classroom and chapter and topics opened and can access and see his own insights and all type bro. also in that institute plan teacher can have a limited access compare to school teacher. then we have a school, for a school owner we give all access, then its teacher need a some extra things like attendance and all and school all department need there own department access and see there only menu, also for a schoold student they can see there attendance and other benifits school contain all can be done. also in all this when we have a member thing at there we need a connect option which can connect us to there account and we need this functionality to only the schood owner and institute owner need that functionality. so we dont need this much demo button need to show in login we can display 3 good demo option login there and from each we can navigate to there department and all type.
   - [x] Institute owners can now open Members, invite teacher/student members, and use owner-only Connect to switch into active member accounts; school-only office/family roles stay blocked for institute workspaces.
   - [x] Individual learners can now open Curriculum, create subjects/chapters/topics, and import PDFs into their self-study plan; school and institute students remain blocked from curriculum management/import.
2. Need to change a some labels like the whole App name need to be Admin and school have a owner type and the admin need a extra things like how many school have added and how many student and he can see every record and its own dashboard which shows a overview of its apps all school and everything. and also each school need its records display and handle type make sure we dont show other school student class or anything into each other which may cause a privacy issue so. admin only see all things other things dont.
3. we need a profile of a users. where they can change a name and password and all things as per the need they can add a image of them and everything and some basic contact number and all things needed.
4. Admin is a app owner so he need to see a app related dashboard which shows a how many schools are there and all different type of data in dashboard rather then school related things there type.
5. overview and classroom have a same icon pls update that.
6. Need a batter layoyut for a classrooms where it needed each for a school rather then individual bro and when we have a school for any teacher or anyone then we need a autofill that type and also in a institute and individual dont need that its individual so for a admin we need a batter layout for this.
7. [x] also i see in classroom you added a 2 fields different one for search and according to that selection work bro its wrong at all we need a simple one thing like in selection field we need a direct inside search option type bro current one is completely confusion type. also we need to make a custom selection field design or maybe just use any other online available design which support this search and all and everything and use that in whole app insted of normal selection. Completed with a single custom searchable dropdown component.
8. [x] clicking a remove from a classroom student giving a error "Failed to execute 'json' on 'Response': Unexpected end of JSON input". same when deleting a class "Request failed with 500". Completed by making the API helper accept empty 204 responses and preserve real backend errors; classroom delete remains covered by backend tests.
9. [x] When admin go to classroom its showing a "No classroom is available for this user" bro why we are showing a classroom to admin he is not in any class then? remove that menu for a admin. Completed by removing legacy admin from workspace classroom routes/getters and removing the backend classroom fallback for that role.
10. [x] in a student insights the Learner prerequisite map is a completly mess and broken type bro its not good think of something good batter fit type thing bro need complete change in that. Completed by replacing the graph map with prerequisite readiness rows, risk cards, strengths, weaknesses, and today-focus sections.
11. [x] Attendance also need a complete rework bro. like what is that teacher cant go one by one and select attendance type we need a some good thing where we need a roll number for a classroom of a student and according to that teacher just take a attendance and one by one student come to screen according to roll numbers and teacher just select a option and all type and also in a display make a good view to display that attendance bro. Completed with a roll-call workflow, roll/section display, quick status buttons, progress summary, and mark-remaining-present action.
12. [x] curriculam layout is a good but need a batter thing like according to classroom it need to be and based on a teacher the clas sdefault open and in that class teahcer and only see which subject is she is teaching. Completed with classroom-context filtering and default subject auto-open from the assigned classroom.
13. [x] when deleting a suject topic getting a error "Failed to execute 'json' on 'Response': Unexpected end of JSON input". Completed through the shared API helper fix for empty 204 delete responses; curriculum delete actions now use that path.
14. [x] also when the subject gets added we need a teacher who is teaching it and it can be a multiple too. also if its a school then under that school that classroom subject shows and all like think of a school hirarchy structure we need that type thing. Completed by exposing subject assignments from existing classroom hierarchy: School -> Classroom -> Subject -> Teacher, including multiple assigned teachers/classes per subject in curriculum views.
15. [x] in a Import curriculum there is a issue like we need it to do maybe using a codex help to directly show correct subject and topic and all because current thing is not working good so need to implement AI import type which read pdf and add a subject, chapter, topics type. Completed with a Codex cleanup/refine step for extracted PDF drafts, keeping human review before commit and still not storing PDFs.
16. [x] Also Applicant pipeline need a good thing bro like in which class they are going its dropdown and everything good bro with its proper form view and good layout needed for that too bro. Completed with classroom dropdown selection, split applicant/admission-target form layout, and improved applicant pipeline metadata.
17. [x] also i think delete not working for anything check and fix it too. Completed by verifying the shared API helper supports 204 empty delete responses and adding timetable delete regression coverage alongside the existing curriculum/classroom/fees delete coverage.
18. [x] need a batter layout for a invoices too bro what is that half broken looking. Completed by replacing the invoice table with grouped invoice cards, due/paid/billed summaries, line items, payment actions, and a collection-focus panel.
19. [x] same for a Hr payroll bro why cant we add a models and all and give a many2one so its show designation department and all because currently there are no many2one fields and all used which is why its not connected at all we need a complete hirarchy in this bro. Completed by using designation and salary-structure many-to-one selectors, department hierarchy panels, salary structure references, payroll stats, and grouped employee cards.
20. [x] also school operation time table need a good layout bro its broken like we need to make a good display like it shows a each day time vise time table type insted of plain list bro make it good. Completed by rebuilding school operations timetable into a day-wise board with time-sorted lessons, classroom/day comboboxes, room display, summary stats, and remove actions.
21. [x] remove library and transport and update a school operation to timetable thing only bro its not complete to present so. Completed by making the operations page a dedicated Timetable page, removing the library/transport tabs and matching the sidebar and route title to Timetable.
22. [x] also for a member layout we need a complete neww and good layout because when it scales it wont look good at all bro need complete rework there too. Completed with member stats, a structured invite panel, role mix, department-grouped member cards, scalable filters, pending-invite cards, and clearer role/status actions.
23. [x] also to admin dont show school related things bro why admin want to see school he want to see his apps performance and all and not a school so remove all thing related to school from a admin. school owner sees it. Completed by turning platform admin into an app-performance dashboard with adoption, revenue, content, user, and audit signals, removing the organization/workspace detail table from the admin surface.
24. [x] also the account, hr and all that many roles of a school owner are not showing a any menus which need a fix. Completed by opening Fees to accountant and HR & payroll to HR in route guards, adding role-specific sidebar groups for accountant/HR, and adding Account links for workspace-owner flows.
25. [x] also many dasdhboard and all have a empty spaces and all which need a fix. Completed by adding role-specific dashboard actions, hiding empty/zero charts, restricting the classroom empty state to school owner/admin contexts, and making accountant/HR dashboard data module-specific.
26. [x] also in a parent we need some more information about student like its attendance and other things like quize score and all the overview of the things. Completed by enriching the parent child summary API with attendance counts, quiz/teach-back counts, topic strengths/gaps, latest activity, and updating the parent UI to show those details.
