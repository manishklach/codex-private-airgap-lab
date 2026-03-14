#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab"
OUTPUT_DIR="${1:-/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab/artifacts/tiny-gpt2-lora}"
MODEL_ID="sshleifer/tiny-gpt2"

source ~/codex-airgap-venv/bin/activate

python "$REPO_ROOT/wsl/train_lora.py" \
  --model "$MODEL_ID" \
  --train-data "$REPO_ROOT/data/train.jsonl" \
  --valid-data "$REPO_ROOT/data/valid.jsonl" \
  --output-dir "$OUTPUT_DIR" \
  --max-length 256 \
  --epochs 1
