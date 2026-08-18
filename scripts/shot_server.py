# -*- coding: utf-8 -*-
"""Tiny local receiver that saves POSTed screenshot bytes to files.

Run:   python3 shot_server.py [OUT_DIR] [PORT]     (defaults: ./screenshots 8899)

Then, from the app page in a browser you control, POST an image blob to
    http://127.0.0.1:<PORT>/save?name=<basename>
and it is written to OUT_DIR/<basename>.jpg. CORS is wide-open so the page can post
cross-origin. See references/screenshot-capture.md for the browser-side snippet.
"""
import http.server, urllib.parse, os, sys

OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath("screenshots")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8899
os.makedirs(OUT, exist_ok=True)

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
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
