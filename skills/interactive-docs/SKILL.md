---
name: interactive-docs
description: >-
  Generate self-contained, interactive HTML documentation for ANY software project — web app, CLI,
  mobile app, backend API, data/ML pipeline or library: (1) a DEPLOYMENT / INFRASTRUCTURE doc with a
  clickable topology, data flow, containers, storage, seeding runbook, security and deploy steps;
  (2) an AI WORKFLOWS doc with mermaid diagrams of every model call — agent loops, RAG index/query
  paths, guardrails — plus prompt inventory, context & data path, failure modes and cost; and (3) an
  interactive USER GUIDE / usage walkthrough with a flow tree, real evidence (screenshots, terminal
  transcripts or request/response pairs) and per-step "who does what". Use when the user asks to
  build/produce an interactive usage guide, product tutorial, onboarding walkthrough, "how the app
  works" doc, an architecture or infrastructure diagram, an AI/LLM/RAG/agent pipeline diagram, a
  deployment/ops doc, or a client-facing explainer of a running system.
metadata:
  short-description: Interactive infra, AI-workflow and usage docs for any project
---

# Interactive project docs

Up to three **single self-contained HTML files** (inline CSS/JS, images base64-embedded),
**theme-aware**, openable offline in any browser. Each also exports to PDF and Word.

| # | Deliverable | Built when |
|---|---|---|
| 1 | `ARCHITECTURE_INFRASTRUCTURE.html` | always |
| 2 | `AI_WORKFLOWS.html` | only if the project actually calls a model |
| 3 | `USER_GUIDE_INTERACTIVE.html` | always |

Build in that order: 1 and 2 come from one code-reading pass and are cheap; 3 needs a *running*
app and is the expensive one. Match effort to the ask — if the user wants only one of them, build
only that. Confirm scope when unclear (which flows? all three docs?). **Verify each file renders
before claiming done.**

## Bundled

All paths below are relative to **this skill's folder** (the directory containing this
`SKILL.md`), not the project being documented — run the scripts by their full path, e.g.
`python3 <skill-dir>/scripts/build_arch.py arch.json`, from the project root.

| Path | What |
|---|---|
| `references/discovery.md` | **Start here.** How to read any codebase: classify it, inventory infra, detect the AI surface, build the honesty ledger. |
| `references/project-types.md` | What "guide" and "infra" mean for web / CLI / mobile / API / data-ML / library. |
| `references/ai-workflows.md` | The AI doc's content spec + which diagram kind fits which workflow shape. |
| `references/mermaid-recipes.md` | Theming, click wiring, sizing, and the mermaid gotchas. |
| `references/screenshot-capture.md` | The browser html2canvas recipe + every gotcha. |
| `references/capture-nonweb.md` | Terminal, simulator and request/response evidence capture. |
| `scripts/build_arch.py` | `arch.json` → the infra doc **and** the AI doc. |
| `scripts/vendor_mermaid.py` | Fetches the pinned, hash-checked mermaid bundle (automatic on first build). |
| `scripts/build_guide.py` | `guide.json` + evidence → the interactive guide (`--flat` = print edition). |
| `scripts/shot_server.py` · `scripts/export_doc.py` | Screenshot receiver · PDF/DOCX export. |
| `examples/sample-arch.json` | A worked `arch.json` using every supported field. |
| `scripts/install.sh` · `scripts/install.ps1` | Installs/refreshes this skill for every agent CLI found (Claude Code, Codex) — bash / Windows PowerShell. |

---

## Step 0 · Discovery (always first)

Follow `references/discovery.md`. It classifies the project, inventories the infrastructure,
detects whether there's an AI surface at all, and establishes **how the database schema is created**
— which changes the whole seeding section. Write findings straight into `arch.json`.

**The rule everything else rests on:** an entry in `.env`, compose or `package.json` proves
something is *deployed*, never that it is *used*. Confirm each edge at its call site. Anything
unconfirmed is marked `inferred` or `provisioned-unused` — never quietly promoted to fact.

```bash
python3 scripts/vendor_mermaid.py     # optional: build_arch.py fetches it on first use
```

---

## A · Infrastructure doc

