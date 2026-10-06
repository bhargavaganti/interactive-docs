# -*- coding: utf-8 -*-
"""Build a self-contained, interactive, tree-navigated usage guide from a JSON spec.

Usage:
    python3 build_guide.py guide.json [--shots DIR] [--out FILE]

guide.json shape:
{
  "title": "MyApp — Interactive Usage Guide",
  "favicon": "📘",                      # optional (only used as browser-tab title hint)
  "groups": [
    {"id":"start","label":"Start","sub":"Shared","color":"#3f47c4"},
    {"id":"flow1","label":"Flow 1","sub":"...","color":"#0d7a72"}
  ],
  "pages": [
    {
      "id":"start-signin","group":"start","step":0,"icon":"◆",
      "title":"Sign in","crumb":"Start","who":"Any user",
      "imgs":["01-login"],                      # basenames (no ext) in the shots dir
      "caps":["The sign-in screen"],            # one caption per image (optional)

      # `evidence` generalises `imgs` for projects with no GUI to screenshot. Mix freely;
      # `imgs`/`caps` are folded into this list, in order, and keep working unchanged.
      "evidence":[
        {"kind":"image",    "src":"01-login", "cap":"The sign-in screen"},
        {"kind":"terminal", "title":"$ myapp init --name demo",
         "body":"✔ created demo/\n✔ wrote demo/config.toml", "cap":"Real output, not retyped"},
        {"kind":"code",     "title":"POST /api/ask → 200", "lang":"json",
         "body":"{\"answer\": \"…\", \"citations\": [1,4]}", "cap":"Actual response body"}
      ],
      "do":"What the user does …",              # HTML ok
      "see":"What the user sees …",             # HTML ok
      "note":"Optional callout HTML",           # optional
      "note_kind":"info|tip|warn",              # optional (default info)
      "spec":{"title":"…","desc":"…"},          # optional key/value 'brief' card
      "body":"<div>…rich HTML…</div>"           # optional free-form HTML block
    }
  ]
}

Notes
- step 0 hides the per-flow progress bar (use for non-sequential pages).
- Images are embedded as base64 data URIs so the output is one portable file.
- Each group gets its own accent COLOR (from the group's "color"), used for the pill,
  progress bar, active tree node, next button, and callouts — so readers always know
  which section they are in.
"""
import base64, os, re, json, argparse, html as _html

def normalize(pages):
    """Fold `imgs`/`caps` into a single ordered `ev` list so renderers handle one shape.

    A guide for a CLI, an API service or a data pipeline has no screenshots to take, but it
    still needs evidence that the thing really ran — a terminal transcript or a real
    request/response is that evidence. Treating all three uniformly keeps those projects
    first-class instead of bolting them on.
    """
    for p in pages:
        ev = []
        caps = p.get("caps") or []
        for i, im in enumerate(p.get("imgs") or []):
            ev.append({"kind": "image", "src": im,
                       "cap": caps[i] if i < len(caps) else None})
        for b in p.get("evidence") or []:
            b = dict(b)
            b.setdefault("kind", "image" if b.get("src") else "code")
            ev.append(b)
        p["ev"] = ev
    return pages


def used_images(pages):
    out = []
    for p in pages:
        for b in p.get("ev", []):
            if b.get("kind") == "image" and b.get("src") and b["src"] not in out:
                out.append(b["src"])
    return out


def dataimg(shots, name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = os.path.join(shots, name + ext)
        if os.path.exists(p):
            mime = "image/png" if ext == ".png" else ("image/webp" if ext == ".webp" else "image/jpeg")
            with open(p, "rb") as f:
                return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())
    return ""  # missing image -> empty (renders as broken but keeps build alive

