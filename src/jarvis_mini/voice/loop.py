"""Loop di interazione vocale: wake word -> (chi sei?) -> STT -> agente -> TTS.

Con i mock e' una 'CLI vocale' (legge da stdin); con i modelli reali diventa
l'interazione a voce vera. Gli errori non fermano il loop.

L'elaborazione (cervello + voce) passa sempre dalla VoiceSession condivisa,
cosi' il dialogo dal microfono e quello via `POST /ask` alimentano lo stesso
stato vivo mostrato dal cockpit.
"""

from .session import VoiceSession, STATE_IDLE, STATE_LISTENING
from .stt import make_stt
from .wakeword import make_wakeword


def run_voice_loop(agent, wakeword=None, stt=None, tts=None, speaker=None,
                   verify: bool = False, session: VoiceSession = None) -> None:
    wakeword = wakeword or make_wakeword()
    stt = stt or make_stt()
    # La sessione e' il punto d'ingresso unico; se non fornita se ne crea una.
    session = session or VoiceSession(agent)

    print("Loop vocale attivo (di' la wake word, poi parla).")
    while True:
        try:
            session.set_state(STATE_IDLE)
            if not wakeword.wait():
                continue

            session.set_state(STATE_LISTENING)

            # Verifica del parlante (opzionale): 'sei tu?'
            if verify and speaker is not None:
                who = speaker.identify("")  # reale: campione dal microfono
                if who is None:
                    session.set_state(STATE_IDLE)
                    agent.say("Non ti riconosco.")
                    continue

            text = stt.transcribe()
            if not text:
                continue
            if text.lower() in (":quit", "esci", "stop"):
                break

            # La sessione pensa, pubblica lo stato e pronuncia la risposta.
            result = session.ask(text)
            print(f"[{result.source.value}] {result.text}")
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as exc:
            print(f"[voce:errore] {exc}")
