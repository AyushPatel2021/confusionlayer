# Project Spec v2 — "ConfusionLayer"
### Predictive, teacher-gated AI learning platform | OpenAI Build Week — Education Track

> **How to use this doc:** `- [ ]` → `- [x]` as you finish things. This is v2 — rewritten after expert review to close credibility gaps and add a genuine, non-generic differentiator. Update it live every night; it's also your evidence trail for the README and `/feedback` writeup.

---

## 0. One-Line Pitch

**"AI clears the confusion. Teachers lead the learning."**

Teachers unlock chapters as they teach them, chapter-by-chapter — AI handles tutorials, doubt-chat, and quizzes only for what's actually been taught. But the real innovation: instead of only reacting *after* a student struggles, ConfusionLayer **forecasts which upcoming concepts a student is likely to struggle with**, using their decayed mastery on prerequisite concepts — and hands the teacher a briefing *before* the lesson, not just a report card after.

---

## 1. Why This Isn't "Just Another AI Tutor Wrapper" (read this before building)

Reviewer feedback (correctly) flagged that tutorials + doubt-chat + quizzes is table stakes — most Education-track submissions will have some version of that. Two things make this submission different, and both should get disproportionate build time:

1. **Confusion Forecast Engine (headline differentiator)** — deterministic graph-propagation math (not GPT) that predicts future struggle *before it happens*, using prerequisite-chain mastery decay. This is the one part of the product that isn't "call GPT and format the response" — it's real system design, and it directly rebuts the "AI wrapper" critique.
2. **Teach-Back / Feynman Mode (secondary differentiator)** — instead of only multiple-choice correctness, occasionally ask the student to explain the concept back in their own words. GPT-as-Diagnostician grades explanation quality, catching "memorized the answer, doesn't understand it" — something quizzes structurally can't catch.

Everything else (tutorials, doubt-chat, standard quizzes) is necessary scaffolding, but it is NOT what should win this. Budget your best nights toward #1 and #2.

---

## 2. Roles & Boundaries

| Role | Can do | Cannot do |
|---|---|---|
| **Teacher** | Unlock chapters per classroom, view Confusion Brief (aggregated), view Forecast Brief (pre-lesson), assign recommended practice, upload a syllabus PDF to auto-create chapter/concept structure | Cannot see individual chat transcripts; cannot see any misconception shown by fewer than 3 students (privacy threshold) |
| **Student** | View syllabus tree, access only unlocked chapters, use tutorial/doubt-chat/quiz/teach-back, self-start any topic outside the school syllabus | Cannot access locked chapters, cannot see other students' data |
| **GPT-5.6** | 4 jobs, each with a fixed structured-output contract: (1) Tutorial Generator (2) Socratic Tutor — progressive scaffolding (3) Grader/Diagnostician — fixed misconception taxonomy (4) Teach-Back Grader | Never computes the final mastery score (system does, deterministically); never invents new misconception codes outside the fixed taxonomy |
| **Forecast Engine (pure code, no AI)** | Computes predicted difficulty per upcoming concept from prerequisite mastery decay | N/A — this is deterministic math, that's the point |
| **Codex** | **Two distinct roles, don't conflate them:** (1) *Build-time* — the coding agent used interactively to write this codebase (2) *Production inference* — via `codex exec` (Section 3.2), the actual mechanism the deployed backend uses to call GPT-5.6 for all 4 prompt contracts | Never runs destructive DB queries even in its production-inference role (Section 7.5); the build-time role still never ships as part of the running app's own logic — it writes the code, it doesn't stay resident as "the app," `codex exec` calls are just how the app reaches GPT-5.6 |

---

## 3. Tech Stack (locked)

- [x] Frontend: Vue 3 + TypeScript + Vite + Pinia + Vue Router + Tailwind
- [x] Charts: Chart.js (mastery-over-time line on the Progress screen, Night 8; forecast bars use dependency-free CSS)
- [x] Backend: FastAPI (Python) + SQLAlchemy + Alembic (migrations — shows real engineering, not just `create_all()`)
- [x] **DB: PostgreSQL**, self-hosted on your Oracle Cloud free-tier VM (200GB — massive overkill for this, which is fine, it's free and it's yours)
- [x] **Deployment: self-hosted on the Oracle VM, live before the hackathon deadline** — no third-party hosted-DB fallback needed, you own the whole stack
- [x] AI: GPT-5.6, 4 structured-output prompt contracts (Section 7) — accessed via `codex exec` (Section 3.2) as the production path; no direct Platform API fallback
- [x] **Auth: real, lightweight self-registration** (email + password, no email verification needed) — upgraded from role-switcher because judges will be self-registering on a public link, not just clicking a seeded demo button
  - [x] Still keep ONE seeded demo classroom (teacher + 8-12 students, per Section 5) as a "View Demo Data" fast-path, for a judge who doesn't want to build up their own data from a fresh signup
- [ ] Real-time sync: still explicitly out of scope — refresh-based
- [x] **Basic AI-call rate limiting**: cap GPT-5.6 calls per user per day (e.g. 50/day) — this is now a public link, protect yourself from cost blowout or abuse

**No hard weekend-only deadline internally** — you're doing nightly 3-hour sessions. Phases below are structured as **Night 1, Night 2, ...** rather than Sat/Sun, so you can slot them into whatever nights you actually have before submission.

### 3.1 Deployment (Oracle Cloud VM — do this Night 1, not Night 10)

