# Codex Private Airgap Lab

This repository documents and demonstrates a practical Windows PowerShell + WSL Ubuntu pipeline for:

- operating Codex CLI in `--oss` mode
- scoping Codex to a private local workspace
- creating a supervised fine-tuning dataset from local files
- running a local LoRA fine-tuning job in WSL Ubuntu
- testing the resulting adapter locally
- documenting what is and is not directly usable with Ollama and Codex

The goal of this repo is to show the pipeline clearly, not to pretend every model in the pipeline is production-ready for Codex.

## What This Repo Actually Proves

This repo proves the following end to end:

- local workspace files can be turned into a supervised JSONL dataset
- a LoRA fine-tuning run can be executed locally in WSL
- adapter artifacts can be produced locally
- the trained adapter can be queried locally
- the adapter can be exposed through a simple local browser UI

This repo does not claim that every successful training run here is a good Codex backend model.

## Current State

What is implemented and verified:

- sample corpus copied into `samples/source/`
- reproducible dataset generation script
- generated `train.jsonl`, `valid.jsonl`, and `test.jsonl`
- WSL training script using Transformers + PEFT LoRA
- PowerShell helpers for monitoring and launch
- local-only documentation
- a real tiny LoRA example artifact at `artifacts/tiny-gpt2-lora/`
- a real DistilGPT2 LoRA example artifact at `artifacts/distilgpt2-copilot-sre-lora/`
- a local browser UI for the DistilGPT2 LoRA demo
- a realistic TinyLlama base-model path for an Ollama/Codex-oriented workflow

What is documented as constrained or incomplete:

- DistilGPT2 is fast enough for a local LoRA demo, but weak for useful repo Q&A
- DistilGPT2 is not the right model family for the intended Codex + Ollama backend path
- TinyLlama is a more realistic Ollama/Codex target, but CPU-only LoRA training in WSL was too slow on this machine to complete practically
- a fully local `codex --oss -m <fine-tuned-model>` demo still depends on successfully training and packaging a compatible Ollama-served model

## Repository Layout

- `docs/` - Mac and Windows guides in Markdown and HTML
- `samples/source/` - sample files copied from the local `copilot-sre` repository
- `data/` - generated fine-tuning dataset
- `scripts/` - PowerShell and Python helpers
- `wsl/` - WSL Ubuntu training assets
- `ui/` - local UI for the DistilGPT2 demo
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

Recommended order:

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

What this demonstrates:

- a real local LoRA training run can complete on this machine
- adapter files are produced locally
- the resulting model can be queried locally

What it does not demonstrate:

- high-quality repo question answering
- a Codex-compatible Ollama backend model

### 3c. Open a Local Browser UI for DistilGPT2

Install `gradio` in the WSL training environment if needed:

```bash
source ~/codex-airgap-venv/bin/activate
pip install gradio
```

Then launch the UI:

```bash
cd /mnt/c/Users/ManishKL/Documents/Playground/codex-private-airgap-lab
source ~/codex-airgap-venv/bin/activate
bash wsl/run_distilgpt2_ui.sh
```

Open:

- `http://127.0.0.1:7860`

Files used by the UI:

- `artifacts/distilgpt2-base/`
- `artifacts/distilgpt2-copilot-sre-lora/`

What this UI is:

- a local browser interface to the DistilGPT2 LoRA demo

What it is not:

- not a Codex backend model
- not served through Ollama or LM Studio for `codex --oss`

Why the answers may be poor:

- `distilgpt2` is a small continuation model, not a strong modern instruction model
- the LoRA run here is intentionally tiny and exists to prove the mechanics
- the UI therefore demonstrates local inference, not a high-quality assistant

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

- the included `tiny-gpt2` and DistilGPT2 artifacts are real fine-tuning examples
- the locally served Ollama alias used during repo setup was still based on a compatible Ollama model, not the DistilGPT2 adapter
- to connect Codex to a fine-tuned model with `--oss -m`, you still need a compatible local serving path such as a successfully packaged Ollama-servable model

## TinyLlama Path

For a more realistic local model path, the repo now includes:

- base model directory: `artifacts/tinyllama-base/`
- WSL runner: `wsl/run_tinyllama_example.sh`
- Ollama adapter template: `ollama/Modelfile.tinyllama.adapter.template`

That path is intended for:

1. running LoRA against a small Llama-family instruct model
2. packaging the adapter for Ollama with an `ADAPTER` Modelfile
3. launching Codex against the resulting local model with `--oss -m ...`

This is the right serving shape for a real local Codex workflow. The constraint on this machine was CPU runtime, not repository setup.

TinyLlama explanation:

- TinyLlama is a 1.1B chat model and is much closer to a real Ollama/Codex local serving target than `tiny-gpt2`
- that makes it more realistic, but also much slower on CPU-only WSL
- the repo keeps TinyLlama as the realistic path and DistilGPT2 as the faster validation path

This is the core distinction in the repo:

- DistilGPT2 proves the local LoRA pipeline quickly
- TinyLlama represents the more realistic Ollama/Codex direction

## Codex `--oss` Boundary

Be precise about what `--oss` proves.

- `--oss` tells Codex to use a local OSS model provider
- `-m` selects the model on that local provider
- `network_access = false` restricts sandboxed command execution from using the network

That combination is a strong local-only Codex setup, but it is not by itself a true physical air gap.

Additional controls still matter:

- disable web search
- avoid MCP servers that proxy to remote services
- ensure the provider is genuinely local
- disconnect the host from the network if you need strict air-gap assurance

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

The repo also includes a successful DistilGPT2 LoRA training example:

- base model: `distilgpt2`
- training data: generated from local files in `samples/source/`
- output directory: `artifacts/distilgpt2-copilot-sre-lora/`
- local UI path: `ui/distilgpt2_gradio.py`

This DistilGPT2 path is the fastest verified proof of the pipeline on this machine.

## Practical Conclusion

If you want to understand the pipeline, this repo now demonstrates it clearly:

1. pick local files
2. build JSONL
3. run LoRA locally
4. produce adapter artifacts
5. query the result locally
6. document the difference between a successful fine-tune and a Codex-compatible served model

That distinction is the main lesson from this repo.
