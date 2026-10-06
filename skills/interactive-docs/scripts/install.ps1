# Install (or refresh) this skill for every agent CLI found on this machine — native Windows.
# (macOS / Linux / Git Bash / WSL: use install.sh.)
#
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1           # install/update
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Link     # junction instead of copy
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -List     # show what is installed where
#
# Same behaviour as install.sh: an agent counts as present when its home dir exists, and the
# skills dir under it is created if needed.
param([switch]$Link, [switch]$List)
$ErrorActionPreference = 'Stop'
$Src  = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Name = Split-Path $Src -Leaf
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$Agents = @(
  @{ Label = 'Claude Code'; Home = (Join-Path $HOME '.claude'); Dir = (Join-Path $HOME '.claude\skills') },
  @{ Label = 'Codex';       Home = $CodexHome;                  Dir = (Join-Path $HOME '.agents\skills') }
)
# Codex still reads this older location; a copy left there shows up twice in its picker
$Legacy = Join-Path $CodexHome "skills\$Name"
$Skip = @('.git', '__pycache__')

if ($List) {
  foreach ($a in $Agents + @(@{ Label = 'Codex (legacy)'; Dir = (Join-Path $CodexHome 'skills') })) {
    $d = Join-Path $a.Dir $Name
    if (Test-Path $d) {
      $item = Get-Item $d -Force
      if ($item.LinkType) { "  $($a.Label): $d -> $($item.Target)  [$($item.LinkType)]" }
      else { "  $($a.Label): $d  [copy]" }
    } else { "  $($a.Label): not installed" }
  }
  return
}

foreach ($a in $Agents) {
  if (-not (Test-Path $a.Home)) { "skip $($a.Label) (not installed on this machine)"; continue }
  New-Item -ItemType Directory -Force -Path $a.Dir | Out-Null
  $d = Join-Path $a.Dir $Name
  if (Test-Path $d) {
    $item = Get-Item $d -Force
    # remove a junction without following it into the source tree
    if ($item.LinkType) { $item.Delete() } else { Remove-Item $d -Recurse -Force }
  }
  if ($Link) {
    # a junction needs no admin rights or Developer Mode, unlike a symlink
    New-Item -ItemType Junction -Path $d -Target $Src | Out-Null
    "linked    $($a.Label): $d -> $Src"
  } else {
    New-Item -ItemType Directory -Path $d | Out-Null
    Get-ChildItem $Src -Force | Where-Object { $Skip -notcontains $_.Name } |
      Copy-Item -Destination $d -Recurse -Force
    Get-ChildItem $d -Recurse -Force -Include '__pycache__', '*.pyc' | Remove-Item -Recurse -Force
    "installed $($a.Label): $d"
  }
}
if ((Test-Path $CodexHome) -and (Test-Path $Legacy)) {
  $item = Get-Item $Legacy -Force
  if ($item.LinkType) { $item.Delete() } else { Remove-Item $Legacy -Recurse -Force }
  "removed   old Codex copy: $Legacy (now in ~/.agents/skills)"
}
if (-not (Test-Path (Join-Path $Src 'assets\mermaid.min.js'))) {
  '  (mermaid is fetched on first build; run scripts\vendor_mermaid.py to prefetch)'
}
