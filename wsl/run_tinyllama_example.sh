#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab"
OUTPUT_DIR="${1:-/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab/artifacts/tinyllama-copilot-sre-lora}"
MODEL_PATH="/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab/artifacts/tinyllama-base"

source ~/codex-airgap-venv/bin/activate

python "$REPO_ROOT/wsl/train_lora.py" \
  --model "$MODEL_PATH" \
  --train-data "$REPO_ROOT/data/train.jsonl" \
  --valid-data "$REPO_ROOT/data/valid.jsonl" \
  --output-dir "$OUTPUT_DIR" \
  --max-length 64 \
  --epochs 1 \
  --max-steps 2
