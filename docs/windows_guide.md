# Private Air-Gapped AI Workspace on Windows PowerShell with Codex CLI

This guide explains how to build a private local AI workflow on Windows for sensitive code and documents. It covers:

- local-only Codex CLI usage
- private workspace scoping
- Windows PowerShell operation
- WSL-based fine-tuning for local OSS models
- local serving of the fine-tuned model
- safe usage patterns for an air-gapped workflow

This guide assumes:

- you are using Windows PowerShell
- you want your sensitive workspace to remain on your own machine
- you want to use Codex with a locally served model

## 1. What This Setup Does

This setup gives you a strong local-only workflow:

- Codex CLI runs locally on Windows
- the model is served locally through Ollama or LM Studio
- your workspace is scoped to specific directories
- sandboxed shell commands can be denied network access
- you can fine-tune a local OSS model on private workspace-derived data

Important: this is not automatically a true air gap just because you use `--oss`.

A true air-gapped workflow requires all of the following:

- local model provider only
- sandbox network disabled
- web search disabled
- no MCP servers that reach remote services
- the host machine itself offline or physically isolated if you need strict assurance

## 2. Core Concepts

### Codex CLI

Codex CLI is the local terminal agent. It can read files, edit files, and run commands in your workspace.

### `--oss`

`--oss` tells Codex to use the local open-source model provider instead of a remote hosted provider.

In the current Codex CLI, the local providers are:

- `ollama`
- `lmstudio`

`--oss` is not by itself a complete "kill switch" for all network activity. It only selects the local model provider.

### `network_access = false`

This controls whether sandboxed model-generated shell commands can access the network.

It is an important local-only control, but it is not the entire air-gap story by itself.

### Workspace Scoping

Codex does not "train itself on your workspace" automatically. Instead, you give it access to specific folders for the current session.

Examples:

```powershell
codex --oss -C C:\SensitivePatent
codex --oss -C C:\SensitivePatent --add-dir C:\ResearchDocs
```

This affects session context, not permanent model learning.

### Fine-Tuning

Fine-tuning means adapting a model outside Codex, then serving that fine-tuned model locally and pointing Codex at it.

Codex does not fine-tune models by itself.

## 3. LoRA and QLoRA

- LoRA = Low-Rank Adaptation
- QLoRA = Quantized Low-Rank Adaptation

Practical meaning:

- LoRA trains small adapter weights instead of retraining the full model
- QLoRA does the same while keeping the base model quantized, reducing memory usage

On Windows, QLoRA is usually the better starting point if you are fine-tuning on consumer GPU hardware.

## 4. Recommended Architecture on Windows

For Windows, a clean private workflow looks like this:

1. Prepare a base open-source model locally
2. Convert your private workspace into a supervised fine-tuning dataset
3. Fine-tune locally, usually in WSL with NVIDIA CUDA support
4. Merge or keep the adapter
5. Serve the resulting model locally through LM Studio or Ollama
6. Use Codex CLI in PowerShell with `--oss` and `-m` to connect to that local model

Important distinction:

- WSL or Linux tooling is the practical fine-tuning path on Windows
- LM Studio or Ollama is the local model server Codex connects to

## 5. Recommended Hardware

Fine-tuning on Windows is most practical with:

- NVIDIA GPU
- WSL2 installed
- recent CUDA-compatible drivers
- enough disk for models, datasets, and checkpoints

If you do not have an NVIDIA GPU:

- local fine-tuning is still possible in some cases
- but it is usually slow and much less practical
- in that case, use retrieval or smaller adapter experiments instead of expecting a strong fine-tuning workflow

## 6. Installation

### 6.1 Install Codex CLI

Install Codex CLI by one of the official supported methods.

Example:

```powershell
npm install -g @openai/codex
```

Verify:

```powershell
codex --version
```

### 6.2 Install Python

Install Python 3 and verify:

```powershell
python --version
```

### 6.3 Install WSL

For practical Windows fine-tuning, install WSL:

```powershell
wsl --install
```

After restart, install an Ubuntu distribution and verify:

```powershell
wsl -l -v
```

