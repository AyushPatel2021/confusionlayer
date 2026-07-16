# DESIGN.md — ConfusionLayer Design System

> **Status: v1 — global system decided (agent's call, per human delegation on 2026-07-15).**
>
> The human delegated the look-and-feel decision to the agent, so the palette, type
> scale, and spacing below are **decided** — this is the source of truth for AGENTS.md §8.
> They're chosen to feel calm and trustworthy for a teacher/education product,
> deliberately *not* the generic purple-SaaS / default-shadcn look. Anyone can still
> revise; if you change a token here, it changes everywhere by design.
>
> **Per-screen sections (bottom) are still stubs** — headers only. Per §8, a screen isn't
> built until its section here is filled in, so those remain to be specced per screen.
>
> **One dependency flag:** the webfonts named in §2 are a new dependency. Per AGENTS.md §1,
> *installing/wiring* them (`@fontsource`/CDN) is confirmed at build time before adding the
> package — the system-font fallbacks below hold until then, so no font is loaded prematurely.

---

## 0. Design intent

**Feeling:** calm, grounded, trustworthy — like a good textbook or a well-run classroom,
not a hype-y AI dashboard. Teachers are the gatekeepers; the product should read as a
serious pedagogical instrument they'd trust with their students.

**Explicitly avoid:**
- Default `indigo-500` / violet primary buttons (the "every AI app" look)
- Inter used flat for everything with no hierarchy
- Cookie-cutter equal card grids with drop shadows everywhere
- Neon gradients, glassmorphism, dark-mode-first "developer tool" vibes

**Lean into:** warm paper-like neutrals, a single confident calm-teal primary, a warm
clay accent used sparingly, generous whitespace, and clear typographic hierarchy over
decoration.

---

## 1. Color palette

Not framework defaults. Warm-neutral "paper & slate" base + calm teal primary + warm
clay accent. Semantic colors are muted, not fire-alarm bright.

### Neutrals — "Paper / Slate" (warm-tinted, not pure gray)
| Token | Hex | Use |
|---|---|---|
| `--paper` | `#FAF8F3` | App background (warm off-white, not `#fff`) |
| `--surface` | `#FFFFFF` | Cards / raised surfaces |
| `--surface-sunken` | `#F1EDE4` | Insets, code blocks, sunken panels |
| `--border` | `#E4DED2` | Hairline borders / dividers |
| `--ink-900` | `#1F2A2E` | Primary text (deep warm slate, not black) |
| `--ink-700` | `#3C4A4F` | Body text |
| `--ink-500` | `#6B7880` | Secondary / muted text |
| `--ink-300` | `#A6AFB4` | Disabled / placeholder |

### Primary — "Calm Teal" (trust, focus)
| Token | Hex | Use |
|---|---|---|
| `--primary-600` | `#0F6E6E` | Primary buttons, active nav, key actions |
| `--primary-500` | `#178A8A` | Hover / lighter primary |
| `--primary-100` | `#D6EAE9` | Primary-tinted backgrounds, selected rows |
| `--primary-050` | `#EBF4F3` | Subtle wash / focus ring bg |

### Accent — "Clay" (warmth, human touch — use sparingly)
| Token | Hex | Use |
|---|---|---|
| `--accent-600` | `#C1592E` | Highlights, teach-back / human moments, small CTAs |
| `--accent-100` | `#F6E3D8` | Accent-tinted backgrounds |

### Semantic (muted, education-appropriate)
| Token | Hex | Meaning |
|---|---|---|
| `--success` | `#2E7D5B` | Mastered / correct (calm green, not lime) |
| `--success-bg` | `#E2EFE8` | |
| `--warning` | `#B8862B` | Predicted confusion / at-risk (amber-gold) |
| `--warning-bg` | `#F6ECD6` | |
| `--danger` | `#B23A3A` | Errors / misconceptions (muted brick, not `#ef4444`) |
| `--danger-bg` | `#F3DEDE` | |
| `--info` | `#2F6690` | Neutral info / locked-but-available |
| `--info-bg` | `#DCE7F0` | |

### Mastery / forecast scale (sequential — for tree nodes, heatmaps, charts)
A single calm ramp so "mastered → confused" reads instantly and doesn't clash with the
brand. 5-step: `#E2EFE8` (mastered) → `#CDE3D6` → `#F6ECD6` → `#EBCBA6` →
`#E0A98A` (high predicted confusion). **Note:** these are *display* colors only — the
mastery/forecast *numbers* remain the deterministic formulas per AGENTS.md §7. The color
mapping never influences the computed score; it only visualizes it.

---

## 2. Typography

Not Inter-for-everything. A humanist serif for headings (warmth, authority, "textbook"
feel) paired with a clean humanist sans for UI/body, and a mono for code/quiz tokens.

| Role | Family | Fallback |
|---|---|---|
| Display / headings | **Fraunces** | `Georgia, serif` |
| UI / body | **Public Sans** | `system-ui, sans-serif` |
| Mono / code / tokens | **JetBrains Mono** | `ui-monospace, monospace` |

> **Dependency note:** these three are webfonts. Loading them (`@fontsource` package or a
> CDN link) is a new dependency, so that install is confirmed at build time per AGENTS.md §1.
> Until then the system-font fallbacks above render everything — the design does not break
> without the webfonts, it just looks less distinctive.

### Type scale (1.20 minor-third, base 16px)
| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `display` | 44 / 48 | 600 serif | Marketing / login hero only |
| `h1` | 33 / 40 | 600 serif | Screen title |
| `h2` | 27 / 34 | 600 serif | Section heading |
| `h3` | 22 / 30 | 600 serif | Card / subsection |
| `body-lg` | 19 / 30 | 400 sans | Tutorial prose, reading content |
| `body` | 16 / 26 | 400 sans | Default UI text |
| `body-sm` | 14 / 22 | 400 sans | Secondary / meta |
| `caption` | 12 / 16 | 500 sans | Labels, badges, timestamps |
| `mono` | 14 / 22 | 400 mono | Code, quiz answers, IDs |

Rules: one `h1` per screen; serif for headings only (never body); body max line length
~68ch for reading-heavy views (tutorial, doubt chat).

---

## 3. Spacing, radius, elevation

### Spacing — 4px base scale
`space-1`=4 · `space-2`=8 · `space-3`=12 · `space-4`=16 · `space-5`=24 · `space-6`=32 ·
`space-7`=48 · `space-8`=64

Defaults: card padding `space-5` (24), section gap `space-6` (32), inline gap `space-2/3`.
Favor generous whitespace over borders/shadows to separate content.

### Radius (soft, not pill-everything)
`radius-sm`=6 (inputs, badges) · `radius-md`=10 (cards, buttons) · `radius-lg`=16
(modals, major panels) · `radius-full` (avatars, status dots only).

### Elevation (restrained — max 2 levels; prefer border + subtle shadow)
- `flat`: no shadow, 1px `--border` — default for cards
- `raised`: `0 1px 2px rgba(31,42,46,.06), 0 2px 8px rgba(31,42,46,.05)` — popovers/menus
- `overlay`: `0 8px 30px rgba(31,42,46,.14)` — modals/dialogs only

### Layout
- Content max-width: `1120px` (dashboards), `720px` (reading views)
- Grid gutter: `space-5` (24). Avoid uniform equal-card grids — vary card size by importance.
- Focus ring: `2px solid --primary-500` + `2px` offset. Never remove focus outlines.

---

## 4. Component states (generic — apply to EVERY screen)

Per AGENTS.md §8, every screen ships **real** empty / loading / error states — never a
bare spinner or a "TODO" placeholder. Defaults below; override per screen as noted.

### Empty state
- Purposeful, not apologetic. Short heading (serif `h3`) + one line of `body` guidance +
  the single most useful action.
- Optional simple line illustration or a large muted glyph in `--ink-300`. No stock art.
- Copy is context-specific ("No students have hit this concept yet" — not "No data").
- Background `--paper`; centered within the content region, not the whole viewport.

### Loading state
- **Skeletons over spinners** for content-shaped areas (lists, cards, trees): `--surface-sunken`
  blocks at real dimensions, gentle shimmer, `radius-sm/md` to match final content.
- Spinner (`--primary-500`) only for short inline/button-level waits.
- Buttons: disabled + inline spinner + verb label ("Grading…", "Generating tutorial…").
- Never layout-shift when real content arrives — skeletons must match final geometry.
- AI-generation waits (tutorial/doubt/quiz/teach-back) get an honest "thinking" affordance
  with a plain-language line, since these can take seconds.

### Error state
- Muted `--danger` / `--danger-bg`, calm tone — never a red full-bleed scare.
- Say what happened + what to do next + a retry affordance. No raw stack traces to users.
- Distinguish: (a) recoverable (retry button), (b) empty-due-to-permission (locked chapter →
  explain the gate, don't show a scary error), (c) hard failure (support/next step).
- Inline field errors sit beneath the field in `body-sm --danger`; never rely on color alone
  (include an icon/text) for accessibility.

### Other shared components (stub — fill in as built)
- Buttons (primary / secondary / ghost / danger), inputs, badges/pills (mastery, priority),
  cards, nav/sidebar, modal/dialog, toast, tooltip, chart primitives, mastery-node styling.

---

## 5. Accessibility & motion

- Target WCAG AA contrast (≥4.5:1 body, ≥3:1 large). Verify teal/clay on paper before locking.
- Never encode meaning in color alone (mastery/forecast get label + icon + color).
- Full keyboard nav; visible focus everywhere; respect `prefers-reduced-motion` (skeleton
  shimmer + transitions off when set).
- Motion: 150–200ms ease for UI transitions; no bouncy/springy hype animations.

---

# Per-screen specs (STUBS — human to fill in)

> Headers only. Each screen must eventually document: layout/structure, key components,
> and its specific empty / loading / error states. Screen list + priorities mirror
> `PROJECT_SPEC.md` §10. **Do not build a screen whose section below is still empty —
> stop and ask (AGENTS.md §8).**

## Screen 1 — Signup / Login + "View Demo Data" fast-path  · Must
_TODO: layout, primary action hierarchy, demo fast-path treatment, empty/loading/error._

## Screen 2 — Student: Syllabus Tree (locked / unlocked / mastered)  · Must
_TODO: tree layout, node states + mastery color mapping, locked-gate treatment, states._

## Screen 3 — Teacher: Classroom chapter unlock control  · Must
_TODO: roster/chapter matrix, unlock toggle affordance, confirm patterns, states._

## Screen 4 — Concept Detail (Tutorial / Doubt Chat / Quiz / Teach-Back)  · Must
_TODO: tabbed vs sectioned layout, mode switching, shared concept header, states._

## Screen 5 — Tutorial view  · Must
_TODO: reading layout (720px), prose type, generation loading affordance, states._

## Screen 6 — Doubt Chat (progressive scaffolding)  · Must
_TODO: chat layout, scaffolding-level cues, thinking state, message error/retry._

## Screen 7 — Quiz screen w/ structured feedback  · Must
_TODO: question layout, structured feedback block, misconception tagging display, states._

## Screen 8 — Teach-Back screen (explain-back, GPT grades)  · Must — secondary differentiator
_TODO: input affordance (text/voice?), grading wait state, feedback presentation, states._

## Screen 9 — Teacher: Confusion Brief (reactive, aggregated)  · Must
Built Night 7. Reached via the **Teacher Insights** header tab (teacher/admin only).
- **Layout:** a `panel` header (eyebrow "Reactive · aggregated" + title + one-line explainer that states the privacy threshold), then one `tutorial-band` card per concept that has a surfaced misconception, sorted by affected-student count.
- **Per concept:** chapter label + concept title, an "N of M affected" `badge-muted`, and a list of misconception clusters — each showing the taxonomy `code`, student count + share %, and description.
- **Privacy:** only clusters shared by ≥ `privacy_threshold` (3) students appear; **no student names anywhere** (enforced server-side, verified in tests).
- **GPT narrative:** per concept, a "Generate teaching brief" button calls the narrative endpoint (numbers deterministic, prose GPT) and renders summary + suggested activity inline.
- **States:** loading → skeleton cards; empty → "no shared misconceptions yet, needs ≥3 students"; error → shared calm error banner.

## Screen 10 — Teacher: Forecast Brief (predictive, pre-lesson)  · Must — headline differentiator
Built Night 7. Same **Teacher Insights** tab, shown above the Confusion Brief.
- **Layout:** `panel` header (eyebrow "Predictive · pre-lesson" + a **Recompute** action) then one `tutorial-band` card per upcoming concept, sorted by at-risk count.
- **Per concept:** chapter + concept title, a risk `badge` (On track / Some risk / High risk), an "N of M predicted to struggle · avg difficulty %" line, a **CSS forecast bar** (`forecast-bar` / `forecast-bar-fill`) visualizing average difficulty, and a "Weak prerequisites driving this" list (prereq title, avg effective mastery %, student count).
- **Determinism note:** all numbers come from the forecast engine (Section 8); the bar and colors only *display* them (DESIGN.md §1 mastery ramp). GPT writes only the optional teaching-brief prose.
- **States:** loading → skeleton cards; empty → "no forecasts yet, press Recompute"; error → shared calm error banner.
- **Chart lib:** intentionally none — CSS bars only. Chart.js is deferred to the Progress screen (Screen 12).

## Screen 11 — Student: Self-start any topic (outside syllabus)  · Should
Built Night 8. Student-only **Self-Start** header tab.
- **Layout:** `panel` with eyebrow "Explore · outside the syllabus", a single topic input + generate button, then the generated tutorial rendered in the same two-column `tutorial-band` layout as the Concept tutorial (explanation + worked example).
- **Framing:** copy makes clear this is exploration outside the official syllabus and does not affect class progress. Reuses the Tutorial Generator contract (free-form topic, grounded to the student's board/class/subject for level only). No unlock required; rate-limited.
- **States:** loading → skeleton cards; empty → "enter any topic"; error → shared banner.

## Screen 12 — Student: My Progress / mastery-over-time chart  · Should
Built Night 8. Student-only **My Progress** header tab.
- **Layout:** three summary `metric` tiles (concept count, mastered count at ≥80%, current avg mastery), a **Chart.js line chart** of average mastery-over-time (teal `#0f766e`, y-axis 0–100%), then a per-concept list with current effective vs peak mastery shown on `forecast-bar` bars.
- **Data:** backed by the new `mastery_history` table (weekly snapshots); effective (decayed) mastery computed deterministically per Section 6. Chart.js was added as a dependency for this screen (approved).
- **States:** loading → tall skeleton; empty → "no mastery data yet"; error → shared banner.

## Screen 13 — Exam Mode  · Nice-to-have
_TODO: focused/distraction-reduced layout, timing affordance, states._

## Screen 14 — Teacher: Recommended Practice assign  · Nice-to-have
_TODO: recommendation list, assign flow, states._

## Screen 15 — Teacher: Syllabus Importer (PDF upload → extraction → review)  · Nice-to-have — stretch (§5.1)
_TODO: upload state, extraction progress/loading, review/edit table, states._
