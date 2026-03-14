# Codex Private Airgap Lab

This repository packages a practical Windows PowerShell + WSL Ubuntu workflow for:

- operating Codex CLI in `--oss` mode
- scoping Codex to a private local workspace
- creating a sample supervised fine-tuning dataset from local files
- running a LoRA fine-tuning job in WSL Ubuntu
- serving the resulting model through Ollama
- launching Codex CLI against the served model with `-m`

This repo is intentionally self-contained. It includes:

- documentation for Mac and Windows local-only workflows
- sample source files copied from the local `copilot-sre` repository
- a dataset builder that converts those files into `train/valid/test` JSONL
- a WSL training script for a local LoRA run
- PowerShell helpers to validate the local stack and launch Codex
- an Ollama Modelfile template for serving the resulting model locally

## Current State

The repository is ready for a local Windows/WSL workflow, but the full LoRA training run is not executed automatically here because that depends on your machine's local compute environment and model availability.

What is implemented:

- sample corpus copied into `samples/source/`
- reproducible dataset generation script
- sample `train.jsonl`, `valid.jsonl`, and `test.jsonl`
- WSL training script scaffold using Transformers + PEFT LoRA
- PowerShell launch helpers for Codex and Ollama
- local-only documentation
- a real tiny LoRA example artifact produced in WSL at `artifacts/tiny-gpt2-lora/`
- a realistic TinyLlama base-model path for a Codex-servable local adapter workflow
- a smaller DistilGPT2 CPU-friendly LoRA demo path for faster local validation

What still depends on your machine when you run it:

- downloading or mounting the base model in WSL for anything beyond the included tiny example
- running a LoRA training job for a model you actually want to serve in Codex
- exporting or packaging the trained result for Ollama
- serving that trained model locally

## Repository Layout

- `docs/` - Mac and Windows guides in Markdown and HTML
- `samples/source/` - sample files copied from the local `copilot-sre` repository
- `data/` - generated fine-tuning dataset
- `scripts/` - PowerShell and Python helpers
- `wsl/` - WSL Ubuntu training assets
- `ollama/` - Ollama serving templates

## Sample Source Files

The sample corpus in this repo was copied from the local `copilot-sre` repository:

- `copilot-sre/README.md`
- `copilot-sre/docs/ARCHITECTURE.md`
- `copilot-sre/copilot_sre/analysis.py`
- `copilot-sre/copilot_sre/prompt_builder.py`
- `copilot-sre/copilot_sre/web.py`

These are used to generate a toy fine-tuning dataset so the repository has a concrete end-to-end path.

## Prerequisites

### Windows

- Windows PowerShell
- `codex` CLI installed
- `ollama` installed
- WSL2 installed with Ubuntu 24.04 or similar
- Python on Windows for dataset generation

### Optional

- GitHub CLI for repo operations
- LM Studio if you want LM Studio instead of Ollama

## Quick Start

### 1. Generate the Dataset

From PowerShell in the repo root:

```powershell
python .\scripts\build_dataset.py
```

This writes:

- `data\train.jsonl`
- `data\valid.jsonl`
- `data\test.jsonl`

### 2. Check the Local Stack

```powershell
.\scripts\check_local_stack.ps1
```

### 3. Train in WSL Ubuntu

Recommended default:

- use the DistilGPT2 path first for a fast local LoRA validation
- use TinyLlama later if you want a more realistic Ollama/Codex target

Inside WSL:

```bash
cd /mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab
bash wsl/run_train.sh /path/to/local-or-cached-model
```

This uses the local dataset and runs a LoRA job with the training script in `wsl/train_lora.py`.

### 3a. Run the Included Tiny LoRA Example

This repo already includes a completed tiny CPU-safe LoRA example using `sshleifer/tiny-gpt2`.

To reproduce it:

```bash
cd /mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab
source ~/codex-airgap-venv/bin/activate
bash wsl/run_tiny_example.sh
```

This produces the adapter in:

- `artifacts/tiny-gpt2-lora/`

To run a quick inference using that adapter:

```bash
python wsl/infer_lora.py \
  --model sshleifer/tiny-gpt2 \
  --adapter /mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab/artifacts/tiny-gpt2-lora \
  --prompt "Summarize the copilot-sre sample workspace."
```