def build(spec_path, shots, out):
    spec = json.load(open(spec_path))
    groups = spec["groups"]
    pages = normalize(spec["pages"])
    title = spec.get("title", "Interactive Guide")

    used = used_images(pages)
    IMG = {k: dataimg(shots, k) for k in used}
    missing = [k for k, v in IMG.items() if not v]
    if missing:
        print("WARNING missing images:", ", ".join(missing))

    DATA = {"groups": groups, "pages": pages}

    CSS = r"""
:root{
  --bg:#eaeef4; --panel:#ffffff; --ink:#161c2b; --muted:#586074; --line:#dbe1ea;
  --nav:#0f1626; --nav2:#172038; --nav-ink:#c8d0e2; --nav-muted:#727e99; --nav-line:#232e49;
  --accent:#3f47c4; --accent-soft:#e6e8fb; --gold:#b45309; --gold-soft:#f3e7d6;
  --tone:#3f47c4;
  --shadow:0 8px 24px rgba(24,32,56,.09); --shadow-sm:0 1px 4px rgba(24,32,56,.07);
  --font-display:"Palatino Linotype","Book Antiqua",Palatino,"Iowan Old Style",Georgia,serif;
  --font-body:"Segoe UI",system-ui,-apple-system,BlinkMacSystemFont,Roboto,"Helvetica Neue",Arial,sans-serif;
}
:root[data-theme="dark"]{
  --bg:#0d121d; --panel:#151c29; --ink:#e7ebf3; --muted:#96a1b6; --line:#242f40;
  --nav:#080c15; --nav2:#111a2c; --nav-ink:#c4cddf; --nav-muted:#68738c; --nav-line:#1c2740;
  --accent:#8b90f0; --accent-soft:#1b1f3a; --gold:#d8934a; --gold-soft:#33261a;
  --shadow:0 10px 30px rgba(0,0,0,.55); --shadow-sm:0 1px 6px rgba(0,0,0,.45);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0d121d; --panel:#151c29; --ink:#e7ebf3; --muted:#96a1b6; --line:#242f40;
  --nav:#080c15; --nav2:#111a2c; --nav-ink:#c4cddf; --nav-muted:#68738c; --nav-line:#1c2740;
  --accent:#8b90f0; --accent-soft:#1b1f3a; --gold:#d8934a; --gold-soft:#33261a;
  --shadow:0 10px 30px rgba(0,0,0,.55);
}}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:var(--font-body);font-size:16px;line-height:1.6}
.app{display:grid;grid-template-columns:312px 1fr;min-height:100vh}
.side{background:linear-gradient(180deg,var(--nav),var(--nav2));color:var(--nav-ink);
  border-right:1px solid var(--nav-line);position:sticky;top:0;height:100vh;overflow-y:auto;padding:22px 16px 40px}
.brand{display:flex;align-items:baseline;gap:8px;padding:4px 8px 16px}
.brand .logo{font-family:var(--font-display);font-size:22px;letter-spacing:.5px;color:#fff}
.brand .v{font-size:11px;color:var(--nav-muted);letter-spacing:.12em;text-transform:uppercase}
.side h2{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--nav-muted);margin:18px 10px 8px;font-weight:700}
.grp{margin-bottom:6px;border-radius:12px;overflow:hidden}
.grp-head{display:flex;align-items:center;gap:10px;padding:9px 10px;cursor:pointer;border-radius:10px;user-select:none;border-left:3px solid var(--tone,transparent)}
.grp-head:hover{background:rgba(255,255,255,.04)}
.grp-head .dot{width:9px;height:9px;border-radius:50%;background:var(--tone);flex:none;box-shadow:0 0 0 3px color-mix(in srgb,var(--tone) 25%,transparent)}
.grp-head .gl{font-weight:650;font-size:14px;color:#fff}
.grp-head .gs{display:block;font-size:11px;color:var(--nav-muted);font-weight:400;margin-top:1px}
.grp-head .chev{margin-left:auto;color:var(--nav-muted);transition:transform .2s;font-size:12px}
.grp.collapsed .chev{transform:rotate(-90deg)} .grp.collapsed .steps{display:none}
.steps{list-style:none;margin:2px 0 8px;padding:0 0 0 20px;position:relative}
.steps::before{content:"";position:absolute;left:16px;top:2px;bottom:12px;width:1px;background:var(--nav-line)}
.steps a{display:flex;align-items:center;gap:10px;padding:7px 10px;margin:2px 0;border-radius:9px;color:var(--nav-ink);text-decoration:none;font-size:13.5px}
.steps a .num{flex:none;width:22px;height:22px;border-radius:7px;display:grid;place-items:center;font-size:11.5px;font-weight:700;background:var(--nav-line);color:var(--nav-ink)}
.steps a:hover{background:rgba(255,255,255,.05)}
.steps a.active{background:color-mix(in srgb,var(--tone) 24%,transparent);color:#fff}
.steps a.active .num{background:var(--tone);color:#fff}
.steps a.done .num{background:transparent;border:1px solid var(--tone);color:var(--tone)}
.main{padding:34px clamp(20px,4vw,64px) 90px;max-width:1000px;margin:0 auto;width:100%}
.top{display:flex;align-items:center;gap:12px;margin-bottom:6px;flex-wrap:wrap}
.pill{font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:3px 10px;border-radius:20px;color:#fff;background:var(--tone)}
.who{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:650;color:var(--ink);background:color-mix(in srgb,var(--tone) 12%,var(--panel));border:1px solid color-mix(in srgb,var(--tone) 35%,transparent);padding:4px 11px;border-radius:20px}
.themeb{margin-left:auto;background:var(--panel);border:1px solid var(--line);color:var(--muted);border-radius:9px;padding:7px 11px;cursor:pointer;font:inherit;font-size:13px}
.prog{display:flex;gap:6px;margin:14px 0 22px}
.prog i{height:5px;border-radius:3px;flex:1;background:var(--line)} .prog i.on{background:var(--tone)}
h1.pt{font-family:var(--font-display);font-size:34px;line-height:1.15;letter-spacing:-.01em;margin:.1em 0}
.pane{opacity:0;transform:translateY(8px);transition:opacity .28s ease,transform .28s ease}
.pane.show{opacity:1;transform:none}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:8px 0 4px}
@media(max-width:760px){.cols{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow-sm)}
.card .lbl{font-size:11px;letter-spacing:.13em;text-transform:uppercase;font-weight:700;color:var(--tone);margin-bottom:6px}
.card p{margin:0;font-size:15px}
.note{margin:20px 0 0;padding:13px 16px;border-radius:10px;border:1px solid var(--line);border-left:3px solid var(--accent);background:var(--accent-soft);font-size:14.5px}
.note.tip{border-left-color:var(--tone);background:color-mix(in srgb,var(--tone) 10%,var(--panel))}
.note.warn{border-left-color:var(--gold);background:var(--gold-soft)}
.figs{display:flex;flex-direction:column;gap:14px;margin:20px 0}
figure{margin:0} figure img{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
/* Evidence blocks for projects with no GUI: a real terminal session, a real payload. */
.term,.codeblk{border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:var(--shadow)}
.term{background:#0d1220}
.term-h{display:flex;align-items:center;gap:6px;padding:8px 12px;background:#161d2e;border-bottom:1px solid #232c42}
.term-h i{width:10px;height:10px;border-radius:50%;background:#39405a;flex:none}
.term-h i:first-child{background:#ff5f57}.term-h i:nth-child(2){background:#febc2e}.term-h i:nth-child(3){background:#28c840}
.term-h span{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#8f9bb5;margin-left:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.term pre{margin:0;padding:14px 16px;font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.55;
  color:#d7deee;white-space:pre-wrap;word-break:break-word;overflow-x:auto}
.codeblk{background:var(--panel)}
.code-h{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 14px;background:color-mix(in srgb,var(--tone) 10%,var(--panel));
  border-bottom:1px solid var(--line);font-family:ui-monospace,Menlo,monospace;font-size:12px;font-weight:650;color:var(--tone)}
.code-h .lang{font-weight:400;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-size:10.5px}
.codeblk pre{margin:0;padding:13px 16px;font-family:ui-monospace,Menlo,monospace;font-size:13px;line-height:1.55;
  color:var(--ink);white-space:pre-wrap;word-break:break-word;overflow-x:auto}
figcap{display:block;font-size:12.5px;color:var(--muted);margin-top:8px;padding-left:2px;line-height:1.45}
figcap b{color:var(--ink)}
.spec{margin:18px 0 4px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--panel);box-shadow:var(--shadow-sm)}
.spec-h{background:color-mix(in srgb,var(--tone) 12%,var(--panel));padding:9px 16px;font-size:11px;letter-spacing:.13em;text-transform:uppercase;font-weight:700;color:var(--tone);border-bottom:1px solid var(--line)}
.spec-row{display:grid;grid-template-columns:104px 1fr;gap:12px;padding:11px 16px;border-top:1px solid var(--line)}
.spec-row:first-of-type{border-top:none}
.spec-k{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700;padding-top:2px}
.spec-v{font-size:14.5px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;background:color-mix(in srgb,var(--muted) 16%,transparent);padding:.1em .42em;border-radius:5px}
.nav{display:flex;justify-content:space-between;gap:12px;margin-top:34px;border-top:1px solid var(--line);padding-top:20px}
.nav button{font:inherit;font-size:14px;font-weight:600;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:11px;padding:11px 18px;cursor:pointer;display:flex;align-items:center;gap:9px;box-shadow:var(--shadow-sm)}
.nav button.next{background:var(--tone);color:#fff;border-color:transparent}
.nav button:disabled{opacity:.4;cursor:default} .nav .lab{display:flex;flex-direction:column;line-height:1.15} .nav .lab small{font-size:11px;opacity:.7;font-weight:500}
/* generic rich-body helpers usable from page.body */
.gb-h{font-family:var(--font-display);font-size:20px;margin:26px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--line)}
.gb-fx{margin:8px 0;font-family:ui-monospace,Menlo,monospace;font-size:14px;background:color-mix(in srgb,var(--tone) 8%,var(--panel));border:1px solid var(--line);border-left:3px solid var(--tone);border-radius:8px;padding:9px 13px;overflow-x:auto}
.gb-table{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0} .gb-table th,.gb-table td{border:1px solid var(--line);padding:8px 11px;text-align:left}
.gb-table th{background:color-mix(in srgb,var(--tone) 12%,var(--panel))}
"""

    JS = r"""
var groups=DATA.groups, pages=DATA.pages;
var order=pages.map(function(p){return p.id});
var colorOf={}; groups.forEach(function(g){colorOf[g.id]=g.color||'#3f47c4'});
var cur=order[0];
function esc(s){return String(s==null?'':s)}
function esch(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;')}
/* One evidence block: a real screenshot, a real terminal transcript, or a real
   request/response. Same slot in the layout, so a CLI or API guide reads like a GUI one. */
function evBlock(b,p){
  var cap=b.cap?'<figcap>'+b.cap+'</figcap>':'';
  if(b.kind==='terminal')
    return '<figure class="ev"><div class="term">'+(b.title?'<div class="term-h">'
      +'<i></i><i></i><i></i><span>'+esch(b.title)+'</span></div>':'')
      +'<pre>'+esch(b.body)+'</pre></div>'+cap+'</figure>';
  if(b.kind==='code')
    return '<figure class="ev"><div class="codeblk">'+(b.title?'<div class="code-h">'
      +esch(b.title)+(b.lang?'<span class="lang">'+esch(b.lang)+'</span>':'')+'</div>':'')
      +'<pre>'+esch(b.body)+'</pre></div>'+cap+'</figure>';
  return '<figure class="ev"><img src="'+(IMG[b.src]||'')+'" alt="'+esc(p.title)+'">'+cap+'</figure>';
}
function buildTree(){
  var nav=document.getElementById('tree');
  groups.forEach(function(g){
    var ps=pages.filter(function(p){return p.group===g.id});
    if(!ps.length) return;
    var grp=document.createElement('div'); grp.className='grp'; grp.id='grp-'+g.id; grp.style.setProperty('--tone',colorOf[g.id]);
    var head=document.createElement('div'); head.className='grp-head';
    head.innerHTML='<span class="dot"></span><span><span class="gl">'+esc(g.label)+'</span><span class="gs">'+esc(g.sub||'')+'</span></span><span class="chev">▾</span>';
    head.onclick=function(){grp.classList.toggle('collapsed')};
    var ul=document.createElement('ul'); ul.className='steps';
    ps.forEach(function(p){
      var li=document.createElement('li'); var a=document.createElement('a'); a.href='#'+p.id; a.id='nav-'+p.id;
      a.innerHTML='<span class="num">'+esc(p.icon||'•')+'</span><span>'+esc(p.title)+'</span>';
      a.onclick=function(e){e.preventDefault();show(p.id)}; li.appendChild(a); ul.appendChild(li);
    });
    grp.appendChild(head); grp.appendChild(ul); nav.appendChild(grp);
  });
}
function render(p){
  var tone=colorOf[p.group]; var m=document.getElementById('main'); m.style.setProperty('--tone',tone);
  var idx=order.indexOf(p.id);
  var gp=pages.filter(function(x){return x.group===p.group}); var gi=gp.map(function(x){return x.id}).indexOf(p.id);
  var prog = (p.step===0) ? '' : '<div class="prog">'+gp.map(function(x,i){return '<i class="'+(i<=gi?'on':'')+'"></i>'}).join('')+'</div>';
  var figs=(p.ev||[]).map(function(b){return evBlock(b,p)}).join('');
  var note=p.note?'<div class="note '+(p.note_kind||'info')+'">'+p.note+'</div>':'';
  var spec=p.spec?'<div class="spec"><div class="spec-h">'+esc(p.spec.label||'Details')+'</div>'+Object.keys(p.spec).filter(function(k){return k!=='label'}).map(function(k){return '<div class="spec-row"><span class="spec-k">'+esc(k)+'</span><span class="spec-v">'+p.spec[k]+'</span></div>'}).join('')+'</div>':'';
  var cols=(p.do||p.see)?'<div class="cols">'+(p.do?'<div class="card"><div class="lbl">What you do</div><p>'+p.do+'</p></div>':'')+(p.see?'<div class="card"><div class="lbl">What you see</div><p>'+p.see+'</p></div>':'')+'</div>':'';
  m.innerHTML='<div class="top"><span class="pill">'+esc(p.crumb||'')+'</span>'+(p.who?'<span class="who">👤 '+p.who+'</span>':'')+'<button class="themeb" onclick="toggleTheme()">◐ Theme</button></div>'+prog+
    '<div class="pane" id="pane"><h1 class="pt">'+esc(p.title)+'</h1>'+cols+spec+note+'<div class="figs">'+figs+'</div>'+(p.body||'')+
    '<div class="nav">'+(idx>0?'<button onclick="show(\''+order[idx-1]+'\')">←<span class="lab"><small>Previous</small>'+esc(pages[idx-1].title)+'</span></button>':'<span></span>')+
    (idx<order.length-1?'<button class="next" onclick="show(\''+order[idx+1]+'\')"><span class="lab" style="text-align:right"><small>Next</small>'+esc(pages[idx+1].title)+'</span>→</button>':'<span></span>')+'</div></div>';
  requestAnimationFrame(function(){document.getElementById('pane').classList.add('show')});
}
function show(id){
  cur=id; var p=pages.filter(function(x){return x.id===id})[0];
  document.querySelectorAll('.steps a').forEach(function(a){a.classList.remove('active','done')});
  var gp=pages.filter(function(x){return x.group===p.group}); var gi=gp.map(function(x){return x.id}).indexOf(id);
  gp.forEach(function(x,i){var a=document.getElementById('nav-'+x.id); if(a&&i<gi)a.classList.add('done')});
  var act=document.getElementById('nav-'+id); if(act)act.classList.add('active');
  var g=document.getElementById('grp-'+p.group); if(g)g.classList.remove('collapsed');
  render(p); window.scrollTo({top:0,behavior:'smooth'}); history.replaceState(null,'','#'+id);
}
function toggleTheme(){var r=document.documentElement;var c=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');r.setAttribute('data-theme',c==='dark'?'light':'dark');render(pages.filter(function(x){return x.id===cur})[0]);}
document.addEventListener('keydown',function(e){var i=order.indexOf(cur);if(e.key==='ArrowRight'&&i<order.length-1)show(order[i+1]);if(e.key==='ArrowLeft'&&i>0)show(order[i-1]);});
buildTree();
var start=(location.hash&&pages.filter(function(x){return '#'+x.id===location.hash}).length)?location.hash.slice(1):order[0];
show(start);
"""

    brand = _html.escape(title.split("—")[0].strip() or "Guide")
    HTML = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>" + _html.escape(title) + "</title><style>" + CSS + "</style></head><body>"
            "<div class='app'><aside class='side'><div class='brand'><span class='logo'>" + brand + "</span>"
            "<span class='v'>Guide</span></div><h2>Pick a step</h2><nav id='tree'></nav></aside>"
            "<main class='main' id='main'></main></div>"
            "<script>var IMG=" + json.dumps(IMG) + ";var DATA=" + json.dumps(DATA) + ";</script>"
            "<script>" + JS + "</script></body></html>")

    d = os.path.dirname(os.path.abspath(out))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out, "w") as f:
        f.write(HTML)
    print("wrote %s  %d KB · pages: %d · images: %d" % (out, os.path.getsize(out) // 1024, len(pages), len(used)))


def build_flat(spec_path, shots, out):
    """Emit a single linear, print-friendly HTML (all groups & steps stacked, no JS/tree).

    This is the export source: `chrome --headless --print-to-pdf` or `pandoc` (→ .docx) both
    want one document with everything visible, not a JS single-page app. See export_doc.py.
    """
    spec = json.load(open(spec_path))
    groups = spec["groups"]
    pages = normalize(spec["pages"])
    title = spec.get("title", "Guide")
    IMG = {k: dataimg(shots, k) for k in used_images(pages)}

    def cap(s):
        return _html.escape(str(s)) if s is not None else ""

    parts = []
    for g in groups:
        ps = [p for p in pages if p["group"] == g["id"]]
        if not ps:
            continue
        color = g.get("color", "#3f47c4")
        parts.append('<section class="grp" style="--tone:%s"><h2 class="gh">%s'
                     '<small>%s</small></h2>' % (color, cap(g["label"]), cap(g.get("sub", ""))))
        for p in ps:
            parts.append('<article class="pg" style="--tone:%s">' % color)
            parts.append('<div class="pmeta"><span class="pill">%s</span>%s</div>'
                         % (cap(p.get("crumb", "")),
                            ('<span class="who">👤 %s</span>' % p["who"]) if p.get("who") else ""))
            parts.append('<h3 class="ph">%s</h3>' % cap(p["title"]))
            if p.get("do") or p.get("see"):
                parts.append('<div class="cols">')
                if p.get("do"):
                    parts.append('<div class="card"><div class="lbl">What you do</div><p>%s</p></div>' % p["do"])
                if p.get("see"):
                    parts.append('<div class="card"><div class="lbl">What you see</div><p>%s</p></div>' % p["see"])
                parts.append('</div>')
            if p.get("spec"):
                sp = p["spec"]
                rows = "".join('<div class="spec-row"><span class="spec-k">%s</span><span class="spec-v">%s</span></div>'
                               % (cap(k), sp[k]) for k in sp if k != "label")
                parts.append('<div class="spec"><div class="spec-h">%s</div>%s</div>'
                             % (cap(sp.get("label", "Details")), rows))
            if p.get("note"):
                parts.append('<div class="note %s">%s</div>' % (p.get("note_kind", "info"), p["note"]))
            for b in p.get("ev", []):
                c = ('<figcaption>%s</figcaption>' % b["cap"]) if b.get("cap") else ""
                if b.get("kind") == "terminal":
                    parts.append('<figure class="ev"><div class="term">%s<pre>%s</pre></div>%s</figure>'
                                 % (('<div class="term-h">%s</div>' % cap(b["title"])) if b.get("title") else "",
                                    cap(b.get("body", "")), c))
                elif b.get("kind") == "code":
                    parts.append('<figure class="ev"><div class="codeblk">%s<pre>%s</pre></div>%s</figure>'
                                 % (('<div class="code-h">%s</div>' % cap(b["title"])) if b.get("title") else "",
                                    cap(b.get("body", "")), c))
                else:
                    parts.append('<figure><img src="%s">%s</figure>' % (IMG.get(b.get("src"), ""), c))
            if p.get("body"):
                parts.append('<div class="body">%s</div>' % p["body"])
            parts.append('</article>')
        parts.append('</section>')
    body = "\n".join(parts)

    CSS = """
    :root{--ink:#1a2233;--muted:#5b6474;--line:#d9dfe8;--tone:#3f47c4;--panel:#fff;--soft:#eef1f8}
    *{box-sizing:border-box}
    body{margin:0;color:var(--ink);background:#fff;font:15px/1.6 "Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif}
    .wrap{max-width:820px;margin:0 auto;padding:32px 26px 60px}
    h1.t{font:700 30px/1.15 Georgia,"Palatino Linotype",serif;letter-spacing:-.01em;margin:0 0 4px}
    .sub{color:var(--muted);margin:0 0 24px}
    .grp{margin-top:26px}
    .gh{font:600 21px/1.2 Georgia,serif;color:var(--tone);border-bottom:2px solid var(--line);padding-bottom:6px;margin:0 0 8px}
    .gh small{display:block;font:400 12px/1.4 "Segoe UI",sans-serif;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-top:3px}
    .pg{border:1px solid var(--line);border-left:3px solid var(--tone);border-radius:10px;padding:16px 18px;margin:14px 0;break-inside:avoid}
    .pmeta{display:flex;gap:10px;align-items:center;margin-bottom:6px}
    .pill{font:700 10px/1 inherit;letter-spacing:.05em;text-transform:uppercase;color:#fff;background:var(--tone);padding:4px 9px;border-radius:20px}
    .who{font:650 12px/1 inherit;color:var(--ink);background:var(--soft);border:1px solid var(--line);padding:4px 10px;border-radius:20px}
    .ph{font:650 19px/1.25 Georgia,serif;margin:2px 0 10px}
    .cols{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:6px 0}
    .card{border:1px solid var(--line);border-radius:9px;padding:11px 13px;background:var(--soft)}
    .lbl{font:700 10px/1 inherit;letter-spacing:.13em;text-transform:uppercase;color:var(--tone);margin-bottom:5px}
    .card p{margin:0;font-size:14px}
    .note{margin:12px 0;padding:10px 14px;border:1px solid var(--line);border-left:3px solid var(--tone);border-radius:8px;background:var(--soft);font-size:14px}
    .spec{border:1px solid var(--line);border-radius:9px;overflow:hidden;margin:12px 0}
    .spec-h{background:var(--soft);padding:7px 13px;font:700 10px/1 inherit;letter-spacing:.12em;text-transform:uppercase;color:var(--tone);border-bottom:1px solid var(--line)}
    .spec-row{display:grid;grid-template-columns:120px 1fr;gap:10px;padding:9px 13px;border-top:1px solid var(--line);font-size:14px}
    .spec-row:first-of-type{border-top:none}.spec-k{color:var(--muted);text-transform:uppercase;font-size:10px;letter-spacing:.1em;font-weight:700}
    figure{margin:14px 0;break-inside:avoid}
    figure img{width:100%;height:auto;border:1px solid var(--line);border-radius:8px}
    figcaption{font-size:12px;color:var(--muted);margin-top:6px}
    .term,.codeblk{border:1px solid var(--line);border-radius:8px;overflow:hidden}
    .term-h,.code-h{padding:6px 11px;background:var(--soft);border-bottom:1px solid var(--line);
      font-family:ui-monospace,Menlo,monospace;font-size:11.5px;font-weight:650;color:var(--tone)}
    .term pre,.codeblk pre{margin:0;padding:10px 13px;font-family:ui-monospace,Menlo,monospace;
      font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-word}
    .term pre{background:#0d1220;color:#d7deee}
    code{font-family:ui-monospace,Menlo,monospace;font-size:.86em;background:var(--soft);padding:.1em .4em;border-radius:4px}
    .gb-h{font:600 17px/1.2 Georgia,serif;margin:18px 0 8px;border-bottom:1px solid var(--line);padding-bottom:5px}
    .gb-fx{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:var(--soft);border-left:3px solid var(--tone);border-radius:7px;padding:8px 12px;margin:8px 0;overflow-x:auto}
    .gb-table,table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}
    .gb-table th,.gb-table td,th,td{border:1px solid var(--line);padding:7px 10px;text-align:left}
    .gb-table th,th{background:var(--soft)}
    @page{margin:16mm}
    @media print{.pg{break-inside:avoid}figure{break-inside:avoid}.gh{break-after:avoid}}
    """
    HTML = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<title>" + _html.escape(title) + "</title><style>" + CSS + "</style></head><body>"
            "<div class='wrap'><h1 class='t'>" + _html.escape(title) + "</h1>"
            "<p class='sub'>Printable / exportable edition</p>" + body + "</div></body></html>")
    d = os.path.dirname(os.path.abspath(out))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out, "w") as f:
        f.write(HTML)
    print("wrote %s  %d KB · flat (print/export) · pages: %d" % (out, os.path.getsize(out) // 1024, len(pages)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--shots", default="screenshots")
    ap.add_argument("--out", default="USER_GUIDE_INTERACTIVE.html")
    ap.add_argument("--flat", action="store_true",
                    help="emit a linear print/export-friendly HTML instead of the interactive app")
    a = ap.parse_args()
    (build_flat if a.flat else build)(a.spec, a.shots, a.out)