### 6.4 Install a Local Model Server

Install one of:

- LM Studio
- Ollama

Codex currently expects the local OSS model to be served through one of those providers.

## 7. Prepare Before Disconnecting from the Network

If you want a strict air-gapped workflow, do your downloads first while still online:

- install Codex CLI
- install Python
- install WSL and your Linux toolchain
- install fine-tuning packages
- download the base model you want to fine-tune
- install and verify LM Studio or Ollama

Only after all required assets are present should you disconnect the machine from the network.

For strict assurance:

- turn off Wi-Fi
- unplug Ethernet if used
- avoid OneDrive or cloud-mounted workspace folders
- avoid editors or tools with background cloud sync

## 8. Choose a Base Model

For a private coding assistant, start with a manageable instruct or coder model.

Typical good starting points:

- a 7B coding model
- a 14B coding model if you have enough VRAM
- a larger model only if your hardware can support it

General rule:

- smaller model = easier fine-tuning and serving
- larger model = better capability but higher memory pressure

## 9. Prepare the Fine-Tuning Dataset

This is the most important step.

Do not point the trainer at a folder and expect it to "learn the repo." Fine-tuning requires a dataset of examples.

Your dataset should reflect the behavior you want from the model.

Good example categories:

- explain modules from your private codebase
- summarize internal architecture docs
- answer domain-specific technical questions
- refactor code in your preferred style
- write structured documents in your preferred format

### 9.1 Recommended Data Format

Use JSONL. Each line should be one training example.

Chat-style example:

```json
{"messages":[
  {"role":"system","content":"You are an expert assistant for this private codebase."},
  {"role":"user","content":"Explain how the job scheduler works."},
  {"role":"assistant","content":"The scheduler coordinates queued tasks by..."}
]}
```

Code transformation example:

```json
{"messages":[
  {"role":"system","content":"You are a careful code refactoring assistant."},
  {"role":"user","content":"Refactor this function to avoid shared mutable state:\n<code here>"},
  {"role":"assistant","content":"<ideal refactor here>"}
]}
```

### 9.2 Create a Dataset Directory

Example:

```powershell
New-Item -ItemType Directory -Force -Path C:\airgap-ft\data
```

Suggested files:

- `C:\airgap-ft\data\train.jsonl`
- `C:\airgap-ft\data\valid.jsonl`
- `C:\airgap-ft\data\test.jsonl`

### 9.3 Dataset Quality Rules

Use these rules:

- remove secrets you do not want reproduced
- prefer clean, high-quality examples over raw volume
- keep answer style consistent
- keep prompts realistic
- hold out some examples for evaluation

Fine-tuning works best when the dataset teaches behavior, style, and domain response patterns. It is not the best tool for frequently changing factual content.

## 10. Fine-Tuning Path on Windows

The practical fine-tuning path on Windows is usually:

1. use PowerShell for Windows-side setup
2. use WSL for the fine-tuning run
3. serve the resulting model locally on Windows
4. use Codex from PowerShell against that local server

This is the cleanest path because most modern local fine-tuning tools are better supported on Linux than on native Windows.

## 11. Fine-Tune Locally in WSL

Inside WSL, create a Python environment and install your fine-tuning stack.

Typical starting point:

```bash
python3 -m venv ~/ft-env
source ~/ft-env/bin/activate
pip install --upgrade pip
```

Then install your chosen QLoRA or LoRA tooling. A practical choice is an Unsloth-style QLoRA workflow if your stack supports it.

General shape:

```bash
python train.py \
  --model /path/to/base-model \
  --train-data /mnt/c/airgap-ft/data/train.jsonl \
  --valid-data /mnt/c/airgap-ft/data/valid.jsonl \
  --output-dir /mnt/c/airgap-ft/output \
  --lora
```

The exact command depends on the fine-tuning framework you choose, but the output is usually one of:

- adapter weights
- merged model
- checkpoint directory

## 12. Test the Fine-Tuned Result

Before deployment, test the adapter or merged model locally.

Verify:

- held-out examples are answered correctly
- behavior improved on private domain tasks
- the model does not simply overfit or parrot training prompts

