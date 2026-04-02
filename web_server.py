import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATS_PATH = ROOT / "stats.json"


class HangmanHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path == "/api/stats":
            self.handle_get_stats()
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/stats":
            self.handle_post_stats()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")

    def handle_get_stats(self):
        data = {}
        if STATS_PATH.exists():
            try:
                data = json.loads(STATS_PATH.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                data = {}

        payload = json.dumps(data).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_post_stats(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing request body")
            return

        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        if not isinstance(payload, dict):
            self.send_error(HTTPStatus.BAD_REQUEST, "JSON payload must be an object")
            return

        try:
            STATS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to persist stats")
            return

        response = json.dumps({"ok": True}).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def run_server(port=5500):
    server = ThreadingHTTPServer(("", port), HangmanHandler)
    print(f"Serving Hangman app at http://localhost:{port}/frontend/")
    print(f"Stats API available at http://localhost:{port}/api/stats")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
