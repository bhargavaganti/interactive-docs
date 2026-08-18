# interactive-docs (agent skill)

Generate **single self-contained, theme-aware HTML docs** for any software project — web app, CLI,
mobile app, backend API, data/ML pipeline or library:

1. **Deployment / infrastructure doc** — clickable topology, data-flow diagram, request lifecycle,
   containers & images, data stores, external services, a from-zero **seeding runbook**, security,
   scaling and deploy steps.
2. **AI workflows doc** *(only when the project actually calls a model)* — mermaid diagrams of every
   model call, with the diagram kind chosen to match each workflow's real shape (agent loops with
   the loop edge drawn, RAG index **and** query paths, guardrail pass/fail/error branches), plus a
   prompt inventory, context & data path, failure modes and cost.
3. **Interactive user guide** — a left flow-tree of groups → steps, real evidence (screenshots,
   terminal transcripts, or request/response pairs), per-step "who does what", and rich explainers.

Every file inlines all CSS/JS and embeds images as base64, so it opens offline in any browser.
All three export to PDF and Word.

## Install

Works with **Claude Code** and **OpenAI Codex** — both load a skill from a folder containing a
`SKILL.md` with YAML frontmatter, so one copy serves both.

```bash
python3 scripts/vendor_mermaid.py    # once — caches mermaid so built docs render offline
./scripts/install.sh                 # installs into ~/.claude/skills and ~/.codex/skills
./scripts/install.sh --link          # symlink instead, if you're developing the skill
./scripts/install.sh --list          # show where it's installed and whether a copy went stale
```

Then invoke with `/interactive-docs`, or just ask for an interactive usage guide / architecture
diagram / AI pipeline diagram.

The instructions are agent-neutral — every step is a plain `python3`/shell command, with no
dependency on a particular harness's tools.

## Contents

| Path | What it is |
|---|---|
| `SKILL.md` | The skill instructions — discovery → project profile → the three docs. |
| `references/discovery.md` | How to read any codebase: classify it, inventory infra, detect the AI surface, build the honesty ledger. |
| `references/project-types.md` | What "guide" and "infra" mean for web / CLI / mobile / API / data-ML / library. |
| `references/ai-workflows.md` | AI doc content spec + which diagram kind fits which workflow shape. |
| `references/mermaid-recipes.md` | Theming, click wiring, sizing, and the mermaid gotchas. |
| `references/screenshot-capture.md` | The browser html2canvas recipe + every gotcha. |
| `references/capture-nonweb.md` | Terminal, simulator and request/response evidence capture. |
| `scripts/build_arch.py` | `arch.json` → the infrastructure doc **and** the AI workflows doc. |
| `scripts/vendor_mermaid.py` | Caches the mermaid bundle once so built docs stay offline. |
| `scripts/build_guide.py` | `guide.json` + evidence → the interactive guide (`--flat` for print/export). |
| `scripts/shot_server.py` | Local receiver that saves browser screenshots to files. |
| `scripts/export_doc.py` | Exports any of these docs to PDF and Word (.docx). |
| `examples/sample-arch.json` | A worked `arch.json` exercising every supported field — build it to see all three doc styles. |

## Quick start

```bash
python3 scripts/vendor_mermaid.py
python3 scripts/build_arch.py examples/sample-arch.json     # both infra + AI docs
python3 -m http.server                                      # open them in a real browser
```

## The quality bar (baked into SKILL.md)

Docs should show the *real* system doing the *real* thing:

- **Nothing is asserted that wasn't read in the repo.** An env var proves a thing is deployed, never
  that it's used — unconfirmed edges are marked `inferred`, and components nothing calls are marked
  `provisioned-unused` rather than quietly drawn as working.
- **Seeding is a real runbook.** Establish how the schema is created first (`create_all` /
  migrations / restore-from-dump); restore-based setups are common and easy to get wrong.
- **AI diagrams show the mechanism**, including where fidelity is lost (truncation, chunking, top-k
  with no score floor), the step that *doesn't* exist but readers assume does, and fail-open
  guardrails that vanish precisely when they're needed.
- **Guides use real evidence, never fabricated.** High-DPI captures from the running app, every flow
  end-to-end including other actors and public pages — or real terminal/API transcripts for projects
  with no GUI.
