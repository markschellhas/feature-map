from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional


def make_server(html: str, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    encoded = html.encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path not in ("/", "/index.html"):
                self.send_error(404, "Not Found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    return ThreadingHTTPServer((host, port), Handler)


def server_url(server: ThreadingHTTPServer) -> str:
    host, port = server.server_address
    return "http://{0}:{1}/".format(host, port)


def serve_until(server: ThreadingHTTPServer, timeout: Optional[float] = None) -> None:
    timer = None
    try:
        if timeout is not None and timeout > 0:
            timer = threading.Timer(timeout, server.shutdown)
            timer.daemon = True
            timer.start()
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if timer is not None:
            timer.cancel()
        server.shutdown()
        server.server_close()
