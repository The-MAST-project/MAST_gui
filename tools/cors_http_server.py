"""
Small replacement for `python3 -m http.server` that adds CORS headers
and handles OPTIONS preflight requests.

Usage:
  python3 tools/cors_http_server.py 8008 --origins="*"
  python3 tools/cors_http_server.py 8008 --origins="http://localhost:3000,http://example.com"

Defaults:
  port: 8008
  origins: '*' (allow all)
"""
import argparse
import http.server
import socketserver
from http.server import SimpleHTTPRequestHandler
import sys
from urllib.parse import urlparse


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, allowed_origins="*", **kwargs):
        self._allowed_origins = [o.strip() for o in (allowed_origins or "").split(",") if o.strip()]
        super().__init__(*args, **kwargs)

    def _origin_allowed(self, origin):
        if not origin:
            return False
        if "*" in self._allowed_origins:
            return True
        # origin may include scheme+host+port, compare host+scheme exact
        return origin in self._allowed_origins

    def send_cors_headers(self):
        # Determine origin to echo or wildcard
        origin = self.headers.get("Origin")
        if "*" in self._allowed_origins:
            # print("Sending: Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Origin", "*")
        elif self._origin_allowed(origin):
            # print("Sending: Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Origin", origin)
        # Allow common CORS headers
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        # Echo back requested headers or allow common set
        req_headers = self.headers.get("Access-Control-Request-Headers")
        if req_headers:
            self.send_header("Access-Control-Allow-Headers", req_headers)
        else:
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        # Optional: allow credentials if you wish (disable with caution)
        # self.send_header("Access-Control-Allow-Credentials", "true")

    def end_headers(self):
        # Inject CORS headers for all responses
        try:
            self.send_cors_headers()
        except Exception:
            pass
        super().end_headers()

    def do_OPTIONS(self):
        # Respond to preflight requests
        self.send_response(200, "OK")
        self.send_cors_headers()
        # Short TTL for preflight caching; adjust as needed
        self.send_header("Access-Control-Max-Age", "3600")
        self.end_headers()


def run(port=8008, bind="0.0.0.0", directory=None, origins="*"):
    handler_class = lambda *args, **kwargs: CORSRequestHandler(*args, directory=directory, allowed_origins=origins, **kwargs)
    with socketserver.ThreadingTCPServer((bind, port), handler_class) as httpd:
        sa = httpd.socket.getsockname()
        print(f"Serving HTTP on {sa[0]} port {sa[1]} (directory: {directory or '.'}) -> CORS origins: {origins}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down")
            httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="Simple HTTP server with CORS support")
    parser.add_argument("port", nargs="?", type=int, default=8008, help="Port to serve on (default 8008)")
    parser.add_argument("--bind", default="0.0.0.0", help="Bind address (default 0.0.0.0)")
    parser.add_argument("--dir", dest="directory", default=None, help="Directory to serve (default: cwd)")
    parser.add_argument("--origins", default="*", help="Comma-separated list of allowed origins (default '*')")
    args = parser.parse_args()

    run(port=args.port, bind=args.bind, directory=args.directory, origins=args.origins)


if __name__ == "__main__":
    main()
