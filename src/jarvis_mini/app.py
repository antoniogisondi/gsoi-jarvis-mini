"""Punto d'ingresso a riga di comando di Jarvis Mini.

Due modalita':

  * `jarvis-mini cli`   -> sessione interattiva di test (default)
  * `jarvis-mini serve` -> processo di servizio, avviato da systemd nell'OS

La modalita' `serve` resta in foreground (Type=simple) e in futuro ospitera'
il loop wake word / STT / TTS. Nella v0.1 e' un processo idle che tiene vivo
il servizio.
"""

import argparse
import time

from .agent import JarvisMini


def _run_cli(agent: JarvisMini) -> None:
    print("GSOI Jarvis Mini — CLI di test.")
    print("Scrivi un comando; ':status' per lo stato, ':quit' per uscire.\n")

    while True:
        try:
            text = input("Tu > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text in (":quit", ":q", "exit"):
            break
        if text == ":status":
            print(f"Modalita': {agent.mode().value}\n")
            continue

        result = agent.handle(text)
        print(f"[{result.source.value}] {result.text}\n")


def _run_serve(agent: JarvisMini) -> None:
    # Espone lo stato al cockpit via HTTP locale (thread in background).
    import threading
    from .api.server import run_state_server, DEFAULT_HOST, DEFAULT_PORT

    api_thread = threading.Thread(
        target=run_state_server, args=(agent,), daemon=True
    )
    api_thread.start()

    # In futuro: qui parte anche il loop wake word / STT / TTS (Fase 5).
    print(f"GSOI Jarvis Mini pronto (servizio). Modalita': {agent.mode().value}")
    print(f"API stato: http://{DEFAULT_HOST}:{DEFAULT_PORT}/state")
    print("In attesa di comandi. Premi Ctrl+C per uscire.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nArresto Jarvis Mini.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis-mini",
        description="GSOI Jarvis Mini — Car Agent locale, offline-first.",
    )
    # I sottocomandi sono opzionali: senza argomenti si avvia la CLI.
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("cli", help="sessione interattiva di test")
    subparsers.add_parser("serve", help="avvia come servizio (systemd)")
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    agent = JarvisMini()

    if args.command == "serve":
        _run_serve(agent)
    else:
        _run_cli(agent)


if __name__ == "__main__":
    main()
