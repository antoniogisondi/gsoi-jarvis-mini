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
        # Jarvis "parla" la risposta (TTS mock nella v0.1).
        agent.say(result.text)


def _run_serve(agent: JarvisMini) -> None:
    import threading
    from .api.server import run_state_server, DEFAULT_HOST, DEFAULT_PORT
    from .telemetry import snapshot
    from .proactive.engine import ProactiveEngine

    engine = ProactiveEngine()
    shared = {"latest": snapshot(agent.mode().value)}

    def tick_loop():
        active_ids = set()
        while True:
            snap = snapshot(agent.mode().value)
            suggestions = engine.evaluate(snap)

            sug_list = []
            new_ids = set()
            for s in suggestions:
                sug_list.append({"id": s.id, "text": s.text, "severity": s.severity})
                new_ids.add(s.id)
                # Pronuncia solo i suggerimenti NUOVI (una volta).
                if s.id not in active_ids:
                    agent.say(s.text)
            active_ids = new_ids

            snap["agent"] = {
                "listening": True,
                "message": sug_list[0]["text"] if sug_list else "Tutto tranquillo. Buona guida.",
                "suggestions": sug_list,
            }
            shared["latest"] = snap
            time.sleep(3)

    threading.Thread(target=tick_loop, daemon=True).start()

    threading.Thread(
        target=run_state_server,
        args=(lambda: shared["latest"],),
        daemon=True,
    ).start()

    # In futuro: qui parte anche il loop wake word / STT (Fase 5).
    print(f"GSOI Jarvis Mini pronto (servizio). Modalita': {agent.mode().value}")
    print(f"API stato: http://{DEFAULT_HOST}:{DEFAULT_PORT}/state")
    print("Motore proattivo attivo. Premi Ctrl+C per uscire.")
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