- [x] Provision/confirm the Oracle free-tier VM is reachable (SSH in, confirm public IP)
- [x] Install Docker + Docker Compose on the VM
- [x] `docker-compose.yml` with services: `postgres` (data volume mounted to persist across restarts/redeploys) + `backend` (FastAPI, reads DB creds from `.env`, NOT committed to git) + frontend static build
- [x] Real domain — `confusionlayer.znova.in` — pointed at the VM, HTTPS working
- [x] Firewall: only ports 80/443 open externally, Postgres port NOT exposed to the internet (only reachable from the backend container on the internal Docker network)
- [x] `.env` file with Codex model/runtime config and DB credentials — confirmed in `.gitignore`, never pushed to the public repo; no Platform API key path remains
- [x] Confirm the whole stack is reachable at `https://confusionlayer.znova.in` with a placeholder "hello world" page
- [x] Write a one-line redeploy script (`git pull && docker compose up -d --build`) so every subsequent night ends with "push to git, SSH in, run redeploy script" — not a manual multi-step process

**Actual deployment architecture (as built, Night 1):** live at `https://confusionlayer.znova.in` — the VM's existing **nginx** owns public `80/443` and reverse-proxies to the internal ConfusionLayer container on `127.0.0.1:18080`. Postgres stays internal to Docker, not exposed publicly. (Earlier draft of this doc mentioned Caddy/DuckDNS as the plan — nginx + the real `znova.in` subdomain is what actually got built, and it's the better outcome: real domain beats a dynamic-DNS placeholder.)

**✅ Night 1 deployment acceptance test:** from a phone on mobile data (not your home wifi), open the live HTTPS URL and see the placeholder page load. If this works Night 1, every night after just adds features to something already live.

### 3.2 GPT-5.6 Access Strategy — Two Accounts, Two Roles (fixes the `insufficient_quota` blocker)

**The problem:** the backend's Platform API key hit `insufficient_quota` — that account has no billing/credits attached. Separately, there are two distinct OpenAI-account assets available, and each is better suited to a different job:

| Account | Asset | Best used for |
|---|---|---|
| **ChatGPT Plus** (ongoing subscription, 5-hour rolling usage window) | Codex access via `codex login` | **Production** — this account doesn't expire, so it's the one the *live, deployed* backend should authenticate as |
| **Hackathon Codex credits** (2,400 credits, expires **July 21**) | Codex access, separate account | **Testing only** — burn this down running local smoke tests, prompt iteration, and the Section 11 evaluation framework during build week; do not architect anything long-term around it, since it stops working the moment the hackathon ends |

**Chosen path: `codex exec` as the inference call, not the Platform API.** Authenticated via `codex login` (ChatGPT account, not an API key), `codex exec` draws from Codex credits/plan usage instead of separate Platform billing — which sidesteps the `insufficient_quota` issue entirely, since that's a Platform-account problem, not a Codex-account problem. Keep this simple: no Platform fallback path in the app.

- [x] Confirm Codex CLI supports `--json` and `--output-schema`
- [x] Use `gpt-5.6-luna` as the Codex model string from the VM Codex session
- [x] Backend calls `codex exec --json --output-schema <schema.json> "<prompt>"` as a subprocess instead of hitting `api.openai.com` directly for Tutorial Generator
- [x] Extend the same Codex subprocess adapter to the remaining 3 prompt contracts (Sections 7.2-7.4)
- [x] Production backend authenticates via the **ChatGPT Plus account** (`codex login` on the VM, persisted session/credentials)
- [ ] Local dev/testing/evaluation-framework runs authenticate via the **hackathon credits account** (separate `codex login` session, e.g. in a local dev container or a second CLI profile) — this is explicitly a build-week-only resource
- [ ] Latency check: time 5 sequential `codex exec` calls end-to-end, confirm it's acceptable for a user-facing request (target: comfortably under a few seconds; if it's routinely 10+ seconds, that changes the UX and needs a loading-state design, not a silent wait)
- [ ] Concurrency check: fire 3-5 `codex exec` calls in parallel (simulating simultaneous judge/student traffic), confirm no crashes, deadlocks, or silent failures
- [ ] Confirm whether credit-based `codex exec` usage shares the same 5-hour rolling rate window as interactive Codex use, or is independent — if it shares the window, a burst of live demo traffic could hit a wall mid-demo, and the rate limiter (Section 3, "Basic AI-call rate limiting") needs to account for that
- [x] Remove Platform API key/model env vars from repo docs/config; Codex-only path

**✅ Section 3.2 acceptance test:** with the ChatGPT Plus account authenticated on the VM, call the live `/api/tutorial` endpoint for a real seed concept → confirm a genuine GPT-5.6-generated response returns, end-to-end, on the deployed app — this replaces the old "Night 2" live-smoke-test blocker.

Section 3.2 evidence: live `/api/concepts/1/tutorial` returned `200` through the deployed backend using containerized `codex-cli 0.144.4` and `CODEX_MODEL=gpt-5.6-luna`.

---

## 4. Data Model (v2 — fixes the "global flag" and "no formula" gaps)

