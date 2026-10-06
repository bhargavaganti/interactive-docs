# Discovery — reading any codebase before you write a word

Everything these docs claim has to come from the repo. This is the pass that gets you the facts.
Budget 10–20 minutes. Write findings straight into `arch.json` as you go.

**The rule that governs all of it:** an entry in `.env`, `docker-compose.yml` or `package.json` is
evidence something is *deployed*, never evidence it is *used*. Confirm every edge by finding the
call site. Anything you cannot confirm is `inferred` or `provisioned-unused` — never silently
promoted to fact.

---

## 1 · Classify the project

Run this first; it decides which profile in `project-types.md` you follow.

```bash
ls -a
cat README* 2>/dev/null | head -60
# manifests tell you the stack
ls package.json pyproject.toml requirements.txt go.mod Cargo.toml pom.xml build.gradle \
   Gemfile composer.json *.csproj Package.swift pubspec.yaml 2>/dev/null
# shape of the thing
ls docker-compose*.y*ml Dockerfile* Makefile Procfile 2>/dev/null
ls -d .github/workflows k8s helm charts terraform infra deploy 2>/dev/null
```

| You see | Profile |
|---|---|
| `[project.scripts]` / `bin` in package.json / `cobra`, `click`, `argparse`, `clap` | **CLI / TUI** |
| `Package.swift`, `*.xcodeproj`, `build.gradle` + `AndroidManifest.xml`, `pubspec.yaml` | **Mobile** |
| A web framework **and** a `web/`, `frontend/`, `client/` folder with a bundler | **Web app** |
| A web framework and **no** frontend folder | **Backend / API** |
| `dags/`, `dbt_project.yml`, `kedro`, `prefect`, `airflow`, `*.ipynb` + a training entrypoint | **Data / ML pipeline** |
| A single importable package, no entrypoint, docs full of code samples | **Library** (guide = API walkthrough) |

Ambiguous or a monorepo? Say so and pick the surface the *user* interacts with. Don't guess silently.

---

## 2 · Infrastructure inventory

```bash
# services, images, ports, depends_on, healthchecks, volumes
cat docker-compose*.y*ml
grep -rn "EXPOSE\|ENTRYPOINT\|CMD\|FROM " Dockerfile* 2>/dev/null
# every knob and what it defaults to — the config module is more honest than .env.example
cat .env.example 2>/dev/null
grep -rn "getenv\|os.environ\|process.env\|Settings(\|BaseSettings" --include=*.py --include=*.ts --include=*.js | head -40
# orchestration, if any
find . -name "*.yaml" -path "*k8s*" -o -name "values.yaml" -o -name "*.tf" | head
```

Capture per component: image + tag, published vs internal ports, `depends_on`, restart policy,
volumes, healthcheck, and the file:line you read it from. Deployed with no compose/k8s? Then infra
is the install path: package registry, binary targets, CI release job, runtime prerequisites.

**Schema creation — establish this before writing the seeding runbook, it changes every later step:**

```bash
grep -rn "create_all\|createAllTables\|synchronize: *true\|db.create_all" --include=*.py --include=*.ts
ls migrations/ alembic/versions/ db/migrate/ prisma/migrations/ 2>/dev/null
find . -iname "*backup*" -o -iname "*.dump" -o -iname "seed_*" -o -iname "*_seed.*" | head
```

- `create_all` present → schema is automatic; seeding only adds rows.
- Migrations only → they build *and* seed; apply in order.
- **A dump/restore, or migrations that are incremental patches with no table creation** → the
  schema *and* the first org/admin come from the dump. The app cannot bootstrap itself from empty.
  This is common and easy to miss; if there's no `create_all` and no CREATE TABLE in migration 1,
  it's this.

---

## 3 · Is there an AI surface at all?

One sweep. A hit here means you build `AI_WORKFLOWS.html`; zero hits across all rows means you
don't, and you say so rather than inventing one.

```bash
grep -rniE "anthropic|openai|langchain|langgraph|llamaindex|litellm|ollama|bedrock|vertexai|\
mistralai|cohere|huggingface|transformers|sentence.transformers|vllm|llama.cpp|\
crewai|autogen|dspy|semantic.kernel|haystack|instructor|guardrails|pydantic.ai|\
qdrant|pinecone|weaviate|chromadb|pgvector|milvus|faiss|lancedb|\
modelcontextprotocol|@anthropic-ai|ai-sdk|@langchain" \
 --include=*.py --include=*.ts --include=*.tsx --include=*.js --include=*.go --include=*.rs \
 --include=*.java --include=*.rb --include=requirements*.txt --include=pyproject.toml \
 --include=package.json -l | sort -u
```

Then find the actual call sites and read them:

```bash
grep -rnE "messages\.create|chat\.completions|\.invoke\(|\.generate\(|\.embed|embeddings\.create|\
generateText|streamText|\.run\(|\.stream\(" --include=*.py --include=*.ts | head -40
# prompts usually live apart from the code that sends them
find . -iname "*prompt*" -o -iname "*.j2" -o -iname "*.tmpl" | grep -v node_modules | head -20
```

For each call site record, into `ai.workflows[]`:

| Field | Where it comes from |
|---|---|
| model + provider | the client construction, not the docs |
| temperature, max tokens, output schema | the call's kwargs |
| what's in the prompt | read the template *and* the code that fills it |
| truncation / chunking budget | the slice, `[:N]`, splitter config — this is where fidelity is lost |
| retries, timeout, fallback model | the client wrapper / decorator |
| what happens when it fails | follow the except/catch — **does it fail open or closed?** |
| whether a human ever sees it | is the result gated, queued for review, or returned raw? |

**Fail-open guardrails are the single highest-value finding in this whole pass.** A validator that
returns "pass" when the model call times out means the protection silently disappears under exactly
the conditions where it matters. Look for it explicitly, and if it's there, put it in the diagram.

---

## 4 · Build the honesty ledger

For each AI/infra component, decide its status and record the evidence string:

| Status | Test |
|---|---|
| `wired` | you found the call site and traced it to a user-reachable path |
| `provisioned-unused` | it's in compose/deps but nothing imports or calls it |
| `inferred` | you believe the connection exists but couldn't confirm it in code |
| `planned` | referenced in TODO/docs/config, no implementation |

These become `ai.state_of_play[]` and the `unused` / `kind:"inferred"` flags on nodes and edges.
A doc that admits what it couldn't confirm is trusted; one that quietly guesses gets caught once
and then nothing in it is believed.

---

## 5 · Before you build

Confirm you can answer these. Any "no" is a gap to close or to state plainly in the doc:

- Which single command brings this up from nothing, and what breaks if you skip the restore?
- What is the one external dependency whose outage takes the product down?
- Where does user data physically go, and what leaves the machine?
- Which piece is deployed but does nothing?
- Where does the system lose fidelity (truncation, chunking, no OCR, no reranking)?
