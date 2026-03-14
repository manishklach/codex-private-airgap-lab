#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: bash wsl/run_train.sh /path/to/model [output_dir]"
  exit 1
fi

MODEL_PATH="$1"
OUTPUT_DIR="${2:-/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab/artifacts/lora-output}"
REPO_ROOT="/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab"

python3 -m venv "$HOME/codex-airgap-venv"
source "$HOME/codex-airgap-venv/bin/activate"
python -m pip install --upgrade pip
pip install -r "$REPO_ROOT/wsl/requirements.txt"

python "$REPO_ROOT/wsl/train_lora.py" \
  --model "$MODEL_PATH" \
  --train-data "$REPO_ROOT/data/train.jsonl" \
  --valid-data "$REPO_ROOT/data/valid.jsonl" \
  --output-dir "$OUTPUT_DIR"

