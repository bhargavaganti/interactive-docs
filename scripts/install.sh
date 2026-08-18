#!/usr/bin/env bash
# Install (or refresh) this skill for every agent CLI found on this machine.
#
#   ./scripts/install.sh            # install/update wherever a skills dir exists
#   ./scripts/install.sh --link     # symlink instead of copy (stays in sync while developing)
#   ./scripts/install.sh --list     # show what is installed where, and whether it is stale
#
# Claude Code and Codex use the same on-disk format — a folder containing SKILL.md with YAML
# frontmatter — so one payload serves both.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="$(basename "$SRC")"
TARGETS=("$HOME/.claude/skills" "$HOME/.codex/skills")
MODE="copy"; [[ "${1:-}" == "--link" ]] && MODE="link"

if [[ "${1:-}" == "--list" ]]; then
  for t in "${TARGETS[@]}"; do
    d="$t/$NAME"
    if [[ -L "$d" ]]; then echo "  $d -> $(readlink "$d")  [symlink]"
    elif [[ -d "$d" ]]; then
      if diff -rq "$SRC" "$d" --exclude=.git --exclude=__pycache__ >/dev/null 2>&1;
        then echo "  $d  [copy, up to date]"; else echo "  $d  [copy, STALE — re-run install]"; fi
    else echo "  $t  (not installed)"; fi
  done; exit 0
fi

for t in "${TARGETS[@]}"; do
  [[ -d "$t" ]] || { echo "skip $t (no such agent on this machine)"; continue; }
  d="$t/$NAME"
  rm -rf "$d"
  if [[ "$MODE" == "link" ]]; then ln -s "$SRC" "$d"; echo "linked  $d -> $SRC"
  else
    mkdir -p "$d"
    # everything except VCS/build cruft; assets/ is included so docs render offline
    (cd "$SRC" && tar cf - --exclude=.git --exclude=__pycache__ --exclude='*.pyc' .) | (cd "$d" && tar xf -)
    echo "installed $d"
  fi
done
[[ -f "$SRC/assets/mermaid.min.js" ]] || echo "! run scripts/vendor_mermaid.py so diagrams render offline"
