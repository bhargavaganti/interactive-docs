# Mermaid in these docs — recipes and the gotchas that cost time

`build_arch.py` inlines the vendored Mermaid UMD bundle so the page works offline. You write
mermaid source into `arch.json`; the builder handles theming, click wiring and sizing.

```bash
python3 scripts/vendor_mermaid.py     # once per machine — caches assets/mermaid.min.js (~3.4 MB)
```

`--mermaid inline` (default, self-contained) · `link` (references `assets/mermaid.min.js`, small
files) · `none` (renders the source as a code block — used automatically if the bundle is missing).

---

## What the builder does for you

- **Theming.** Mermaid runs with `theme:'base'` and `themeVariables` read from the page's CSS
  custom properties, so diagrams follow the light/dark tokens. Toggling the theme re-renders every
  diagram. **Never hard-code a hex colour in a node** — it will be invisible in one of the themes.
- **Click → detail panel.** Node keys in a workflow's `nodes` map are matched against the diagram
  source and `click <id> call pick("<scope>","<key>")` is appended automatically. Add a node to
  `nodes` and it becomes clickable; no directive to write.
- **Sizing.** Mermaid measures labels itself and under-counts markup inside them, which draws nodes
  outside its computed viewBox and clips them. The builder refits every viewBox to the geometry
  that actually rendered, after render and after each theme change.
- **Rendering** uses `mermaid.render()` rather than `run()`. `run()` tracks which elements it has
  processed and throws when re-run, which would blank every diagram on the first theme toggle.

## Gotchas

- **Click callbacks only work on `flowchart` / `graph`.** `sequenceDiagram`, `stateDiagram` and ER
  diagrams have no click support — the builder skips them rather than emitting invalid syntax. Put
  the clickable detail in a flowchart and use the sequence diagram alongside it for the timeline.
- **Subgraphs plus `LR` produce tangled, crossing edges.** The infra flow diagram deliberately
  omits subgraphs — the tier grid above it already shows the grouping. Opt in with
  `"flow_subgraphs": true` only if you check the result.
- **Quotes and specials in labels.** Always quote labels — `A["text"]` — and use `#quot;` for a
  literal quote. `mlabel()` handles this for generated diagrams; do it by hand in author-written
  source. Parentheses and brackets inside a quoted label are fine.
- **`<br/>` for line breaks, `<small>` for the sub-line.** Both work; the viewBox refit compensates
  for the mis-measurement they cause.
- **Node ids must be `[A-Za-z0-9_]`.** Ids starting with a digit break the parser. `sid()` sanitizes
  generated ids; keep hand-written ones simple and short.
- **Don't use `end` as a node id** — it's a keyword and terminates a subgraph.
- **JSON escaping.** Mermaid source lives in a JSON string: newlines are `\n` and every `"` in a
  label is `\"`. Long diagrams are easier to get right if you write them as one line with `\n`
  separators and validate with `python3 -m json.tool arch.json` before building.

## Conventions used across these docs

Keep them consistent — readers learn them once and then read every diagram faster.

| Meaning | Syntax |
|---|---|
| Synchronous call | `A --> B` |
| Async / queued | `A ==> B` (thick) |
| Inferred, not confirmed in code | `A -.-> B` |
| Missing step a reader will assume exists | dashed node + `classDef gap stroke-dasharray:3 4,opacity:.55` |
| External / third-party | `external: true` on the node (dashed border) |
| Deployed but never called | `unused: true` on the node (dashed + faded) |

Shapes, via a node's `shape` field: `box` service · `actor` person/client · `db`/`store` datastore ·
`queue` broker · `model` an inference call · `decision` a branch · `ext` external · `doc` document.

## A worked pair

Loop with a real stop condition, and the timeline beside it:

```
flowchart LR
  Q(["Question"]) --> P["Plan<br/><small>agent/plan.py:22</small>"]
  P --> T{"Tool needed?"}
  T -->|yes| X["Call tool<br/><small>6 registered</small>"]
  X --> P
  T -->|no| A(["Answer"])
  P -.->|"max 8 turns → give up"| F(["partial answer"])
```

```
sequenceDiagram
  autonumber
  participant U as User
  participant A as Agent
  participant M as Model
  U->>A: question
  loop until no tool call (max 8)
    A->>M: messages + tool schemas
    M-->>A: tool_use
  end
  A-->>U: final answer
```

Validate any hand-written diagram before shipping: build the doc, open it, and confirm the SVG
rendered. A syntax error shows up as the source in a code block, which is the builder telling you
the diagram didn't parse.