## 13. Package the Model for Serving

Once the result looks good, package it for your local serving stack:

- import it into LM Studio
- or create/import it in Ollama

Codex CLI does not load arbitrary raw checkpoints directly by itself. The practical path is:

1. load the trained model artifact into LM Studio or Ollama
2. start the local server
3. point Codex at that local server using `--oss`

## 14. Use the Fine-Tuned Model with Codex CLI

Once the local model server is running:

```powershell
codex --oss --local-provider ollama -m your-finetuned-model -C C:\SensitivePatent
```

Or with LM Studio:

```powershell
codex --oss --local-provider lmstudio -m your-finetuned-model -C C:\SensitivePatent
```

With an extra writable directory:

```powershell
codex --oss --local-provider ollama -m your-finetuned-model -C C:\SensitivePatent --add-dir C:\ResearchDocs
```

Meaning:

- `--oss` selects the local OSS provider
- `--local-provider` selects which local server Codex uses
- `-m` selects the specific model exposed by that server
- `-C` sets the primary workspace
- `--add-dir` adds additional writable roots

## 15. Recommended Secure Codex Settings

Use conservative settings for sensitive work.

Interactive example:

```powershell
codex `
  --oss `
  --local-provider ollama `
  -m your-finetuned-model `
  -C C:\SensitivePatent `
  --sandbox workspace-write `
  --ask-for-approval on-request
```

Recommended config file location:

```powershell
$env:USERPROFILE\.codex\config.toml
```

Recommended config example:

```toml
model_provider = "oss"
oss_provider = "ollama"
model = "your-finetuned-model"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "disabled"

[sandbox_workspace_write]
network_access = false
```

What this gives you:

- local model provider
- explicit workspace sandbox
- explicit approval gate
- web search off
- sandboxed command network disabled

## 16. Important Security Boundaries

Be precise about the protection level:

- `--oss` means local model provider
- `network_access = false` means sandboxed shell commands cannot use the network
- neither of those alone guarantees a true physical air gap

To claim a real air-gapped workflow, you also need:

- the Windows machine disconnected or isolated from all external networks
- no external MCP servers
- no remote model provider configured
- no sync tools leaking data outside the machine

## 17. Fine-Tuning vs Retrieval

Use the right tool for the job.

Fine-tuning is best for:

- writing style
- answer format
- code transformation habits
- domain-specific behavior

Retrieval is best for:

- frequently changing code
- large document sets
- exact factual recall from current files

If your workspace changes often, retrieval over the private files is usually better than repeatedly fine-tuning.

## 18. Common Mistakes

Avoid these:

- calling workspace scoping "training"
- assuming `--oss` alone means fully air-gapped
- feeding raw private repos directly into training without curation
- fine-tuning on Windows CPU and expecting a practical workflow
- testing only on training examples

## 19. Minimal End-to-End Workflow

1. Install Codex CLI, WSL, your fine-tuning stack, and a local model server
2. Download the base model while still online
3. Build a clean JSONL dataset from the private workspace
4. Disconnect the machine from the network
5. Fine-tune in WSL with LoRA or QLoRA
6. Test the adapter or merged model
7. Package the model for LM Studio or Ollama
8. Serve it locally
9. Launch Codex with `--oss -m ...`
10. Work inside the scoped private workspace

## 20. Example Session

Example launch:

```powershell
codex `
  --oss `
  --local-provider ollama `
  -m patent-coder-private-v1 `
  -C C:\Users\You\Documents\SensitivePatent `
  --add-dir C:\Users\You\Documents\PatentResearch `
  --sandbox workspace-write `
  --ask-for-approval on-request
```

Inside Codex, use:

- `/status` to verify model, sandbox, and writable roots

## 21. Final Takeaway

The correct mental model is:

- Codex scopes and uses your local workspace
- WSL-based tooling fine-tunes a local model on a curated dataset derived from that workspace
- LM Studio or Ollama serves the resulting model locally
- `--oss` and `network_access = false` support a strong local-only workflow
- host-level isolation is still required for a true air gap