Expected result:

- the command should run successfully and produce text
- the text quality will be poor because `sshleifer/tiny-gpt2` is only a CPU-safe mechanics demo, not a useful production model

### 3b. Run the Faster DistilGPT2 Example

For a larger but still CPU-friendlier demo than `tiny-gpt2`, use the local DistilGPT2 path:

```bash
cd /mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab
source ~/codex-airgap-venv/bin/activate
bash wsl/run_distilgpt2_example.sh
```

Output:

- `artifacts/distilgpt2-copilot-sre-lora/`

Windows helpers:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\start_distilgpt2_training.ps1
PowerShell -ExecutionPolicy Bypass -File .\scripts\check_distilgpt2_training.ps1
```

### 4. Package for Ollama

Use the model artifact from `artifacts/` and adapt the Modelfile template in:

- `ollama/Modelfile.template`
- `ollama/Modelfile.tinyllama.adapter.template`

### 5. Serve with Ollama

Example shape:

```powershell
ollama create codex-airgap-demo -f .\ollama\Modelfile
ollama run codex-airgap-demo
```

### 6. Launch Codex Against the Local Model

```powershell
.\scripts\launch_codex_ollama.ps1 -Model codex-airgap-demo -Workspace C:\Users\ManishKL\Documents\Playground\copilot-sre
```

Equivalent raw command:

```powershell
codex --oss --local-provider ollama -m codex-airgap-demo -C C:\Users\ManishKL\Documents\Playground\copilot-sre --sandbox workspace-write --ask-for-approval on-request
```

Note:

- the included `tiny-gpt2` LoRA artifact is a real fine-tuning example
- the locally served Ollama model alias in this repo is still based on `mistral:latest`
- to connect Codex to a LoRA-adapted model, you still need to package a compatible trained model for Ollama or LM Studio

## TinyLlama Path

For a more realistic local model path, the repo now includes:

- base model directory: `artifacts/tinyllama-base/`
- WSL runner: `wsl/run_tinyllama_example.sh`
- Ollama adapter template: `ollama/Modelfile.tinyllama.adapter.template`

That path is intended for:

1. running LoRA against a small Llama-family instruct model
2. packaging the adapter for Ollama with an `ADAPTER` Modelfile
3. launching Codex against the resulting local model with `--oss -m ...`

This is the right serving shape for a real local Codex workflow. The constraint on this machine is CPU runtime, not repository setup.

TinyLlama explanation:

- TinyLlama is a 1.1B chat model and is much closer to a real Ollama/Codex local serving target than `tiny-gpt2`
- that makes it more realistic, but also much slower on CPU-only WSL
- the repo keeps TinyLlama as the realistic path and DistilGPT2 as the faster validation path

## Airgap and Security Notes

Be precise about the protection level:

- `--oss` means Codex uses a local model provider
- `network_access = false` means sandboxed model-generated commands cannot use the network
- neither of those alone creates a true physical air gap

For a strict air-gapped workflow, also:

- disconnect the host from the network
- keep web search disabled
- avoid remote MCP servers
- avoid sync tools that move workspace data to the cloud

## Notes on Fine-Tuning

This repo uses a LoRA path because it is the most practical way to adapt a local model on a personal machine.

LoRA = Low-Rank Adaptation

QLoRA = Quantized Low-Rank Adaptation

In practice:

- LoRA trains small adapter weights instead of the whole model
- QLoRA reduces memory pressure further by using a quantized base model

## Verified Local Environment During Repo Creation

The following were present in the local environment when this repo was assembled:

- `codex` CLI
- `gh`
- `ollama`
- WSL Ubuntu 24.04

LM Studio was not installed in PATH at the time this repo was created, so the operational path in this repo is wired around Ollama.

## Verified Example Output

The repo includes a successful tiny LoRA training example:

- base model: `sshleifer/tiny-gpt2`
- training data: generated from local files in `samples/source/`
- output directory: `artifacts/tiny-gpt2-lora/`
- runtime: CPU-safe WSL example

This is meant as a concrete LoRA example, not as the final production model you would serve through Codex.
