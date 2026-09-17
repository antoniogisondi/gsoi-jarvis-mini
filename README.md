# GSOI Jarvis Mini

**Car Agent** locale e **offline-first** dell'ecosistema GSOI. Jarvis Mini è
l'agente che gira a bordo dell'automobile, integrato in **GSOI Automotive OS**
come servizio systemd. Deve funzionare anche completamente **offline**.

Il **cervello** dell'agente gira **a bordo**: un LLM locale (Qwen3-4B-Instruct)
servito come processo separato su `localhost`, interrogato senza rete — nessun
round-trip di rete, latenza minima. **Non esiste un modello sul server**: l'auto
pensa da sola. La connettività Internet, quando c'è, serve solo alle funzioni
che la richiedono (traffico, meteo, OTA), non a elaborare le richieste.

> Jarvis Mini **è** il Car Agent: non esiste un progetto separato `car-agent`.

## Come si inserisce nell'OS

Jarvis Mini non è "uno script che si apre": nell'auto gira come **servizio
systemd**, avviato automaticamente al boot.

```
CODICE     questa repo  →  pacchetto Python + jarvis-mini.service
YOCTO      meta-gsoi/recipes-gsoi/jarvis-mini/  installa il pacchetto e il .service
           nell'immagine gsoi-automotive-image
RUNTIME    POWER ON → boot → splash → systemd avvia jarvis-mini.service → pronto
```

Per questo il pacchetto espone un eseguibile `jarvis-mini` con due modalità:
`serve` (processo di servizio, per systemd) e `cli` (test interattivo).

## Architettura

```
richiesta utente
└─ router
   ├─ comando semplice? (intent locale + tool)  → tool locale (deterministico)
   └─ altrimenti                                → cervello LOCALE (LLM su localhost)
```

La richiesta **non esce mai** dalla macchina: nessun modello sul server, nessun
round-trip di rete. I comandi semplici restano sempre **deterministici** e
locali: non è sicuro far passare "alza il volume" o un comando veicolo
attraverso un LLM. La connettività riguarda solo le funzioni online, non il
cervello.

Moduli (`src/jarvis_mini/`):

| Modulo          | Ruolo                                                            |
| --------------- | ---------------------------------------------------------------- |
| `intents/`      | riconoscimento intenti offline (parole chiave, niente LLM)       |
| `tools/`        | tool locali dell'auto (audio, media, navigazione, veicolo, BT)   |
| `connectivity/` | rilevamento Internet, modalità online/offline (per funzioni online) |
| `router/`       | instradamento richieste (tool locale / cervello locale)          |
| `ai/`           | cervello locale: `mock` + client LLM `local` (Qwen3-4B)          |
| `agent.py`      | assembla tutto dietro `handle(testo) -> Result`                  |
| `app.py`        | CLI / servizio                                                   |

I tool della v0.1 sono **mock**: non toccano hardware reale. Il tool veicolo è
**sola lettura** (nessun invio di frame CAN, per sicurezza).

## Installazione e uso (sviluppo)

Richiede Python 3.9+. La v0.1 non ha dipendenze esterne (solo stdlib).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Sessione interattiva di test:

```bash
jarvis-mini cli
# oppure senza installare:  PYTHONPATH=src python3 -m jarvis_mini cli
```

Esempio:

```
Tu > Alza il volume
[local_tool] Volume alzato al 60%.

Tu > Che temperatura ha il motore?
[local_tool] La temperatura del motore e' di 88 gradi.

Tu > :status
Modalita': offline
```

`Modalita'` indica solo lo **stato della rete** (`offline` = niente Internet,
`connected` = Internet disponibile per le funzioni online). Il cervello locale
funziona in entrambi i casi.

Modalità servizio (come farà systemd nell'OS):

```bash
jarvis-mini serve
```

### Variabili d'ambiente

| Variabile              | Default                      | Descrizione                                   |
| ---------------------- | ---------------------------- | --------------------------------------------- |
| `JARVIS_FORCE_OFFLINE` | `0`                          | `1` forza lo stato rete a offline (test)      |
| `JARVIS_AI`            | `mock`                       | cervello locale: `mock` o `local` (LLM)       |
| `JARVIS_MODEL_URL`     | `http://127.0.0.1:8091/v1`   | endpoint OpenAI-compatible del modello        |
| `JARVIS_MODEL_NAME`    | `qwen3-4b-instruct`          | nome del modello richiesto al server locale   |

### Cervello locale (LLM a bordo)

Di default (`JARVIS_AI=mock`) nessun modello gira: l'agente resta pienamente
funzionante (intent + tool) e sviluppabile **senza hardware**. Per attivare il
modello reale serve un server OpenAI-compatible in ascolto su
`JARVIS_MODEL_URL` (es. `llama.cpp` server, Ollama o TensorRT-LLM che serve
**Qwen3-4B-Instruct**), poi:

```bash
JARVIS_AI=local jarvis-mini serve
```

Il client usa **solo la libreria standard** (`urllib`): nessuna dipendenza
aggiuntiva. È **model-agnostic** — per usare un altro modello (es. Minerva)
basta servire un GGUF diverso, senza toccare il codice.

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Roadmap (dal documento di progetto)

La v0.1 copre il **cuore offline**: intent engine, router, connectivity, tool
locali (mock) e CLI. Fasi successive, con interfacce già predisposte:

- STT / TTS / wake word offline (Fase 5)
- ✅ cervello locale — client LLM `local` verso Qwen3-4B su localhost (Fase 6);
  resta da fine-tunare il modello (LoRA/QLoRA) e servirlo sul Jetson
- audio, Bluetooth, GPS, OBD reali (Fasi 7–9)
- funzioni online (traffico, meteo) e OTA quando c'è rete (Fase 11)
- ricetta Yocto `jarvis-mini_git.bb` in `meta-gsoi` per l'integrazione nell'OS