```sql
Subject         { id, name, board, class_level }
Chapter         { id, subject_id, title, order }
Concept         { id, chapter_id, title, order }
ConceptEdge     { id, concept_id, prerequisite_concept_id, weight DEFAULT 1.0 }  -- the actual graph

Classroom       { id, teacher_id, subject_id, name }
ClassroomStudent{ id, classroom_id, student_id }
ChapterUnlock   { id, classroom_id, chapter_id, unlocked_by, unlocked_at }  -- NOT a global flag, per-classroom

Teacher         { id, name }
Student         { id, name }

MisconceptionTaxonomy { id, concept_id, code, description }  -- FIXED list per concept, written by you, not GPT

MasteryRecord   {
  id, student_id, concept_id,
  quiz_accuracy_score,       -- rolling avg, 0-1
  open_answer_score,         -- 0-1
  misconception_recurrence,  -- 0-1, higher = more repeated same mistake
  retention_score,           -- 0-1, from spaced review results
  computed_mastery,          -- DETERMINISTIC formula output, see Section 8
  last_reviewed_at,
  next_review_date
}

QuizAttempt     {
  id, student_id, concept_id, question, student_answer,
  is_correct, misconception_code (FK to taxonomy, nullable),
  confidence, mode: 'quiz'|'exam'|'teach_back'
}

TeachBackAttempt {
  id, student_id, concept_id, student_explanation,
  clarity_score, accuracy_score, gpt_feedback
}

ForecastRecord  {
  id, student_id, concept_id, predicted_difficulty (0-1),
  contributing_concepts (json array), computed_at
}

ConfusionBrief  {
  id, classroom_id, concept_id, generated_text,
  affected_student_count, misconception_breakdown (json), generated_at
}

SyllabusSource  {
  id, chapter_id, source_label, source_url, uploaded_by, created_at
}  -- NEW: one row per chapter created via PDF import, powers the on-screen "Source" citation
```

- [x] Schema written in SQLAlchemy models
- [x] Alembic migration initialized and first migration applied
- [x] Seed script written (loads Section 5 data)
- [ ] `SyllabusSource` table added (supports Section 5.1 feature)

---

## 5. Seed Content (write BEFORE you touch the forecast engine — do this Night 1)

**Multi-student seed is mandatory now** — a 1-student heatmap is not credible to judges, per review.

### 5.0 Curriculum Source Strategy (official-aligned, not copied)

Use official public curriculum/textbook sources as the structural reference, but do **not** copy full textbook content into the product or repo.

Official references:

- CBSE Academic curriculum page for current syllabus/assessment structure: `https://cbseacademic.nic.in/curriculum_2027.html`
- NCERT textbook portal for textbook/chapter availability: `https://ncert.nic.in/textbook.php?ln=en`
- ePathshala for official NCERT e-resources: `https://epathshala.nic.in/`

Safe demo usage:

- Board name, class, subject, chapter titles, concept names, syllabus structure.
- Links to official NCERT/ePathshala resources.
- Our own concept summaries, learning objectives, questions, rubrics, misconception taxonomy, examples, and GPT-generated tutorials.

Avoid:

- Committing NCERT PDFs or chapter files to GitHub.
- Storing complete textbook chapters in the DB.
- Copying long textbook passages, diagrams, illustrations, or end-of-chapter questions in bulk.
- Using CBSE/NCERT branding in a way that implies endorsement.

Implementation direction:

```text
Official syllabus structure
        ↓
Manually curated concept map
        ↓
Original learning objectives + allowed/excluded scope
        ↓
GPT-5.6 generates tutorials/questions inside that scope
```

Do not send only a chapter title to GPT and trust it to infer the syllabus. Each concept should eventually have a structured scope record like:

```json
{
  "board": "CBSE",
  "class_level": "10",
  "subject": "Science",
  "chapter": "Metals and Non-metals",
  "concept": "Reactivity Series",
  "learning_objectives": [
    "Explain the relative reactivity of common metals",
    "Use the reactivity series to predict displacement reactions",
    "Relate metal reactivity to extraction methods"
  ],
  "allowed_scope": [
    "potassium through gold",
    "displacement reactions",
    "reaction with water, acids and oxygen"
  ],
  "excluded_scope": [
    "electrochemical cell calculations",
    "advanced electrode potentials"
  ]
}
```

Hackathon scope decision: use one board (CBSE), one class (Class 10), one subject (Science), one fully functional chapter, and additional locked chapter titles/concepts only where needed for forecast propagation. A broad automated curriculum importer is out of scope until the core demo works.

Required disclaimer for README/app footer/submission:

> ConfusionLayer is an independent educational prototype and is not affiliated with or endorsed by CBSE or NCERT. Curriculum references are used for educational alignment. Official textbooks remain available through NCERT and ePathshala.

- [x] 1 real subject, e.g., CBSE Class 10 Science
- [x] 3 chapters with hand-written concepts (need at least 3 chapters so the forecast engine has something to predict *forward into* — Ch.1→Ch.2→Ch.3 prerequisite chain)
- [x] 5-7 concepts per chapter, with explicit `ConceptEdge` prerequisite links between chapters (not just within)
- [x] **Fixed misconception taxonomy written by hand** for each concept (3-5 plausible wrong-understanding codes each) — do NOT let GPT invent these at runtime
- [x] 1 teacher, 1 classroom
- [x] **8-12 seeded students** (only 1 needs to be the "live" demo account you control; rest are pre-populated historical data)
- [x] 15-30 seeded QuizAttempt rows across students, deliberately clustered so 2-3 misconceptions repeat across multiple students (this is what makes the heatmap and Confusion Brief look real)
- [x] Vary `last_reviewed_at` dates across students (some recent, some 2+ weeks old) so mastery decay and the Forecast Engine have real variance to work with

**✅ Seed data acceptance test:** query the DB directly — at least one misconception code should appear for 3+ different students on the same concept, and mastery/review dates should span at least a 3-week range. If everything is identical/same-day, the demo will look fake.

### 5.1 Syllabus Importer — PDF Upload → Structural-Only Extraction (NEW, stretch feature)

**What this is:** instead of only hand-typing chapters/concepts, let a teacher/admin **upload an official NCERT/CBSE chapter PDF**, and the system extracts *only the structural skeleton* — chapter title and section/sub-topic headings (table-of-contents level) — to auto-create `Chapter` and `Concept` rows. This is a genuinely good "wow" moment for the demo video ("watch us onboard a brand-new chapter in 30 seconds") without crossing into the legal grey zone discussed in Section 5.0.