1. Fill `arch.json` — `tiers`, `nodes`, `edges`, `lifecycle`, `containers`, `storage`, `external`,
   `seeding`, `security`, `scaling`, `deploy`. Every field optional; omitted sections don't render.
   `examples/sample-arch.json` shows all of them. Rename or drop tiers to match reality — see
   `project-types.md`. **A tier that exists only to fill the grid is worse than an asymmetric diagram.**
2. `python3 scripts/build_arch.py arch.json --doc infra`
3. Keep every claim tied to a `file:line`, mark external vs in-cluster, and flag anything
   provisioned-but-unused.

**Seeding is a real from-zero runbook, not a footnote.** Establish the schema mechanism first
(`create_all` / migrations / **restore from a dump** / none) — restore-based setups are common and
easy to miss, and getting this wrong makes every later step wrong. Then give copy-pasteable
commands in exact order, flag destructive ones, name what to back up, and say how tests get an
isolated database.

## B · AI workflows doc

Only when the project really calls a model. Full spec in `references/ai-workflows.md`; diagram
mechanics in `references/mermaid-recipes.md`.

1. Fill `arch.json`'s `ai` block: `workflows` (each with its diagrams and a clickable `nodes` map),
   `prompts`, `models`, `context`, `cost`, `state_of_play`.
2. `python3 scripts/build_arch.py arch.json --doc ai`

**Choose the diagram kind from the workflow's actual shape** — this is what makes the doc worth
having. Chain → `flowchart LR`. Agent → flowchart **with the loop edge and its real stop condition**
+ a `sequenceDiagram` of one turn. RAG → **two** diagrams (index path, query path). Multi-agent →
flowchart with the shared state node. Streaming/async → sequence across client/API/worker/model.
Guardrail → flowchart with pass, fail **and error** branches.

Then make sure these are in it, because they're what readers can't get quickly from the code:

- **Where fidelity is lost** — truncation budgets, chunk size/overlap, no OCR, top-k with no score
  floor, history dropped to fit. Give each its own node.
- **The step that doesn't exist** but a reader will assume does (reranker, retry, fallback model) —
  draw it dashed and label it. Naming the absent step beats a clean diagram implying completeness.
- **Fail-open guardrails.** A validator that returns "pass" when its own model call times out means
  the protection vanishes exactly when it's needed. Look for it deliberately; if present, diagram it.
- **What leaves the machine**, whether anything is redacted first (usually not — say so), and your
  *own* retention: an audit table storing every prompt and completion is often the bigger exposure.
- **Cost with the multiplier explicit** — a mandatory grading pass doubles spend per request.

## C · Interactive user guide

Structure: a left **tree** of groups → steps, and per step a crumb pill, a "👤 who" badge, progress
bar, What-you-do / What-you-see cards, evidence, optional callout, optional `spec` card, optional
free-form `body` HTML, Prev/Next + arrow keys + theme toggle.

1. **Plan the tree** — a shared "Start", then one group per flow/area, plus optional
   "Reference"/"Admin". Give each group a distinct accent `color`.
2. **Capture evidence** from the *running* project into `screenshots/`. Browser →
   `references/screenshot-capture.md`. CLI, mobile, API, data → `references/capture-nonweb.md`.
3. **Write `guide.json`** (shape below), then:
   `python3 scripts/build_guide.py guide.json --shots screenshots --out USER_GUIDE_INTERACTIVE.html`
4. **Verify** — it's JS-driven, so open it in a real browser or over `python3 -m http.server`;
   a script-blocking preview shows a blank page.

```json
{
  "title": "MyApp — Interactive Usage Guide",
  "groups": [{"id":"start","label":"Start","sub":"Shared by all flows","color":"#3f47c4"},
             {"id":"flowA","label":"Flow A","sub":"…","color":"#0d7a72"}],
  "pages": [
    {"id":"start-signin","group":"start","step":0,"icon":"◆","title":"Sign in","crumb":"Start",
     "who":"Any user","imgs":["01-login"],"caps":["The sign-in screen"],
     "do":"Enter email + password and <b>Sign in</b>.","see":"A role-based home.",
     "note":"Demo: <code>admin@…</code>","note_kind":"tip"},
    {"id":"flowA-1","group":"flowA","step":1,"icon":"1","title":"Create the thing","crumb":"Flow A",
     "who":"Admin","evidence":[
       {"kind":"image","src":"10-create","cap":"Admin creating it"},
       {"kind":"terminal","title":"$ myapp sync","body":"✔ 42 records","cap":"Real output"},
       {"kind":"code","title":"POST /api/things → 201","lang":"json","body":"{…}","cap":"Response"}],
     "do":"…","see":"…",
     "spec":{"label":"The inputs","Title":"…","Description":"…"},
     "body":"<h3 class='gb-h'>Formula</h3><div class='gb-fx'>score = Σ (x/max)×w</div>"}
  ]
}
```

