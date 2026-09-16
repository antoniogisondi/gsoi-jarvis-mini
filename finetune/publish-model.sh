#!/usr/bin/env bash
#
# publish-model.sh — carica il modello GGUF su HuggingFace e stampa le due
# righe pronte da incollare nella ricetta dei pesi dell'OS.
#
# Uso:
#   ./publish-model.sh [percorso.gguf]
#
# Senza argomenti usa il primo *.gguf trovato in finetune/gguf_gguf/.
# Richiede: hf (huggingface_hub) con login gia' fatto, sha256sum, python3.
#
# Il file viene caricato SEMPRE con lo stesso nome sul repo HF: ogni upload
# crea un nuovo commit, e la ricetta si pinna a QUELLA revisione (build
# riproducibili anche se ricarichi).
set -euo pipefail

# --- Configurazione (sovrascrivibile da env) --------------------------------
REPO="${GSOI_HF_REPO:-gsoi/gsoi-qwen3-4b-gguf}"
REMOTE_NAME="${GSOI_HF_FILENAME:-qwen3-4b-instruct-2507.Q4_K_M.gguf}"
# Nome con cui la ricetta salva il file nel rootfs (NON cambiarlo: il launcher
# gsoi-model cerca *.gguf in /var/lib/gsoi-model).
DOWNLOAD_NAME="gsoi-qwen3-4b-q4_k_m.gguf"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Usa il venv del finetune se presente, così 'hf' e huggingface_hub ci sono
# anche se non hai fatto 'source .venv/bin/activate'.
if [ -d "$SCRIPT_DIR/.venv/bin" ]; then
    export PATH="$SCRIPT_DIR/.venv/bin:$PATH"
fi

if ! command -v hf >/dev/null 2>&1; then
    echo "ERRORE: 'hf' non trovato. Attiva il venv del finetune o installa" >&2
    echo "        huggingface_hub:  uv pip install huggingface_hub" >&2
    exit 1
fi

# --- Individua il file GGUF -------------------------------------------------
GGUF="${1:-}"
if [ -z "$GGUF" ]; then
    GGUF="$(ls -t "$SCRIPT_DIR"/gguf_gguf/*.gguf 2>/dev/null | head -n1 || true)"
fi
if [ -z "$GGUF" ] || [ ! -f "$GGUF" ]; then
    echo "ERRORE: nessun .gguf trovato. Uso: $0 [percorso.gguf]" >&2
    exit 1
fi

echo ">> File:  $GGUF"
echo ">> Repo:  $REPO   (come '$REMOTE_NAME')"

# --- sha256 -----------------------------------------------------------------
echo ">> Calcolo sha256..."
SHA="$(sha256sum "$GGUF" | awk '{print $1}')"

# --- Upload -----------------------------------------------------------------
echo ">> Upload su HuggingFace (puo' richiedere tempo)..."
hf upload "$REPO" "$GGUF" "$REMOTE_NAME"

# --- Recupera la revisione del commit appena creato -------------------------
echo ">> Recupero la revisione del commit..."
REV="$(python3 - "$REPO" <<'PY'
import sys
from huggingface_hub import HfApi
print(HfApi().list_repo_commits(sys.argv[1], repo_type="model")[0].commit_id)
PY
)"

# --- Stampa le righe pronte -------------------------------------------------
cat <<EOF

===========================================================================
FATTO. Incolla queste due righe in:
  layers/meta-gsoi/recipes-support/gsoi-model-weights/gsoi-model-weights.bb

SRC_URI = "https://huggingface.co/${REPO}/resolve/${REV}/${REMOTE_NAME};downloadfilename=${DOWNLOAD_NAME}"
SRC_URI[sha256sum] = "${SHA}"
===========================================================================

Poi nell'OS:  bitbake gsoi-automotive-image
(oppure test rapido: copia il .gguf in /var/lib/gsoi-model/ e
 'systemctl restart gsoi-model' sul dispositivo/VM.)
EOF
