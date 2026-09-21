"""Server HTTP locale che espone lo stato di Jarvis Mini al cockpit.

Endpoint:
    GET  /state  ->  JSON con modalita' + telemetria + media + agent.
    POST /ask    ->  invia una battuta all'assistente e riceve la risposta.
                     Body JSON: {"text": "..."} -> {"reply": "...", "source": "..."}.

`/ask` e' il "ponte a testo" dell'assistente vocale: consente di pilotarlo
senza microfono (sviluppo/QEMU) e implementa il "premi per parlare / scrivi"
del cockpit. Quando c'e' l'hardware, il loop microfono usa lo STESSO percorso
(la VoiceSession), quindi il comportamento e' identico.

Serve lo snapshot piu' recente prodotto dal loop di servizio (telemetria +
proattivita'), passato tramite `state_getter`. Solo libreria standard; ascolta
su localhost (IPC locale col cockpit, non un servizio esposto in rete).
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8090

# Limite difensivo sul corpo di POST /ask (e' IPC locale, ma restiamo prudenti).
_MAX_ASK_BYTES = 4096


def _make_handler(state_getter, ask_handler=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send_json(self, code, obj):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            # Preflight CORS per il POST del cockpit (XMLHttpRequest).
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            if self.path.rstrip("/") != "/state":
                self.send_response(404)
                self.end_headers()
                return

            try:
                state = state_getter()
            except Exception:
                state = {}
            self._send_json(200, state)

        def do_POST(self):
            if self.path.rstrip("/") != "/ask":
                self.send_response(404)
                self.end_headers()
                return
            if ask_handler is None:
                self._send_json(503, {"error": "assistant unavailable"})
                return

            try:
                length = int(self.headers.get("Content-Length", 0))
            except (TypeError, ValueError):
                length = 0
            if length <= 0 or length > _MAX_ASK_BYTES:
                self._send_json(400, {"error": "bad request"})
                return

            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                text = (payload.get("text") or "").strip()
            except (ValueError, AttributeError):
                self._send_json(400, {"error": "invalid json"})
                return
            if not text:
                self._send_json(400, {"error": "empty text"})
                return

            try:
                result = ask_handler(text)
                source = getattr(getattr(result, "source", None), "value", "local_ai")
                self._send_json(200, {"reply": result.text,
                                      "success": result.success,
                                      "source": source})
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})

    return Handler


def run_state_server(state_getter, host: str = DEFAULT_HOST,
                     port: int = DEFAULT_PORT, ask_handler=None):
    """Avvia (bloccante) il server.

    `state_getter()` restituisce il dict di stato (GET /state).
    `ask_handler(text) -> Result` gestisce POST /ask (opzionale).
    """
    server = ThreadingHTTPServer((host, port), _make_handler(state_getter, ask_handler))
    server.serve_forever()
