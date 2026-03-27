"""
proxy/server.py — Local HTTP proxy that forwards Jira API requests from the
dashboard browser to Jira Cloud with Basic Auth injected.

Usage:
    python3 proxy/server.py

The dashboard calls http://localhost:8080/jira/rest/api/3/...
This proxy strips the /jira prefix and forwards to JIRA_BASE_URL with
the Authorization header set from JIRA_EMAIL + JIRA_API_TOKEN in .env.

Run alongside the dashboard (open index.html in browser or use http.server).
"""

import base64
import http.server
import os
import urllib.error
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL    = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN= os.environ["JIRA_API_TOKEN"]
PORT          = int(os.getenv("PROXY_PORT", "8080"))

AUTH_HEADER = "Basic " + base64.b64encode(
    f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()
).decode()


class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  [{self.command}] {self.path}  →  {args[1] if len(args) > 1 else ''}")

    def _proxy(self):
        # Strip /jira prefix
        if not self.path.startswith("/jira"):
            self.send_error(404, "Path must start with /jira")
            return

        jira_path = self.path[len("/jira"):]
        target    = JIRA_BASE_URL + jira_path

        # Read request body (for POST/PUT)
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length) if length else None

        # Forward headers — inject auth, strip host
        fwd_headers = {
            "Authorization": AUTH_HEADER,
            "Accept":        "application/json",
            "Content-Type":  self.headers.get("Content-Type", "application/json"),
        }

        req = urllib.request.Request(
            target, data=body, headers=fwd_headers, method=self.command
        )

        try:
            with urllib.request.urlopen(req) as resp:
                content = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        except urllib.error.HTTPError as e:
            content = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    def do_GET(self):  self._proxy()
    def do_POST(self): self._proxy()
    def do_PUT(self):  self._proxy()

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()


if __name__ == "__main__":
    server = http.server.HTTPServer(("localhost", PORT), ProxyHandler)
    print(f"Jira proxy running at http://localhost:{PORT}/jira")
    print(f"Forwarding to: {JIRA_BASE_URL}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
