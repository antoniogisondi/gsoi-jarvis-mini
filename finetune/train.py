#!/usr/bin/env python3
"""Fine-tuning QLoRA di Qwen3-4B per GSOI, con Unsloth.

    python train.py --config config.yaml

Gira su Colab (GPU T4 gratis) o su una workstation con GPU NVIDIA. NON gira
sul Jetson: qui si ADDESTRA; in auto si fa solo inferenza sul .gguf esportato.

Pipeline:
    dataset JSONL  ->  QLoRA (Unsloth)  ->  export GGUF  ->  gsoi-model (auto)

Nota: l'ecosistema (unsloth / trl / transformers) evolve in fretta. Se una
firma di funzione cambia, il riferimento canonico è il notebook Unsloth di
Qwen3: questo script ne segue la struttura, guidato da config.yaml.
"""

import argparse
import json
import sys
from pathlib import Path

# L'ecosistema unsloth/torch/datasets supporta Python 3.10–3.12. Su 3.13+
# 'dill' non riesce a serializzare i Dataset (pickle cambiato) e il training
# muore con un traceback criptico: meglio avvisare subito e chiaro.
if sys.version_info[:2] < (3, 10) or sys.version_info[:2] >= (3, 13):
    sys.exit(
        f"[GSOI] Serve Python 3.10–3.12 (rilevato {sys.version_info.major}."
        f"{sys.version_info.minor}). Ricrea il venv, es.:\n"
        "  rm -rf .venv && python3.11 -m venv .venv && source .venv/bin/activate\n"
        "  pip install -r requirements.txt\n"
        "  (oppure:  uv venv --python 3.11 .venv)"
    )

import yaml


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rows(jsonl_path: Path, system_prompt: str) -> list:
    """Carica il JSONL e antepone il system prompt dove manca."""
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                msgs = obj["messages"]
            except (json.JSONDecodeError, KeyError) as exc:
                raise ValueError(f"riga {n} non valida in {jsonl_path}: {exc}")
            if not msgs or msgs[0].get("role") != "system":
                msgs = [{"role": "system", "content": system_prompt}] + msgs
            rows.append({"messages": msgs})
    if not rows:
        raise ValueError(f"nessun esempio in {jsonl_path}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning QLoRA GSOI (Unsloth).")
    parser.add_argument("--config", default="config.yaml", help="file YAML di configurazione")
    args = parser.parse_args()

    cfg = load_config(args.config)
    base_dir = Path(args.config).resolve().parent

    # Import pesanti solo ora: config e dataset si validano senza GPU/unsloth.
    from unsloth import FastLanguageModel
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    m, lo, tr, ex = cfg["model"], cfg["lora"], cfg["train"], cfg["export"]

    print(f"[GSOI] Carico il modello base: {m['name']} (4bit={m['load_in_4bit']})")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=m["name"],
        max_seq_length=m["max_seq_length"],
        load_in_4bit=m["load_in_4bit"],
        dtype=None,  # auto (bf16/fp16 secondo la GPU)
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=lo["r"],
        target_modules=lo["target_modules"],
        lora_alpha=lo["alpha"],
        lora_dropout=lo["dropout"],
        bias=lo.get("bias", "none"),
        use_gradient_checkpointing="unsloth",
        random_state=tr["seed"],
    )

    # --- Dataset: applica il chat template di Qwen3 -------------------------
    jsonl = (base_dir / cfg["dataset"]["path"]).resolve()
    print(f"[GSOI] Dataset: {jsonl}")
    rows = load_rows(jsonl, cfg["dataset"]["system_prompt"])

    def to_text(example):
        return {
            "text": tokenizer.apply_chat_template(
                example["messages"], tokenize=False, add_generation_prompt=False
            )
        }

    dataset = Dataset.from_list(rows).map(to_text)
    print(f"[GSOI] Esempi di training: {len(dataset)}")

    # --- Training ----------------------------------------------------------
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            dataset_text_field="text",
            max_seq_length=m["max_seq_length"],
            per_device_train_batch_size=tr["batch_size"],
            gradient_accumulation_steps=tr["grad_accum"],
            warmup_ratio=tr["warmup_ratio"],
            num_train_epochs=tr["epochs"],
            learning_rate=float(tr["learning_rate"]),
            weight_decay=tr.get("weight_decay", 0.01),
            lr_scheduler_type=tr.get("lr_scheduler", "linear"),
            optim=tr.get("optimizer", "adamw_8bit"),
            logging_steps=tr.get("logging_steps", 1),
            seed=tr["seed"],
            output_dir=tr["output_dir"],
        ),
    )

    print("[GSOI] Avvio training...")
    trainer.train()

    # --- Salvataggi ed export ---------------------------------------------
    out_dir = base_dir / tr["output_dir"]
    if ex.get("save_lora", True):
        lora_dir = out_dir / "lora"
        model.save_pretrained(str(lora_dir))
        tokenizer.save_pretrained(str(lora_dir))
        print(f"[GSOI] Adapter LoRA salvati in: {lora_dir}")

    if ex.get("save_merged_16bit", False):
        merged_dir = out_dir / "merged-16bit"
        model.save_pretrained_merged(str(merged_dir), tokenizer, save_method="merged_16bit")
        print(f"[GSOI] Modello merge 16-bit salvato in: {merged_dir}")

    if ex.get("gguf", True):
        gguf_dir = base_dir / ex["out_dir"]
        model.save_pretrained_gguf(
            str(gguf_dir), tokenizer, quantization_method=ex["quantization"]
        )
        print(f"[GSOI] GGUF ({ex['quantization']}) esportato in: {gguf_dir}")
        print("[GSOI] Servilo con Ollama/llama.cpp su 127.0.0.1 e imposta JARVIS_AI=local.")

    print("[GSOI] Fatto.")


if __name__ == "__main__":
    main()
