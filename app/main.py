"""Tiny demo web app for the homelab CI/CD pipeline.

Standard library only, so the image stays small and there is nothing to pin.
"""
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = os.environ.get("APP_VERSION", "dev")
COLOR = os.environ.get("APP_COLOR", "#2563eb")
PORT = int(os.environ.get("PORT", "8080"))


def render_page(version, hostname, color):
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>Homelab demo app</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
.card{{background:#1e293b;border-top:6px solid {color};padding:2rem 3rem;border-radius:12px}}
code{{color:{color}}}
</style></head>
<body><div class="card">
<h1>Hello from the homelab</h1>
<p>Version: <code>{version}</code></p>
<p>Served by pod: <code>{hostname}</code></p>
<p>Deployed automatically by GitHub Actions + Flux</p>
</div></body></html>
""".format(version=version, hostname=hostname, color=color)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send(200, render_page(VERSION, socket.gethostname(), COLOR),
                       "text/html; charset=utf-8")
        elif self.path == "/healthz":
            self._send(200, "ok", "text/plain")
        elif self.path == "/version":
            self._send(200, json.dumps({"version": VERSION}), "application/json")
        else:
            self._send(404, "not found", "text/plain")

    def log_message(self, fmt, *args):  # one line per request on stdout
        print("%s %s" % (self.address_string(), fmt % args), flush=True)


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print("demo-app %s listening on :%d" % (VERSION, PORT), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
