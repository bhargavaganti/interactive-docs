#!/usr/bin/env bash
# Install (or refresh) this skill for every agent CLI found on this machine (macOS / Linux /
# Git Bash / WSL — on native Windows use install.ps1).
#
#   ./scripts/install.sh            # install/update for each agent that is present
#   ./scripts/install.sh --link     # symlink instead of copy (stays in sync while developing)
#   ./scripts/install.sh --list     # show what is installed where, and whether it is stale
#
# Claude Code and Codex use the same on-disk format — a folder containing SKILL.md with YAML
# frontmatter — so one payload serves both. An agent counts as present when its home dir exists;
# the skills dir under it is created if needed (a fresh install has none yet).
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="$(basename "$SRC")"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
#        agent        home dir         skills dir
AGENTS=("Claude Code|$HOME/.claude|$HOME/.claude/skills"
        "Codex|$CODEX_HOME|$HOME/.agents/skills")
# Codex still reads this older location; a copy left there shows up twice in its picker
LEGACY="$CODEX_HOME/skills/$NAME"
MODE="copy"; [[ "${1:-}" == "--link" ]] && MODE="link"

if [[ "${1:-}" == "--list" ]]; then
  for a in "${AGENTS[@]}" "Codex (legacy)|$CODEX_HOME|$CODEX_HOME/skills"; do
    IFS='|' read -r label _ t <<<"$a"; d="$t/$NAME"
    if [[ -L "$d" ]]; then echo "  $label: $d -> $(readlink "$d")  [symlink]"
    elif [[ -d "$d" ]]; then
      if diff -rq "$SRC" "$d" --exclude=.git --exclude=__pycache__ >/dev/null 2>&1;
        then echo "  $label: $d  [copy, up to date]"; else echo "  $label: $d  [copy, STALE — re-run install]"; fi
    else echo "  $label: not installed"; fi
  done; exit 0
fi

for a in "${AGENTS[@]}"; do
  IFS='|' read -r label home t <<<"$a"
  [[ -d "$home" ]] || { echo "skip $label (not installed on this machine)"; continue; }
  mkdir -p "$t"; d="$t/$NAME"
  rm -rf "$d"
  if [[ "$MODE" == "link" ]]; then ln -s "$SRC" "$d"; echo "linked    $label: $d -> $SRC"
  else
    mkdir -p "$d"
    # everything except VCS/build cruft; assets/ is included so docs render offline
    (cd "$SRC" && tar cf - --exclude=.git --exclude=__pycache__ --exclude='*.pyc' .) | (cd "$d" && tar xf -)
    echo "installed $label: $d"
  fi
done
if [[ -d "$CODEX_HOME" && ( -e "$LEGACY" || -L "$LEGACY" ) ]]; then
  rm -rf "$LEGACY"; echo "removed   old Codex copy: $LEGACY (now in ~/.agents/skills)"
fi
[[ -f "$SRC/assets/mermaid.min.js" ]] || echo "! run scripts/vendor_mermaid.py so diagrams render offline"
