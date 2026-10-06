# The AI workflows doc — content spec

Built by `build_arch.py` from the `ai` block of `arch.json`. Build it **only when the project
actually calls a model.** If it doesn't, set `ai.present: false` and say so in the infra doc —
an AI doc for a system with no AI is noise.

The job of this document is to answer four questions a reader cannot get from the code quickly:
**where does this system call a model, what exactly goes into that call, what happens when it
fails, and what does it cost?**

---

## Pick the diagram kind from the workflow's actual shape

This is the rule that makes these diagrams worth having. One generic box-chart per workflow is
what every other tool produces and it teaches nothing. Match the diagram to the mechanism:

| Shape | `kind` | Diagram(s) to draw |
|---|---|---|
| Fixed sequence of model calls | `chain` | `flowchart LR` of the stages |
| Model picks tools and iterates | `agent` | `flowchart` **with the loop edge drawn** + a `sequenceDiagram` of one real turn |
| Retrieval-augmented | `rag` | **Two** diagrams: the index path (once per doc) and the query path (once per question) |
| Several agents over shared state | `multi-agent` | `flowchart` with the shared state store as a node every agent touches |
| Streamed or queued to a worker | `streaming` | `sequenceDiagram` across client / API / worker / model |
| A check that gates another output | `guardrail` | `flowchart TD` with the pass **and** fail branches, and the error branch |
| Single-shot classify/extract | `classify` | One small `flowchart LR`; don't inflate it |

Two rules that do most of the work:

- **Draw the loop.** An agent diagram without the iteration edge is a chain diagram, and it
  misrepresents the system. Label the edge with the actual stop condition (max turns, no tool call,
  a done signal) read from the code.
- **RAG gets two diagrams, always.** Indexing and querying run at different times, on different
  triggers, with different failure modes. One combined diagram hides that the query path can't fix
  a bad chunking decision made hours earlier.

## Mark what is lossy

Every AI pipeline throws information away somewhere, and that is what readers most need to see.
Give these their own node, and say so in the node's detail:

- truncation to a character/token budget
- chunk size and overlap (and whether boundaries are semantic or arbitrary)
- text extraction that drops tables, columns or images; no OCR fallback
- top-k with no score floor (weak matches still come back and still get answered)
- history dropped to fit the window

Use a dashed node (`classDef gap stroke-dasharray:3 4,opacity:.55`) for a step that **doesn't
exist but a reader will assume does** — an OCR fallback, a reranker, a retry. Naming the absent
step is more useful than leaving a clean diagram that implies completeness.

---

## Sections

**01 · AI surface map.** Every place a model is called, one diagram, clickable. Reading it should
answer "how many model calls does one user action cost?" Omit `ai.surface` and the builder derives
a hub-and-spoke map from your workflows; author it explicitly when the real shape differs.

**02 · Workflows in detail.** One block per workflow: purpose, trigger (with `file:line`), the
diagram(s), a clickable node map, the I/O contract, and what happens when it fails. Every node in
`nodes` gets `kv` facts with the file it lives in — a diagram whose boxes can't be traced back to
code is decoration.

**03 · Prompt inventory.** Table: name, file, purpose, variables injected, budget/truncation
behaviour, model. Prompts are the least reviewed and most load-bearing text in these systems, and
they're usually invisible in a repo tour. If a prompt is built by string concatenation across
several files, say so — that is itself the finding.

**04 · Context & data path.** What fills the window (the `composition` bar), and then the part
teams actually need in writing:
- **what leaves the machine** — which fields, to which provider, over which network hop
- **whether anything is redacted** before it goes (usually: no — say it plainly)
- **retention** — the provider's, *and* your own. An `ai_calls`/audit table storing every prompt
  and completion is frequently the larger exposure and is almost never mentioned. Check for it.
- whether the window is actually the constraint, or whether a retrieval cap is doing the limiting

**05 · Cost.** Real arithmetic: tokens in + out per call, times calls per user action. Make the
multiplier explicit — a mandatory grading pass doubles cost per question, and that belongs in one
sentence a reader can act on.

**06 · State of play.** `wired` / `provisioned-unused` / `inferred` / `planned` with evidence for
each. This is where the reranker nobody calls, and the fallback model that doesn't exist, get said
out loud.

---

## Accuracy bar

- Every model name, temperature, token cap and threshold is **read from the code**, never assumed
  from a provider's defaults.
- Every workflow node cites the file it lives in.
- If you cannot determine something (real p95 latency, actual spend), mark it `inferred` or leave
  it out. A confidently wrong latency number destroys trust in every other number on the page.
- Describe what the code does **now**. Suggested upgrades go in one clearly-labelled place, never
  mixed into the description of current behaviour.
