# GSOI Jarvis Mini

**Car Agent** locale e **offline-first** dell'ecosistema GSOI. Jarvis Mini è
l'agente che gira a bordo dell'automobile, sul Raspberry Pi 5, integrato in
**GSOI Automotive OS** come servizio systemd. Deve funzionare anche
completamente **offline**; quando il server GSOI è raggiungibile può inoltrare
le richieste complesse a `gsoi-jarvis` / `gsoi-llm`, ma resta sempre attivo e
non viene mai sostituito.

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

## Architettura (v0.1)

```
richiesta utente
└─ router
   ├─ comando semplice? (intent locale + tool)  → tool locale   (anche se online)
   └─ altrimenti:
      ├─ server GSOI raggiungibile? → inoltro a gsoi-jarvis/gsoi-llm  (stub)
      └─ altrimenti                 → AI locale di fallback           (stub)
```

Moduli (`src/jarvis_mini/`):

| Modulo          | Ruolo                                                            |
| --------------- | ---------------------------------------------------------------- |
| `intents/`      | riconoscimento intenti offline (parole chiave, niente LLM)       |
| `tools/`        | tool locali dell'auto (audio, media, navigazione, veicolo, BT)   |
| `connectivity/` | rilevamento Internet, salute server GSOI, gestore modalità       |
| `router/`       | instradamento richieste (locale / server / AI locale)            |
| `remote/`       | client verso `gsoi-jarvis` — **stub** nella v0.1                 |
| `ai/`           | AI locale di fallback — **stub** nella v0.1                      |
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

Modalità servizio (come farà systemd nell'OS):

```bash
jarvis-mini serve
```

### Variabili d'ambiente

| Variabile              | Default                 | Descrizione                          |
| ---------------------- | ----------------------- | ------------------------------------ |
| `GSOI_SERVER_URL`      | `http://localhost:8080` | endpoint del server GSOI             |
| `JARVIS_FORCE_OFFLINE` | `0`                     | `1` forza la modalità offline        |

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Roadmap (dal documento di progetto)

La v0.1 copre il **cuore offline**: intent engine, router, connectivity, tool
locali (mock) e CLI. Fasi successive, con interfacce già predisposte:

- STT / TTS / wake word offline (Fase 5)
- AI locale reale — modello quantizzato GGUF (Fase 6)
- audio, Bluetooth, GPS, OBD reali (Fasi 7–9)
- client reale verso `gsoi-jarvis` (Fase 11)
- ricetta Yocto `jarvis-mini_git.bb` in `meta-gsoi` per l'integrazione nell'OS