`step:0` hides the progress bar (reference/non-sequential pages). `who` becomes the 👤 badge.
`evidence` supports `image` · `terminal` · `code`, so a CLI, API or pipeline guide is first-class
rather than screenshot-shaped; `imgs`/`caps` still work and are folded in first. `note_kind` ∈
`info|tip|warn`. `body` is raw HTML (`gb-h`, `gb-fx`, `gb-table` helpers).

### What makes these guides good
- **A shared "Start", then per-flow branches with the SAME step shape**, so differences stand out.
- **Show who acts.** Log in as each role, capture their scoped view, caption each image with the
  account. Never repurpose a screenshot that contradicts the step — capture the correct state.
- **Reuse one worked example / dataset** across flows so the numbers stay consistent.
- **Explain the math.** A Reference page with the real formulas (verified against code) and a
  worked example earns its place.

### Depth & fidelity bar — default to this, don't wait to be asked
- **Real captures from the running project, high-DPI, full-page.** Desktop viewport (**≥1024px**),
  `scale:2`. Never a viewport-cropped or low-res shot.
- **Walk EVERY flow end-to-end** — create → configure → generate → publish → *the other actor's
  view* → evaluate → finalize → the report. Include **public/unauthenticated** pages and each state
  of an object (draft→published→submitted→graded→finalized) as its own step.
- **Turn optional features ON and show them really working.** Enable flag-gated features in a dev
  env and capture the real output. For media the UI won't render, extract a real frame
  (`ffmpeg -ss 2 -i file.mp4 -frames:v 1 out.jpg`).
- **Cut complex dashboards into each section** (region capture via `html2canvas(document.body,
  {x,y,width,height,scale:2})`) and add a per-metric table: **what it is · how it's computed (exact
  formula) · why it matters** — verified against the stats module, not memory.
- **Show variants side by side** — reading levels, difficulty tiers, per-role views — same item in
  each variant, quoting the changed text.

---

## D · Export to PDF and Word

Offer both whenever you hand over a doc.

```bash
python3 scripts/export_doc.py ARCHITECTURE_INFRASTRUCTURE.html --both
python3 scripts/build_guide.py guide.json --shots screenshots --out guide.flat.html --flat
python3 scripts/export_doc.py guide.flat.html --both
```

**Always export the guide from its `--flat` build** — the interactive file shows one step at a
time, so a direct export captures a single page. PDF uses headless Chrome (falls back to
weasyprint, wkhtmltopdf); DOCX uses pandoc. Keep the interactive HTML as the primary deliverable.

## Shared principles

- **Self-contained & offline** — inline everything, base64 images, no fetches at view time
  (html2canvas and mermaid are used at *capture*/*build* time, never fetched by the shipped file).
- **Theme-aware** — light tokens on `:root`, dark under `prefers-color-scheme` and `[data-theme]`;
  always paint `body` from a token. Never hard-code a colour inside a diagram node.
- **Keep files lean** — recompress before building (`sips --resampleWidth 1440`) so a rich guide is
  ~5–8 MB. The AI doc carries ~3.4 MB of inlined mermaid; use `--mermaid link` if size matters more
  than being self-contained.
- **Accuracy over polish** — numbers, formulas, ports, models, evidence and "who does what" must
  match reality. Never fabricate a screenshot, a transcript or a response body.
- **Verify before claiming done** — open every file in a real browser; confirm diagrams rendered as
  SVG (mermaid source shown as a code block means it failed to parse) and that clicking a node
  fills the detail panel.
