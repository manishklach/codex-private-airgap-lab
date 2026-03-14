#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab"

source ~/codex-airgap-venv/bin/activate
python "$REPO_ROOT/ui/distilgpt2_gradio.py"
