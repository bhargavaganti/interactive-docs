# Project profiles — what the two docs mean for each kind of project

"User guide" and "infrastructure" mean different things depending on what the project *is*. Pick
the profile from `discovery.md` step 1 and follow its row. The deliverables and the quality bar
never change — only what counts as evidence and what fills the tiers.

---

## Web app *(the default)*

- **Guide evidence:** browser screenshots — `references/screenshot-capture.md`.
- **Tiers:** Client · Delivery · Application · Data & AI.
- **Walk:** sign-in → each role's home → every flow end-to-end → public/unauthenticated pages →
  admin/reports.

## CLI / TUI

- **Guide evidence:** `terminal` blocks with **real** captured output — `capture-nonweb.md`.
- **Tiers:** rename to **Invocation · Runtime · Local state · External** (there are no containers;
  drawing a fake 4-tier stack is a lie). Nodes: the binary, its runtime, config file locations,
  cache/state dirs, anything it shells out to.
- **"Infra" is the install & distribution path:** package registries, release CI, supported
  platforms/architectures, runtime prerequisites, where config and state live per-OS, upgrade path.
- **Walk:** install → `--help` → init/config → the main task → an error path → uninstall.
  A wrong-usage error message is one of the most useful screens in a CLI guide; include one.

## Mobile

- **Guide evidence:** simulator captures — `capture-nonweb.md`. Real device screenshots are fine
  if the user provides them.
- **Tiers:** Device · App · Backend · Data & AI.
- **Infra covers:** build pipeline and signing, min OS versions, backend services, push
  notifications, crash/analytics SDKs, store distribution and review constraints, offline storage.
- **Walk:** first launch and permission prompts (these are the highest-value screens — capture the
  actual dialogs), onboarding, main flows, offline behaviour, background refresh.

## Backend / API service

- **Guide evidence:** `code` blocks with **real** request/response pairs — `capture-nonweb.md`.
  The "screen" is the payload.
- **Tiers:** Client · Application · Data & AI (there is no delivery tier — don't invent one).
- **Guide structure:** auth first (how to get a token), then one group per resource or use case,
  each step = one endpoint with request, response, and the state change it caused.
  Show at least one **error** response per group with its status code and body shape.
- **Walk:** the full lifecycle of the main object — create → read → update → the async/webhook
  path → delete — plus rate limits, pagination and idempotency if they exist.

## Data / ML pipeline

- **Guide evidence:** `terminal` blocks for run output, `code` blocks for sample rows/schemas,
  images for any dashboard or notebook plot that actually exists.
- **Tiers:** Sources · Orchestration · Compute · Storage & serving.
- **Infra covers:** scheduler and trigger cadence, compute (where jobs actually run), object/table
  storage and formats, the artifact/model registry, lineage, backfill and replay procedure.
- **Guide = one run walked end to end:** ingest → validate → transform → train/score → publish,
  with real row counts and real timings at each stage. State what happens when a stage fails
  mid-run: does it resume, or restart from zero?
- **Reference page:** every metric and feature — what it is, exactly how it's computed, why it
  matters. Verify each formula against the code.

## Library / SDK

- **Guide evidence:** `code` blocks — the sample, then its **actual** output.
- **Tiers:** usually not a topology at all. Draw the module dependency graph instead, or skip the
  diagram and say why.
- **Infra doc becomes:** install, supported versions/platforms, dependency surface, build & release
  process, semver policy, breaking-change history.
- **Walk:** install → the 5-line example → each major capability → error handling → extension points.
  Every snippet must be one you actually ran.

---

## Choosing the tiers honestly

The 4-tier grid is a default, not a requirement. `tiers` in `arch.json` is a free list — rename,
drop to three, or extend to five to match reality. **A tier that exists only to fill the grid is
worse than an asymmetric diagram.** A CLI with no server has no Delivery tier; say so by not
drawing one.

## When there is no running app to capture

Ranked, best first:

1. Run it yourself — a dev/local env, a seeded fixture, a test harness.
2. Ask the user for screenshots or a recording, naming exactly which screens you need.
3. Ship the structure with the text complete and the evidence slots explicitly marked as missing,
   and list which captures are still needed.

Never fabricate a screenshot, a terminal transcript, or a response body. Invented evidence is the
one failure that makes the entire document worthless.
