# -*- coding: utf-8 -*-
"""Vendor the Mermaid UMD bundle into assets/ so the built docs stay fully offline.

    python3 vendor_mermaid.py            # download+cache if missing
    python3 vendor_mermaid.py --force    # re-download
    python3 vendor_mermaid.py --check    # exit 0 if cached, 1 if not (no network)

Why vendor at all: the docs this skill builds are single self-contained HTML files that
must open with no network. Mermaid therefore has to be *inlined*, which means we need a
local copy of the library. We fetch it once into `assets/mermaid.min.js` and reuse it for
every project forever after. The bundle is not shipped with the skill (minified code can't be
reviewed); instead an exact version is pinned and its SHA-256 checked, so every mirror must
serve byte-identical code. `build_arch.py` calls this automatically on first use.

If this can't run (no network, locked-down box), that is not fatal: `build_arch.py`
falls back to its own hand-built HTML/CSS node diagrams. See `--mermaid none`.
"""
import os, sys, argparse, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "assets"))
DEST = os.path.join(ASSETS, "mermaid.min.js")

# UMD build: defines window.mermaid, no module loader needed, works from file://
# To upgrade: change VERSION, download once, and paste the new file's `shasum -a 256` here.
VERSION = "11.16.1"
SHA256 = "18327bef70d96fb505fe7287d9f6a7362ebf07ff6576ddfaffb1a06f3e1a2954"
SOURCES = [
    "https://cdn.jsdelivr.net/npm/mermaid@%s/dist/mermaid.min.js" % VERSION,
    "https://unpkg.com/mermaid@%s/dist/mermaid.min.js" % VERSION,
]
MIN_BYTES = 400_000  # a real mermaid bundle is megabytes; anything small is an error page


def cached():
    return os.path.exists(DEST) and os.path.getsize(DEST) >= MIN_BYTES


def fetch(url):
    from urllib.request import urlopen, Request
    req = Request(url, headers={"User-Agent": "interactive-docs-skill/1.0"})
    with urlopen(req, timeout=60) as r:
        return r.read()


def fetch_pinned(dest, sha256, urls, label):
    """Download `dest` from the first mirror whose bytes match `sha256`. Returns dest or None.

    Shared by every third-party bundle this skill uses (mermaid here, html2canvas in
    shot_server.py): nothing minified is shipped, and nothing unverified is ever run.
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    last = None
    for url in urls:
        try:
            print("fetching %s …" % url)
            blob = fetch(url)
            digest = hashlib.sha256(blob).hexdigest()
            if digest != sha256:
                raise ValueError("sha256 mismatch (got %s…) — refusing to use it" % digest[:16])
            with open(dest, "wb") as f:
                f.write(blob)
            print("vendored %s -> %s  %d KB  (sha256 verified)" % (label, dest, len(blob) // 1024))
            return dest
        except Exception as e:  # try the next mirror
            last = e
            print("  ! %s" % e)
    print("\nCould not vendor %s: %s" % (label, last), file=sys.stderr)
    return None


def vendor(force=False):
    if cached() and not force:
        print("mermaid already vendored: %s (%d KB)" % (DEST, os.path.getsize(DEST) // 1024))
        return DEST
    if fetch_pinned(DEST, SHA256, SOURCES, "mermaid " + VERSION):
        return DEST
    print("Options:\n"
          "  • run build_arch.py with --mermaid none (hand-built HTML diagrams instead)\n"
          "  • download mermaid.min.js manually and drop it at %s" % DEST, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 0 if already cached, 1 if not")
    a = ap.parse_args()
    if a.check:
        ok = cached()
        print("cached" if ok else "not cached")
        sys.exit(0 if ok else 1)
    vendor(a.force)
