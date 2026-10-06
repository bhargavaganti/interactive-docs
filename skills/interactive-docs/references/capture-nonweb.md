# Capturing evidence when there is no web page

`references/screenshot-capture.md` covers browsers. This covers everything else. All of it feeds
the same `evidence` list in `guide.json`:

```json
"evidence": [
  {"kind":"image",    "src":"03-home", "cap":"Signed in as an admin"},
  {"kind":"terminal", "title":"$ myapp init --name demo", "body":"✔ created demo/\n…",
   "cap":"Real output"},
  {"kind":"code",     "title":"POST /api/ask → 200", "lang":"json", "body":"{…}",
   "cap":"Actual response"}
]
```

**The bar is the same as for screenshots: it must be real.** Paste what the terminal printed and
what the server returned. Do not retype, tidy, or invent output — a plausible-looking fake
transcript is the fastest way to make a guide untrustworthy, and it is always eventually noticed.

---

## CLI / TUI

Run the command and capture stdout **and** stderr, with colour disabled so escape codes don't end
up in the doc:

```bash
NO_COLOR=1 TERM=dumb myapp init --name demo > out.txt 2>&1; cat out.txt
```

- Put the command in `title` (with the `$`) and only the output in `body` — the builder draws the
  terminal chrome and prompt line.
- Trim long output to the informative part and mark the cut with `…` on its own line. Don't
  silently truncate mid-token.
- Redact real secrets, tokens, hostnames and usernames before pasting; replace with an obviously
  fake placeholder and mention that you did.
- **Capture at least one error path.** Wrong flag, missing config, absent service. The recovery
  message is often the most useful thing in a CLI guide.
- Full-screen TUIs don't transcribe well. Either capture a terminal window as an image
  (macOS: `screencapture -l$(osascript -e 'id of app "Terminal"') shot.png`) or record with
  `asciinema rec` and pull a representative frame.

## Mobile

If your agent has simulator tooling, use it to boot, launch and screenshot the app. Otherwise drive
the simulator directly — `xcrun simctl boot <device>` then
`xcrun simctl io booted screenshot screens/03-home.png` for iOS. For Android use `adb`:

```bash
adb exec-out screencap -p > screens/03-home.png
```

- Capture **permission dialogs and first-launch state**. They're the screens users actually get
  stuck on and the ones most often missing from documentation.
- Take shots at a consistent device size so the guide's images line up.
- Simulator screenshots are honest evidence; say in the caption that it's a simulator.
- Real-device screenshots from the user are fine — ask for the specific screens by name.

## Backend / API

The request/response pair *is* the screenshot. Capture it with the real service running:

```bash
curl -sS -X POST localhost:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"…"}' | tee resp.json | python3 -m json.tool
```

- Protected endpoints: ask the user to run the call themselves with their own test credentials
  and paste the response, rather than reading a token from the environment or config.

- One `code` block for the request, one for the response, `title` carrying method, path and status.
- Show real ids and timestamps from the actual call, but **redact tokens and personal data**.
- Include one error response per group — the status code and body shape under failure are what
  integrators need most and what docs most often omit.
- For streaming endpoints, capture a few real SSE frames and mark the elision.
- For webhooks/async, capture both halves: the immediate `202` and the eventual callback payload.

## Data / ML

- `terminal` blocks for run logs with **real row counts and real timings** at each stage.
- `code` blocks for a schema and 2–3 sample rows (synthetic values are acceptable here *if* the
  schema is real and you label the values as synthesised).
- Plots and dashboards: capture only if they exist and actually render. A blank chart is worse
  than no chart — prefer the numbers.

## Redaction

Applies to every kind above. Before a transcript or payload goes into a doc, strip API keys,
bearer tokens, cookies, passwords, connection strings, internal hostnames, and personal data.
Replace with a clearly fake placeholder (`sk-REDACTED`, `user@example.com`) rather than deleting,
so the shape of the value is still visible. Say in the caption that values were redacted.