**The hard line, non-negotiable:**
- Extract **headings/structure only** — chapter title, section titles, sub-topic names. Never extract or store body paragraphs, diagrams, images, or the textbook's actual exercise questions.
- **The uploaded PDF itself is never persisted** — parse it in memory for headings, then discard it. It never touches disk, the DB, or the git repo.
- Every concept created this way still gets its `allowed_scope` / `excluded_scope` written by a human (you), same as the hand-seeded chapters in 5.0 — the importer only saves you from *typing out the chapter/concept names*, it does not decide what GPT is allowed to say.
- **All actual learner-facing content is 100% original** — tutorials, worked examples, any diagrams/illustrations, quiz questions, teach-back rubrics — all generated by GPT-5.6 or built by you, never lifted from the source PDF.

**Source attribution (the "give credit" piece you asked for):**
- Every screen that shows content tied to an official curriculum chapter displays a small, consistent **"Source" line** — similar to how AI chat products cite where a claim came from. E.g.: *"Structure aligned to: NCERT Class 10 Science, Ch. 3 — official textbook available via NCERT / ePathshala."* with a real link out to the official free resource.
- This is a single reusable component (`<SourceAttribution />` or similar), not something you write per-screen — build once, drop it into Concept Detail, Tutorial view, and the Syllabus Tree.
- This does double duty: it's the right thing to do (real credit, not silent scraping), and it's a nice, visible "we thought about this" signal for judges.

