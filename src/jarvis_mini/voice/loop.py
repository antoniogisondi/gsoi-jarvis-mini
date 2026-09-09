"""Loop di interazione vocale: wake word -> (chi sei?) -> STT -> agente -> TTS.

Con i mock e' una 'CLI vocale' (legge da stdin); con i modelli reali diventa
l'interazione a voce vera. Gli errori non fermano il loop.
"""

from .tts import make_tts
from .stt import make_stt
from .wakeword import make_wakeword


def run_voice_loop(agent, wakeword=None, stt=None, tts=None, speaker=None,
                   verify: bool = False) -> None:
    wakeword = wakeword or make_wakeword()
    stt = stt or make_stt()
    tts = tts or agent.tts

    print("Loop vocale attivo (di' la wake word, poi parla).")
    while True:
        try:
            if not wakeword.wait():
                continue

            # Verifica del parlante (opzionale): 'sei tu?'
            if verify and speaker is not None:
                who = speaker.identify("")  # reale: campione dal microfono
                if who is None:
                    tts.say("Non ti riconosco.")
                    continue

            text = stt.transcribe()
            if not text:
                continue
            if text.lower() in (":quit", "esci", "stop"):
                break

            result = agent.handle(text)
            print(f"[{result.source.value}] {result.text}")
            tts.say(result.text)
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as exc:
            print(f"[voce:errore] {exc}")
