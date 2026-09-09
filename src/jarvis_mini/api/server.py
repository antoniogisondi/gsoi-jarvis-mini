"""Server HTTP locale che espone lo stato di Jarvis Mini al cockpit.

Endpoint:
    GET /state  ->  JSON con modalita' + telemetria + media + agent.

Serve lo snapshot piu' recente prodotto dal loop di servizio (telemetria +
proattivita'), passato tramite `state_getter`. Solo libreria standard; ascolta
su localhost (IPC locale col cockpit, non un servizio esposto in rete).
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090


def _make_handler(state_getter):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.rstrip("/") != "/state":
                self.send_response(404)
                self.end_headers()
                return

            try:
                state = state_getter()
            except Exception:
                state = {}

            body = json.dumps(state).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def run_state_server(state_getter, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Avvia (bloccante) il server. `state_getter()` restituisce il dict di stato."""
    server = ThreadingHTTPServer((host, port), _make_handler(state_getter))
    server.serve_forever()
