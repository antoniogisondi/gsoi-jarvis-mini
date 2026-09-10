# GSOI — Fine-tuning (QLoRA di Qwen3-4B con Unsloth)

Pipeline per adattare **Qwen3-4B-Instruct** alle esigenze di GSOI (persona,
comandi automotive in italiano, rifiuti di sicurezza) e produrre un **`.gguf`**
da servire in auto come cervello locale di `jarvis-mini`.

> Si **addestra** fuori dall'auto (Colab o workstation con GPU NVIDIA). In auto
> si fa solo **inferenza** sul `.gguf`. Il Jetson non addestra.

```
data/gsoi_dataset.jsonl  →  train.py (QLoRA, Unsloth)  →  gguf/*.gguf  →  gsoi-model (auto)
        (dati)                (guidato da config.yaml)      (deploy)
```

## Cosa modifichi tu

Un solo file: **`config.yaml`**. Contiene *tutti* i parametri (modello, LoRA,
training, export) già con default sensati per QLoRA 4-bit. E il **dataset**
in `data/gsoi_dataset.jsonl`, che espandi con i tuoi esempi.

### Formato del dataset

Una riga JSON per esempio, con una lista `messages` (senza `system`: lo
inietta lo script dal `config.yaml`, così resta allineato al prompt dell'auto):

```json
{"messages": [{"role": "user", "content": "Chi sei?"}, {"role": "assistant", "content": "Sono GSOI..."}]}
```

Copri almeno tre famiglie di esempi:
1. **persona / comandi** in italiano, risposte brevi;
2. **dati di bordo** → non inventare numeri, rimanda ai sensori/tool;
3. **sicurezza** → rifiuta azioni su freni/sterzo/ABS/airbag/centralina (sola lettura).

## Requisiti

- **Python 3.10–3.12** (consigliato 3.11). Su 3.13/3.14 `datasets`/`dill` non
  serializzano ancora i dataset e il training fallisce: `train.py` te lo dice
  subito. Se il tuo sistema ha solo un Python più nuovo, usa `uv venv --python
  3.11` o conda.
- GPU NVIDIA (locale) **oppure** Google Colab (T4 gratis).

## Come si esegue

### Su Colab (consigliato, GPU T4 gratis)
1. Apri un notebook Unsloth di **Qwen3** (Runtime → GPU).
2. Carica la cartella `finetune/` (o clona la repo).
3. `pip install -r requirements.txt` (spesso Unsloth è già presente).
4. `python train.py --config config.yaml`.

### In locale (GPU NVIDIA 8–12 GB+)
```bash
cd finetune
pip install -r requirements.txt
python train.py --config config.yaml
```

Al termine trovi il modello quantizzato in `gguf/`.

## Dal `.gguf` all'auto

```bash
# esempio con Ollama (sul PC per provare, poi sul Jetson)
ollama create gsoi -f Modelfile      # Modelfile che punta al tuo .gguf
ollama run gsoi                      # espone un endpoint OpenAI-compatible

# poi lato agente:
JARVIS_AI=local JARVIS_MODEL_URL=http://127.0.0.1:11434/v1 jarvis-mini serve
```

(oppure `llama.cpp` server: `llama-server -m gguf/....gguf --host 127.0.0.1 --port 8091`)

## Note

- **Model-agnostic:** per provare un altro modello (es. Minerva-7B) cambi solo
  `model.name` in `config.yaml` — attento alla VRAM per i 7B.
- Il `system_prompt` in `config.yaml` deve restare **identico** a
  `SYSTEM_PROMPT` in `src/jarvis_mini/ai/model_client.py`.
- `outputs/` e `gguf/` sono ignorati da git (file pesanti).
