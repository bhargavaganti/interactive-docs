# -*- coding: utf-8 -*-
"""Tiny local receiver that saves POSTed screenshot bytes to files.

Run:   python3 shot_server.py [OUT_DIR] [PORT]     (defaults: ./screenshots 8899)

Then, from the app page in a browser you control, POST an image blob to
    http://127.0.0.1:<PORT>/save?name=<basename>
and it is written to OUT_DIR/<basename>.jpg. CORS is wide-open so the page can post
cross-origin. See references/screenshot-capture.md for the browser-side snippet.

It also serves the capture library at http://127.0.0.1:<PORT>/html2canvas.js — a pinned,
sha256-checked copy fetched once into assets/ — so the page loads it with a plain <script>
tag instead of pulling code from a CDN at capture time.
"""
import http.server, urllib.parse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vendor_mermaid import fetch_pinned

H2C_VERSION = "1.4.1"
H2C_SHA256 = "e87e550794322e574a1fda0c1549a3c70dae5a93d9113417a429016838eab8cb"
H2C = os.path.abspath(os.path.join(HERE, "..", "assets", "html2canvas.min.js"))
H2C_SOURCES = [
    "https://cdn.jsdelivr.net/npm/html2canvas@%s/dist/html2canvas.min.js" % H2C_VERSION,
    "https://unpkg.com/html2canvas@%s/dist/html2canvas.min.js" % H2C_VERSION,
    "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/%s/html2canvas.min.js" % H2C_VERSION,
]

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath("screenshots")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8899
os.makedirs(OUT, exist_ok=True)
if not os.path.exists(H2C) and not fetch_pinned(H2C, H2C_SHA256, H2C_SOURCES,
                                                 "html2canvas " + H2C_VERSION):
    print("! html2canvas unavailable — drop a copy at %s, or capture with the browser's own\n"
          "  screenshot tool instead." % H2C, file=sys.stderr)

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        if urllib.parse.urlparse(self.path).path != "/html2canvas.js" or not os.path.exists(H2C):
            self.send_response(404); self._cors(); self.end_headers(); return
        with open(H2C, "rb") as f:
            body = f.read()
        self.send_response(200); self._cors()
        self.send_header("Content-Type", "application/javascript")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        q = urllib.parse.urlparse(self.path).query
        name = urllib.parse.parse_qs(q).get("name", ["shot"])[0]
        name = "".join(c for c in name if c.isalnum() or c in "-_")
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        with open(os.path.join(OUT, name + ".jpg"), "wb") as f:
            f.write(data)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a):
        pass

print("shot receiver on http://127.0.0.1:%d  ->  %s" % (PORT, OUT))
http.server.HTTPServer(("127.0.0.1", PORT), H).serve_forever()