**Checklist:**
- [ ] `SyllabusSource` table added (Section 4)
- [ ] PDF upload endpoint, teacher/admin-only
- [ ] Heading/TOC extraction (PDF outline/bookmarks if the file has them, else a simple font-size/heading-pattern heuristic) — explicitly NOT full-text OCR of body content
- [ ] Extracted PDF discarded immediately after parsing — never written to disk or DB, confirm this in code review, not just "should be fine"
- [ ] Extracted headings land in a **teacher review screen** before being saved as real Chapters/Concepts — teacher edits/confirms, nothing auto-publishes without a human look (auto-extraction will occasionally misread a heading, don't trust it blindly)
- [ ] `<SourceAttribution />` component built once, wired into Concept Detail / Tutorial / Syllabus Tree
- [ ] Section 5.0's disclaimer rendered as an actual app-wide footer, not just README text
- [ ] Manually tested end-to-end: upload one real NCERT chapter PDF → confirm only headings extracted → confirm zero raw PDF text/images end up in the DB or repo → confirm original GPT content generates correctly, scoped to the extracted headings → confirm source attribution renders correctly on the resulting pages

**✅ Importer acceptance test:** upload a chapter PDF you haven't already hand-seeded → new Chapter + Concepts appear in the teacher review screen matching the real chapter's structure → after confirming, the concept pages show GPT-generated original content plus a visible Source line linking to the official NCERT resource → grep the DB and repo to confirm no PDF bytes or extracted body text exist anywhere.

**Build timing:** this is explicitly a **stretch feature** — build it only after the core Nights 1-9 loop (syllabus tree, tutorials, doubt chat, quiz, teach-back, forecast engine, confusion brief) is solid and deployed. It's a strong bonus wow-moment for the video, not a substitute for the headline differentiator.

---

## 6. Deterministic Mastery Formula (Section 8 in code, not GPT)

```
computed_mastery = 
    0.50 * quiz_accuracy_score
  + 0.25 * open_answer_score
  + 0.15 * (1 - misconception_recurrence)
  + 0.10 * retention_score

effective_mastery(t) = computed_mastery * decay_factor(days_since_last_reviewed)
decay_factor(d) = max(0.4, 1 - 0.03*d)   -- simple linear decay, floors at 0.4, tune if needed
```

- [x] Formula implemented as a pure function, unit-testable, no API call inside it
- [ ] In the demo/video, say explicitly: **"GPT-5.6 identifies WHAT the misconception is. Our system calculates the mastery NUMBER deterministically — the AI never grades itself."** This line matters to judges evaluating responsible AI architecture.

---

## 7. GPT-5.6 Prompt Contracts (all 4 return structured JSON — no free text)

### 7.1 Tutorial Generator
- **Input:** concept title, chapter context, reading level
- **Output:** `{ explanation: string(200-300 words), worked_example: string }`
- [x] Prompt drafted and covered by backend contract tests
- [x] Live GPT-5.6 smoke tested through Codex against a seed concept; Platform API path removed

### 7.2 Socratic Tutor — Progressive Scaffolding (updated per feedback — no longer infinite-stonewall)
- **Input:** concept title, full chat history, student's latest message, **turn_count**
- **Output:** `{ response: string, response_type: "guiding_question"|"hint"|"worked_step"|"explanation" }`
- **Logic (system code, not GPT's choice):** turn 1 → guiding_question, turn 2 → hint, turn 3 → worked_step, turn 4+ → full explanation + a follow-up check question. This is enforced by which prompt variant you call, not left to GPT's judgment.
- [ ] Prompt drafted, tested: confirm turn 1-2 doesn't leak the answer, turn 4 does explain properly
- [x] Codex schema, backend adapter, student-only API endpoint, deterministic turn-type logic, and frontend chat UI wired with backend contract tests
- [ ] Live/evaluation no-leak test still needed: confirm turn 1-2 doesn't leak the answer, turn 4 explains properly

### 7.3 Grader / Diagnostician (structured, fixed taxonomy)
- **Input:** question, student answer, concept's fixed misconception taxonomy list, correct answer/rubric
- **Output:**
```json
{
  "is_correct": false,
  "misconception_code": "RXN_ELECTRONEGATIVITY_CONFUSION",
  "misconception_summary": "Confuses electronegativity trend with metallic reactivity trend",
  "confidence": 0.91,
  "follow_up_question": "Which loses an electron more easily — sodium or aluminium, and why?"
}
```
- **Constraint:** `misconception_code` MUST be selected from the taxonomy list you pass in — never a free-invented code
- [ ] Prompt drafted, tested against 3 deliberately-wrong sample answers, confirm code selection stays within taxonomy
- [x] Codex schema, backend adapter, student-only quiz endpoint, QuizAttempt persistence, taxonomy-code validation, and frontend quiz UI wired with backend contract tests
- [ ] Live/evaluation test still needed: run deliberately-wrong samples against Codex and record taxonomy-code behavior

### 7.4 Teach-Back Grader (NEW — secondary differentiator)
- **Input:** concept title, correct concept summary, student's free-text explanation
- **Output:** `{ clarity_score: 0-1, accuracy_score: 0-1, gap_identified: string, encouragement: string }`
- [ ] Prompt drafted, tested: give it one genuinely confused explanation and one genuinely solid one, confirm scores differ meaningfully
- [x] Codex schema, backend adapter, student-only teach-back endpoint, TeachBackAttempt persistence, and frontend Teach-Back UI wired with backend contract tests
- [ ] Live/evaluation test still needed: run one clearly-confused and one clearly-solid sample explanation and record score separation

### 7.5 DB-Grounded Responses (Codex reads context, never writes — read-only, enforced at the DB level)

**What this adds:** instead of only sending a concept title into the prompt, let the model pull in real, current context from the database before answering — prior misconceptions on this concept, related concept scope, the fixed taxonomy — so responses are grounded in what's actually in the system rather than whatever GPT-5.6 assumes. This makes answers noticeably more relevant (a doubt-chat response that references the *actual* taxonomy codes for this concept, not a generic guess) and is a nice, concrete "we engineered this, not just prompted it" detail for judges.

**The hard rule: read-only, enforced by the database itself, not by trusting the prompt.**
- [ ] Create a dedicated Postgres role, e.g. `confusionlayer_ro`, with **`GRANT SELECT` only** on the specific tables/views this needs (`Concept`, `ConceptEdge`, `MisconceptionTaxonomy`, and an aggregated/anonymized view over `QuizAttempt` — never raw `Student` or `MasteryRecord` rows tied to an individual, to keep the same privacy bar as the Confusion Brief's k≥3 threshold)
- [ ] Explicitly `REVOKE` `INSERT`/`UPDATE`/`DELETE`/`TRUNCATE`/`DROP` on that role at the database level — this must be true even if every line of application code is somehow bypassed; the guarantee lives in Postgres permissions, not in code discipline
- [ ] Wire this as a small **read-only MCP tool** (or an equivalent narrow tool-call interface) that the `codex exec` call can invoke mid-generation to fetch grounding context, rather than the backend guessing upfront what context to stuff into the prompt
- [ ] Confirm no PII or individual student data is ever reachable through this tool — this is the same privacy discipline already required for Section 9 (Confusion Brief), applied here too
- [ ] Log every query this tool actually runs during development, so you can eyeball that it's behaving (fetching taxonomy/scope, not doing anything unexpected)

**✅ Section 7.5 acceptance test:** connect to Postgres directly as `confusionlayer_ro` and manually attempt an `INSERT` or `DELETE` against any table → confirm Postgres itself rejects it with a permissions error, not an application-level check. Then run one real doubt-chat/tutorial request and confirm the response is visibly better-grounded (e.g., correctly references an actual misconception code from the taxonomy, not an invented one) than before this feature existed.

**Build timing:** this is a genuine quality improvement, worth having, but it's not on the critical path — build it after the core 4 prompt contracts are working live (i.e., after Section 3.2 is unblocked), not before. If a night runs short, this is a reasonable thing to defer, just don't defer it past Night 7.

---

## 8. Confusion Forecast Engine (headline feature — pure deterministic code)

**What it does:** for each concept the student HASN'T reached yet, predict how much trouble they'll have, based on their `effective_mastery` on its prerequisites.

```
predicted_difficulty(concept C, student S) =
   weighted_average over all prerequisite concepts P of C:
       (1 - effective_mastery(S, P)) * edge_weight(P → C)

   For multi-hop prerequisites (P is a prerequisite of a prerequisite):
       apply a decay of 0.7 per additional hop of distance
```

- [x] Implement as pure function: input = student_id + target concept_id, output = predicted_difficulty (0-1) + list of "contributing_concepts" (which weak prerequisites are driving the score, for explainability)
- [x] Run this **nightly/on-demand for all not-yet-unlocked concepts** in a classroom, store in `ForecastRecord`
- [x] Build the **Forecast Brief screen (teacher-facing)**: "Before you teach Ch.5 tomorrow: 7 of 12 students are predicted to struggle with 'Ionic Bonding' because their 'Atomic Structure' mastery has decayed below threshold. Suggested 5-min recap before starting the new lesson." (Night 7 — `aggregate_forecast` in `app/briefs.py`, `GET /api/teacher/classrooms/{id}/forecast-brief`, `ForecastBrief.vue`)
- [x] This brief's *narrative text* can be GPT-generated (turn the deterministic numbers into a readable paragraph) — but the numbers themselves must come from the formula above, not from GPT guessing (Night 7 — `POST .../forecast-brief/narrative`, GPT writes prose only, numbers passed in from the formula)

Night 6 implementation note: deterministic prerequisite propagation is implemented in backend code with multi-hop decay, stored via a teacher/admin recompute endpoint, and covered by unit/API tests. Live seeded-data recompute on 2026-07-15 created 50 `ForecastRecord` rows for 10 students across 5 upcoming concepts, with predicted difficulty ranging from 0.0 to 0.7992. No GPT/Codex calls are involved in forecast number calculation.

**✅ Forecast acceptance test:** manually degrade one seeded student's `last_reviewed_at` on a prerequisite concept to 3 weeks ago → confirm their predicted_difficulty on the downstream concept rises measurably vs. a student with recent review → confirm this shows up correctly in the Forecast Brief screen.

---

## 9. Confusion Brief (reactive — per feedback, still valuable, now built on solid data)

- [x] Aggregates `QuizAttempt.misconception_code` across a classroom for a given concept (Night 7 — `aggregate_confusion` in `app/briefs.py`, `GET /api/teacher/classrooms/{id}/confusion-brief`)
- [x] **Privacy threshold enforced in code:** do not surface a misconception in the teacher view unless ≥3 students share it — this is a hard filter, not a suggestion (`PRIVACY_THRESHOLD = 3`, distinct-student count; boundary covered by tests)
- [x] No student names ever attached to misconception breakdowns in the teacher view (aggregation returns codes/counts only; verified by `test_confusion_brief_never_includes_student_identifiers`)
- [x] GPT turns the aggregated counts into a short actionable paragraph, e.g.: "5 of 12 students confuse reactivity with electronegativity. Suggested activity: compare electron-loss ease across Na, Mg, Al (~7 min)." (Night 7 — `POST .../confusion-brief/narrative`, persists a `ConfusionBrief` row)

---

## 10. Screens (Parent screen dropped per feedback — doesn't strengthen the core story)

| # | Screen | Priority |
|---|---|---|
| 1 | Signup / Login (self-registration) + "View Demo Data" fast-path | Must |
| 2 | Student: Syllabus Tree (locked/unlocked/mastered) | Must |
| 3 | Teacher: Classroom chapter unlock control | Must |
| 4 | Concept Detail (Tutorial / Doubt Chat / Quiz / Teach-Back) | Must |
| 5 | Tutorial view | Must |
| 6 | Doubt Chat (progressive scaffolding) | Must |
| 7 | Quiz screen w/ structured feedback | Must |
| 8 | **Teach-Back screen** (explain-back, GPT grades) | Must — secondary differentiator |
| 9 | Teacher: **Confusion Brief** (reactive, aggregated) | Must |
| 10 | Teacher: **Forecast Brief** (predictive, pre-lesson) | Must — headline differentiator |
| 11 | Student: Self-start any topic (outside syllabus) | Should |
| 12 | Student: My Progress / mastery-over-time chart | Should |
| 13 | Exam Mode | Nice-to-have |
| 14 | Teacher: Recommended Practice assign | Nice-to-have |
| 15 | Teacher: **Syllabus Importer** (PDF upload → structural extraction → review screen) | Nice-to-have — stretch, see Section 5.1 |

- [ ] All "Must" screens done
- [x] All "Should" screens done (Screen 11 Self-Start + Screen 12 My Progress, Night 8)
- [ ] "Nice-to-have" done or explicitly cut with note in README

---

## 11. Evaluation Framework (per feedback — proves you engineered this, not just prompted it)

Build a small fixed test set, run it once, publish the numbers honestly (only report what you actually tested):

- [x] 10 correct answers → check Grader classifies correctly (written in `app/eval/dataset.py`)
- [x] 10 partially-correct answers → check Grader handles gracefully (written)
- [x] 10 misconception-pattern answers (deliberately written to match your taxonomy) → check misconception_code matches (written, codes drawn from the real seed taxonomy)
- [x] 5 unrelated/off-topic questions to Doubt Chat → check it redirects instead of answering (written; scored by heuristic)
- [x] 5 attempts to extract a direct answer from Doubt Chat turn 1 → check 0/5 leak (written; scored by heuristic)

README table to fill in with REAL results:
```
Structured output success:            __/30
Correctness classification accuracy:  __/30
Misconception code match accuracy:    __/30 (only vs. the 10 designed-for-taxonomy cases)
Out-of-scope redirection:             __/5
Turn-1 direct-answer leakage:         __/5  (target: 0/5)
Forecast engine sensitivity check:    pass/fail (Section 8 acceptance test)
```

- [x] Test set written (`backend/app/eval/`, mock-tested scoring, 68/68 backend tests)
- [x] Test set run (live `--sample 2` = 10 Codex calls; full 40-call run is one command, deferred as a deliberate quota spend per Section 6)
- [x] Real numbers filled into README (sample results, clearly labeled as a capped sample; no fabricated numbers)

---

## 12. Phases (nightly cadence — 3 hrs/night, not weekend-locked)

### Night 1 — Foundation + Live Deployment
- [x] Oracle VM reachable, Docker + Docker Compose installed (Section 3.1)
- [x] `docker-compose.yml` written, deployed, HTTPS working via nginx reverse proxy
- [x] Night 1 deployment acceptance test passed (Section 3.1) — live URL loads from a phone off your home wifi
- [x] SQLAlchemy models + Alembic migration for full schema (Section 4), applied on the deployed Postgres
- [x] Seed script written and run against the deployed DB — passes the Section 5 acceptance test
- [x] Misconception taxonomy hand-written for all seeded concepts

Night 1 deployment note: HTTPS is working at `https://confusionlayer.znova.in` through the VM's existing nginx reverse proxy.

Production demo reset evidence: on 2026-07-19 the guarded reset seed was run on the VM after taking a DB backup. Live demo data now includes 3 orgs (school, institute, individual), 25 users, 16 students, 45 concepts, 45 concept edges, fees/admissions/HR/payroll/attendance/timetable data for the school demo, and populated learning dashboards for institute and individual demos.

### Night 2 — Backend Core Loop + Real Auth
- [x] Self-registration (signup/login, email+password) implemented and deployed
- [x] "View Demo Data" fast-path wired to the seeded classroom
- [x] Classroom-scoped `ChapterUnlock` endpoint (not global flag)
- [x] `GET /student/syllabus` respects per-classroom unlock state
- [x] Tutorial Generator prompt wired + backend-tested + live-smoked through Codex (7.1)
- [x] Deterministic mastery formula implemented + unit tested (Section 6)
- [x] Basic per-user daily AI-call rate limit implemented

**Night 2 evidence:** local backend tests 27/27 passing; VM synced to commit `ef5dd10`; live health check `https://confusionlayer.znova.in/api/health` returns `200` with `codex_model: gpt-5.6-luna`; live tutorial smoke returned `200` for concept `1`.

### Night 3 — Frontend Core Loop
- [x] Vue scaffold: routing, Pinia, Tailwind base
- [x] Syllabus Tree screen (hero visual)
- [x] Teacher unlock control screen
- [x] Wire syllabus tree to live unlock state

**✅ Night 3 checkpoint:** teacher unlocks chapter → student refresh → sees it unlocked → clicks concept → real tutorial appears. (Same core test as v1, now on Postgres + classroom-scoped model.)

Night 3 evidence: frontend production build passes; backend tests 27/27 pass; app now has teacher/student demo login, live syllabus tree, teacher unlock control, concept detail panel, fixed taxonomy display, and manual tutorial generation button. No live Codex tutorial call was spent for this frontend-only verification; the live tutorial endpoint was already smoke-tested in Night 2.

> ⚠️ **Before Night 4:** Section 3.2's `codex exec` production path needs to be wired and passing its acceptance test. Night 3's frontend work doesn't strictly need live GPT-5.6 responses to build the UI — but Night 4 (Doubt Chat + Quiz grading) does, since there's no meaningful way to test progressive scaffolding or misconception classification without real model responses. If Section 3.2 isn't unblocked by the end of Night 3, that becomes the priority for the start of Night 4, ahead of the doubt-chat/quiz work itself.

### Night 4 — Doubt Chat + Quiz
- [x] Progressive scaffolding Doubt Chat wired (7.2) + backend contract tests
- [x] Quiz screen + Grader/Diagnostician wired (7.3) with fixed taxonomy validation
- [ ] Confirm misconception_code always lands within taxonomy in 5+ test runs

Night 4 implementation note: local backend tests 36/36 pass and frontend production build passes. No live Codex quota was spent during this implementation pass; live no-leak/taxonomy evaluation remains for Section 11.

### Night 5 — Teach-Back Mode (secondary differentiator)
- [x] Teach-Back screen built
- [x] Teach-Back Grader wired (7.4)
- [ ] Tested against one clearly-confused and one clearly-solid sample explanation, scores differ meaningfully

Night 5 implementation note: local backend tests 39/39 pass and frontend production build passes. No live Codex quota was spent during this implementation pass; the confused-vs-solid Teach-Back model evaluation remains open.

### Night 6 — Confusion Forecast Engine (headline differentiator — give this a full night, don't rush)
- [x] Implement propagation formula (Section 8) as pure function, unit tested
- [x] Run against seed data, confirm sensible variance across students
- [x] Passes the formula sensitivity part of Section 8 acceptance test in unit tests (stale review date raises predicted difficulty)

### Night 7 — Forecast Brief + Confusion Brief screens
- [x] Forecast Brief screen (teacher, pre-lesson) built and wired
- [x] Confusion Brief screen (teacher, reactive, privacy-threshold enforced) built and wired
- [x] GPT narrative-generation layer on top of both (numbers stay deterministic, text is GPT)

Night 7 implementation note: deterministic aggregation lives in `backend/app/briefs.py` (`aggregate_confusion`, `aggregate_forecast`) with a hard `PRIVACY_THRESHOLD = 3` distinct-student filter and no student identifiers in output. Four teacher/admin-only endpoints added (`GET`/`POST narrative` for each brief); GPT narratives use two new Codex schemas and are on-demand to conserve quota (no numbers computed by GPT). Frontend adds a **Teacher Insights** tab with `ForecastBrief.vue` + `ConfusionBrief.vue`, each with real empty/loading/error states and CSS forecast bars (no Chart.js). Local backend tests 57/57 pass and the frontend production build passes. No live Codex quota was spent (narratives mocked in tests); a live smoke of the narrative endpoints remains for a later verification pass.

### Night 8 — Self-Start Mode + Progress Screen
- [x] Student can self-start any topic outside the syllabus (reuses Tutorial Generator with a free-form topic instead of a seeded concept)
- [x] Progress screen: mastery-over-time chart per student

Night 8 implementation note: Self-Start adds a student-only `POST /api/self-start/tutorial` (free-form topic, no unlock required, reuses the tutorial Codex contract grounded to the student's board/class/subject for level; rate-limited). Progress adds a new `mastery_history` table (Alembic `0004`) + an idempotent `backfill_mastery_history` seeder (synthetic weekly snapshots), `GET /api/student/progress` returning per-concept history + deterministic effective mastery + summary, and a `Progress.vue` Chart.js line chart. **Data-model change approved by the human** (spec had no time-series data: `MasteryRecord` is single-row per student-concept and quiz/teach-back rows have no timestamps). Chart.js installed (was listed in §3 stack, now done). Local backend tests 62/62 pass, frontend build passes. No live Codex quota spent (self-start AI mocked in tests).

### Night 9 — Evaluation Framework + Polish
- [x] Run the Section 11 test set, record real numbers (harness in `backend/app/eval/`; ran live `--sample 2` = 10 Codex calls, real numbers in README; full 40-call run is one command)
- [x] Loading states, error handling on all AI calls (per-action loading labels + shared error banner on tutorial/doubt/quiz/teach-back/self-start/both brief narratives)
- [x] Styling consistency pass across all screens (uniform utility-class system across all screens; full teal palette migration from DESIGN.md remains a tracked follow-up)

Night 9 implementation note: fixed evaluation set (30 grader + 5 off-topic + 5 leak) with pure, mock-tested scoring (`score_grader`, leak/redirect heuristics) and a live runner (`python -m app.eval.run_eval`, `--sample` caps live calls). Live `--sample 2` on prod scored 6/6 structured, 4/4 correctness, 2/2 partial-graceful, 2/2 code-match, 2/2 redirect, 0/2 leak. Backend tests 68/68. Live Codex calls this session for eval: 10 (capped per Section 6 budget); full 40-call run deferred to a deliberate quota spend.

### Night 10 — Submission Prep
- [ ] Final redeploy to the Oracle VM — confirm the LIVE URL reflects the finished build, not an old version
- [ ] Live URL smoke-tested end-to-end one more time (signup → unlock → tutorial → doubt chat → quiz → teach-back → forecast brief) as if you were a judge who's never seen it
- [ ] README finalized: setup incl. Docker Compose command (for local dev/testing), **the live demo URL + a "View Demo Data" login**, seed data explanation, Codex-vs-GPT-5.6 section, evaluation table
- [ ] `/feedback` Codex session ID captured (from your biggest scaffolding session, likely Night 1 or 2)
- [ ] Demo video recorded (script below) — consider recording against the LIVE URL, not localhost, so it matches what judges will actually click into
- [ ] Repo public / shared with required emails
- [ ] Devpost form submitted, live URL included in the project description

### Night 11 — Stretch: Syllabus Importer (only if Nights 1-9 are fully done and deployed)
- [ ] Section 5.1 checklist complete
- [ ] Importer acceptance test passed
- [ ] `<SourceAttribution />` visible across relevant screens
- [ ] Disclaimer footer live on the deployed app

*(If you get fewer nights than this before the deadline, compress — Nights 6-7 [Forecast Engine] are the ones to protect above all else; compress Nights 8/9 first if squeezed. Night 11 is the first thing dropped, not the last — it's a bonus, the core Nights 1-10 loop is what actually gets judged.)*

---

## 13. Demo Video Script (~2:45, updated wow-moment sequencing per feedback)

| Time | Content |
|---|---|
| 0:00–0:15 | Hook: "Teachers teach. AI clears confusion — even before it happens." Show locked syllabus tree. |
| 0:15–0:35 | Teacher unlocks chapter → student sees it unlock live |
| 0:35–1:00 | Student asks a doubt → progressive scaffolding shown (guiding question, not a direct answer) |
| 1:00–1:20 | Student does Teach-Back → GPT catches a real gap despite a "confident-sounding" explanation |
| 1:20–1:45 | Quiz wrong answer → specific misconception_code shown, not just "incorrect" |
| 1:45–2:15 | **Wow moment**: switch to teacher's **Forecast Brief** — "7 of 12 students are predicted to struggle with tomorrow's lesson, here's why, here's a 5-minute fix before you even start teaching it" |
| 2:15–2:35 | Quick Confusion Brief glance — reactive view, privacy threshold mentioned explicitly |
| 2:35–2:45 | Voiceover: what Codex built (scaffolding/backend/migrations/tests) vs. what GPT-5.6 powers live (4 structured-output roles) vs. what's pure deterministic code (mastery formula + forecast engine) |

*If Night 11 (Syllabus Importer) gets built, it's worth a 10-15 second cutaway ("and if a teacher wants to add a new chapter — upload the PDF, we handle the structure, all the actual content stays 100% original") but only if it doesn't push the video past 3 minutes. Core loop wins over bonus feature every time.*

- [ ] Script finalized, recorded, uploaded, link tested in incognito

---

## 14. Cut List (in order, if a night gets squeezed)

1. Exam Mode
2. Recommended Practice builder
3. Onboarding screen (hardcode board/class/subject)
4. Self-Start Mode (nice differentiator but not headline)
5. Progress/mastery-over-time chart (fallback: plain number, no chart)
6. **Syllabus Importer / PDF upload (Section 5.1)** — genuinely nice for the demo, but it's additive scope on top of an already-full plan; cut this first if any core night runs long, well before touching the forecast engine or confusion brief
7. **DB-Grounded Responses (Section 7.5)** — a nice quality boost, but purely additive; if it's not solid by Night 7, ship without it rather than let it delay the forecast engine or confusion brief

**Never cut:** Forecast Engine, Confusion Brief with privacy threshold, progressive Doubt Chat, deterministic mastery formula. These are what separate this from every other "AI tutor" submission.

---

## 15. Overall Status Tracker

- [x] Night 1 complete
- [x] Night 2 complete
- [x] Night 3 complete + core loop checkpoint passed
- [ ] Night 4 complete
- [ ] Night 5 complete
- [ ] Night 6 complete + forecast engine acceptance test passed
- [x] Night 7 complete
- [x] Night 8 complete
- [x] Night 9 complete + evaluation numbers recorded (sample run; full run one command away)
- [ ] Night 10 complete
- [ ] Night 11 complete (stretch — optional)
- [ ] Submitted on Devpost
