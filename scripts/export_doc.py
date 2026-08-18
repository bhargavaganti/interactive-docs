# -*- coding: utf-8 -*-
"""Export a self-contained HTML doc to PDF and/or Word (.docx).

    python3 export_doc.py INPUT.html [--pdf out.pdf] [--docx out.docx] [--both]

Works on BOTH docs this skill produces:
  * Deployment architecture (static enough to export directly).
  * User guide — export the *flat* build (`build_guide.py --flat`), not the interactive
    single-page app, so every step is on the page for the printer/converter.

PDF  ← headless Chrome/Chromium `--print-to-pdf` (best fidelity: keeps the CSS).
      Falls back to `weasyprint` then `wkhtmltopdf` if no browser is found.
DOCX ← `pandoc` (embeds the base64 images). If pandoc is missing it prints install hints.

Every backend is optional; the script reports what it used and what to install if none
are available.
"""
import argparse, os, shutil, subprocess, sys, tempfile, atexit

_TEMPS = []


@atexit.register
def _cleanup():
    for p in _TEMPS:
        try:
            os.unlink(p)
        except OSError:
            pass


def _run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def find_chrome():
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
             "microsoft-edge", "brave-browser"]
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    for p in [  # common app paths
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]:
        if os.path.exists(p):
            return p
    return None


def to_pdf(html, out):
    src = "file://" + os.path.abspath(html)
    chrome = find_chrome()
    if chrome:
        r = _run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                  "--no-pdf-header-footer", f"--print-to-pdf={out}", src])
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return "chrome"
        r = _run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                  f"--print-to-pdf={out}", src])  # older flag form
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return "chrome(legacy)"
        sys.stderr.write((r.stdout or "")[-400:] + "\n")
    if shutil.which("weasyprint"):
        _run(["weasyprint", html, out])
        if os.path.exists(out):
            return "weasyprint"
    if shutil.which("wkhtmltopdf"):
        _run(["wkhtmltopdf", "--enable-local-file-access", html, out])
        if os.path.exists(out):
            return "wkhtmltopdf"
    return None


def snapshot(html):
    """Return a path to a static copy of `html` with JS-generated content baked in.

    The AI/infra docs draw their diagrams with mermaid at view time. pandoc does not run
    JavaScript, so converting the raw file to .docx silently drops every diagram while
    keeping the prose — the worst possible failure, because the output looks complete.
    Chrome's --dump-dom returns the DOM *after* scripts have run, with the SVGs inlined,
    which pandoc can then convert. Returns the original path if no snapshot is needed or
    no browser is available.
    """
    try:
        with open(html, encoding="utf-8", errors="replace") as f:
            head = f.read(400_000)
    except OSError:
        return html
    if 'class="mermaid"' not in head:
        return html                      # nothing JS-generated to bake
    chrome = find_chrome()
    if not chrome:
        sys.stderr.write("! diagrams are drawn by script and no browser was found to bake them;\n"
                         "  the .docx will contain the text but NOT the diagrams.\n")
        return html
    r = _run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
              "--virtual-time-budget=15000", "--dump-dom", "file://" + os.path.abspath(html)])
    dom = r.stdout or ""
    if "<svg" not in dom:
        sys.stderr.write("! could not bake the diagrams (none rendered); exporting without them.\n")
        return html
    # keep the scratch copy beside the source (relative asset paths must still resolve),
    # but clean it up afterwards so the user is left with only the deliverables
    fd, out = tempfile.mkstemp(suffix=".html", prefix=".snapshot-",
                               dir=os.path.dirname(os.path.abspath(html)) or ".")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(dom)
    _TEMPS.append(out)
    print("       (baked script-rendered diagrams in before converting)")
    return out


def to_docx(html, out):
    if not shutil.which("pandoc"):
        return None
    html = snapshot(html)
    r = _run(["pandoc", html, "-f", "html", "-t", "docx", "-o", out])
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return "pandoc"
    sys.stderr.write((r.stdout or "")[-400:] + "\n")
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--pdf")
    ap.add_argument("--docx")
    ap.add_argument("--both", action="store_true", help="write <name>.pdf and <name>.docx next to the input")
    a = ap.parse_args()
    base = os.path.splitext(a.html)[0]
    pdf = a.pdf or (base + ".pdf" if (a.both or not a.docx) else None)
    docx = a.docx or (base + ".docx" if (a.both or not a.pdf) else None)

    if pdf:
        used = to_pdf(a.html, pdf)
        print(f"PDF  : {'OK via ' + used + ' -> ' + pdf if used else 'FAILED — install Chrome/Chromium, or weasyprint / wkhtmltopdf'}")
    if docx:
        used = to_docx(a.html, docx)
        print(f"DOCX : {'OK via ' + used + ' -> ' + docx if used else 'FAILED — install pandoc (brew install pandoc / apt install pandoc)'}")
