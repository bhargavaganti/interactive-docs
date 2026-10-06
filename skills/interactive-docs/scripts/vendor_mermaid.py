# -*- coding: utf-8 -*-
"""Vendor the Mermaid UMD bundle into assets/ so the built docs stay fully offline.

    python3 vendor_mermaid.py            # download+cache if missing
    python3 vendor_mermaid.py --force    # re-download
    python3 vendor_mermaid.py --check    # exit 0 if cached, 1 if not (no network)

Why vendor at all: the docs this skill builds are single self-contained HTML files that
must open with no network. Mermaid therefore has to be *inlined*, which means we need a
local copy of the library. We fetch it once into `assets/mermaid.min.js` and reuse it for
every project forever after.

If this can't run (no network, locked-down box), that is not fatal: `build_arch.py`
falls back to its own hand-built HTML/CSS node diagrams. See `--mermaid none`.
"""
import os, sys, argparse, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, "..", "assets"))
DEST = os.path.join(ASSETS, "mermaid.min.js")

# UMD build: defines window.mermaid, no module loader needed, works from file://
SOURCES = [
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js",
    "https://unpkg.com/mermaid@11/dist/mermaid.min.js",
    "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js",
]
MIN_BYTES = 400_000  # a real mermaid bundle is megabytes; anything small is an error page


def cached():
    return os.path.exists(DEST) and os.path.getsize(DEST) >= MIN_BYTES


def fetch(url):
    from urllib.request import urlopen, Request
    req = Request(url, headers={"User-Agent": "interactive-docs-skill/1.0"})
    with urlopen(req, timeout=60) as r:
        return r.read()


def vendor(force=False):
    if cached() and not force:
        print("mermaid already vendored: %s (%d KB)" % (DEST, os.path.getsize(DEST) // 1024))
        return DEST
    os.makedirs(ASSETS, exist_ok=True)
    last = None
    for url in SOURCES:
        try:
            print("fetching %s …" % url)
            blob = fetch(url)
            if len(blob) < MIN_BYTES:
                raise ValueError("suspiciously small (%d bytes) — probably not the bundle" % len(blob))
            if b"mermaid" not in blob[:200_000]:
                raise ValueError("payload does not look like mermaid")
            with open(DEST, "wb") as f:
                f.write(blob)
            print("vendored %s  %d KB  sha256=%s"
                  % (DEST, len(blob) // 1024, hashlib.sha256(blob).hexdigest()[:16]))
            return DEST
        except Exception as e:  # try the next mirror
            last = e
            print("  ! %s" % e)
    print("\nCould not vendor mermaid: %s" % last, file=sys.stderr)
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
