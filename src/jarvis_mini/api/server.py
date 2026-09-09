"""Server HTTP locale che espone lo stato di Jarvis Mini al cockpit.

Endpoint:
    GET /state  ->  JSON con modalita' + telemetria veicolo + media.

Solo libreria standard (offline-first, nessuna dipendenza). Ascolta su
localhost: e' un canale IPC tra Jarvis Mini e il cockpit sullo stesso
dispositivo, non un servizio esposto in rete.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .. import telemetry

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090


def _make_handler(mode_getter):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # silenzioso

        def do_GET(self):
            if self.path.rstrip("/") != "/state":
                self.send_response(404)
                self.end_headers()
                return

            try:
                mode = mode_getter()
            except Exception:
                mode = "offline"

            body = json.dumps(telemetry.snapshot(mode)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def run_state_server(agent, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Avvia (bloccante) il server di stato. `agent` espone .mode()."""

    def mode_getter():
        return agent.mode().value

    server = ThreadingHTTPServer((host, port), _make_handler(mode_getter))
    server.serve_forever()
