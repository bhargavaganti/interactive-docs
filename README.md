# interactive-docs

An agent skill for **Claude Code** and **OpenAI Codex** that reads a codebase and generates
**single self-contained, theme-aware HTML docs** for any software project: web app, CLI, mobile app,
backend API, data/ML pipeline or library.

1. **Deployment / infrastructure doc**: clickable topology, data-flow diagram, request lifecycle,
   containers & images, data stores, external services, a from-zero **seeding runbook**, security,
   scaling and deploy steps.
2. **AI workflows doc** *(only when the project actually calls a model)*: mermaid diagrams of every
   model call, with the diagram kind chosen to match each workflow's real shape (agent loops with
   the loop edge drawn, RAG index **and** query paths, guardrail pass/fail/error branches), plus a
   prompt inventory, context & data path, failure modes and cost.
3. **Interactive user guide**: a left flow-tree of groups → steps, real evidence (screenshots,
   terminal transcripts, or request/response pairs), per-step "who does what", and rich explainers.

Every file inlines all CSS/JS and embeds images as base64, so it opens offline in any browser.
All three export to PDF and Word.

## Install

### Claude Code: as a plugin

```
/plugin marketplace add bhargavaganti/interactive-docs
/plugin install interactive-docs@bhargavaganti
```

Invoke it with `/interactive-docs:interactive-docs`, or just ask for an interactive usage guide,
architecture diagram or AI pipeline diagram and it triggers on its own.

### Codex: as a plugin

```bash
codex plugin marketplace add bhargavaganti/interactive-docs
codex plugin add interactive-docs@bhargavaganti
```

Or use the built-in installer from inside Codex:

```
$skill-installer https://github.com/bhargavaganti/interactive-docs/tree/main/skills/interactive-docs
```

Invoke it with `$interactive-docs` (or pick it from `/skills`), or just describe what you want.

### Either agent: from a clone

```bash
git clone https://github.com/bhargavaganti/interactive-docs
cd interactive-docs/skills/interactive-docs
./scripts/install.sh            # macOS / Linux / Git Bash / WSL
./scripts/install.sh --link     # symlink instead, while developing the skill
./scripts/install.sh --list     # where it is installed, and whether a copy is stale
```

```powershell
# native Windows
powershell -ExecutionPolicy Bypass -File scripts\install.ps1          # add -Link or -List as above
```

The installer puts the skill in `~/.claude/skills` (Claude Code) and `~/.agents/skills` (Codex)
for each agent whose home directory exists, creating the skills folder if needed. It also
removes an old copy from `~/.codex/skills`, which Codex still reads and would otherwise list twice.

## Requirements

| For | Needs | Platforms |
|---|---|---|
| Building the docs | Python 3.8+, standard library only | macOS · Linux · Windows |
| Viewing the docs | Any modern browser, offline | everywhere |
| PDF export | Chrome, Chromium, Edge or Brave (or `weasyprint` / `wkhtmltopdf`) | macOS · Linux · Windows |
| Word export | [`pandoc`](https://pandoc.org/installing.html) (plus a browser to bake diagrams in) | macOS · Linux · Windows |
| Screenshot evidence | A browser the agent can drive (for web apps) | n/a |

The mermaid bundle (`assets/mermaid.min.js`) is committed, so diagrams render offline straight
after cloning. `scripts/vendor_mermaid.py` re-downloads it only if you delete or want to update it.

## Usage

Normally the agent drives everything: it reads the repo, writes a spec (`arch.json` / `guide.json`),
captures evidence and runs the scripts. To run them by hand (paths are relative to
`skills/interactive-docs/`):

```bash
python3 scripts/build_arch.py examples/sample-arch.json            # infra + AI docs from one spec
python3 scripts/build_arch.py arch.json --doc infra                # just one of them
python3 scripts/build_guide.py guide.json --shots screenshots      # interactive user guide
python3 scripts/build_guide.py guide.json --shots screenshots --flat --out guide.flat.html
python3 scripts/export_doc.py ARCHITECTURE_INFRASTRUCTURE.html --both   # → .pdf + .docx
python3 scripts/export_doc.py guide.flat.html --both               # export the flat guide, not the app
```

`examples/sample-arch.json` exercises every supported field of the infra and AI docs. The user
guide has no bundled sample because it is built from real captures of a running app.

## Repository layout

```
.claude-plugin/          plugin.json + marketplace.json   (Claude Code)
.codex-plugin/           plugin.json                      (Codex)
.agents/plugins/         marketplace.json                 (Codex)
skills/interactive-docs/ the skill itself — the only part either agent loads
```

| Path (under `skills/interactive-docs/`) | What it is |
|---|---|
| `SKILL.md` | The skill instructions: discovery → project profile → the three docs. |
| `references/discovery.md` | How to read any codebase: classify it, inventory infra, detect the AI surface, build the honesty ledger. |
| `references/project-types.md` | What "guide" and "infra" mean for web / CLI / mobile / API / data-ML / library. |
| `references/ai-workflows.md` | AI doc content spec + which diagram kind fits which workflow shape. |
| `references/mermaid-recipes.md` | Theming, click wiring, sizing, and the mermaid gotchas. |
| `references/screenshot-capture.md` | The browser html2canvas recipe + every gotcha. |
| `references/capture-nonweb.md` | Terminal, simulator and request/response evidence capture. |
| `scripts/build_arch.py` | `arch.json` → the infrastructure doc **and** the AI workflows doc. |
| `scripts/build_guide.py` | `guide.json` + evidence → the interactive guide (`--flat` for print/export). |
| `scripts/export_doc.py` | Exports any of these docs to PDF and Word (.docx). |
| `scripts/shot_server.py` | Local receiver that saves browser screenshots to files. |
| `scripts/vendor_mermaid.py` | Re-downloads the mermaid bundle into `assets/`. |
| `scripts/install.sh` · `scripts/install.ps1` | Installers for Claude Code + Codex (bash / PowerShell). |
| `assets/mermaid.min.js` | The vendored mermaid bundle, inlined into built docs. |
| `examples/sample-arch.json` | A worked `arch.json` covering every supported field. |

## The quality bar (baked into SKILL.md)

Docs should show the *real* system doing the *real* thing:

- **Nothing is asserted that wasn't read in the repo.** An env var proves a thing is deployed, never
  that it's used. Unconfirmed edges are marked `inferred`, and components nothing calls are marked
  `provisioned-unused` rather than quietly drawn as working.
- **Seeding is a real runbook.** Establish how the schema is created first (`create_all` /
  migrations / restore-from-dump); restore-based setups are common and easy to get wrong.
- **AI diagrams show the mechanism**, including where fidelity is lost (truncation, chunking, top-k
  with no score floor), the step that *doesn't* exist but readers assume does, and fail-open
  guardrails that vanish precisely when they're needed.
- **Guides use real evidence, never fabricated.** High-DPI captures from the running app, every flow
  end-to-end including other actors and public pages, or real terminal/API transcripts for projects
  with no GUI.

## Publishing (maintainers)

- **Validate:** `claude plugin validate .` (checks both `.claude-plugin/` manifests).
- **Release:** bump `version` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
  and `.codex-plugin/plugin.json` together, then push. Users pick it up with
  `/plugin marketplace update` or `codex plugin marketplace upgrade`.
- **Anthropic directory:** submit at <https://claude.ai/directory/manage>
  ([docs](https://claude.com/docs/plugins/submit)).
- **OpenAI plugin directory:** upload a ZIP of the repo at <https://platform.openai.com/plugins>
  (requires a verified org; see the [plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines)).

## License

[MIT](LICENSE)
