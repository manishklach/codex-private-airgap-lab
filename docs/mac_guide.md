# Private Air-Gapped AI Workspace on Mac with Codex CLI

This guide explains how to build a private local AI workflow on Apple Silicon Macs for sensitive code and documents. It covers:

- local-only Codex CLI usage
- private workspace scoping
- MLX-based fine-tuning on Mac
- local serving of the fine-tuned model
- safe usage patterns for an air-gapped workflow

This guide is written for Apple Silicon Macs. The workflow assumes you want your sensitive workspace to stay on your own machine.

## 1. What This Setup Does

This setup gives you a strong local-only workflow:

- Codex CLI runs on your Mac
- the model is served locally
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

```bash
codex --oss -C ~/SensitivePatent
codex --oss -C ~/SensitivePatent --add-dir ~/ResearchDocs
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

On many Macs, QLoRA is the better starting point because it is more memory efficient.

## 4. Recommended Architecture on Mac

For Apple Silicon, a clean private workflow looks like this:

1. Prepare a base open-source model locally
2. Convert your private workspace into a supervised fine-tuning dataset
3. Fine-tune locally with MLX
4. Fuse or keep the adapter
5. Serve the resulting model locally through LM Studio or Ollama
6. Use Codex CLI with `--oss` and `-m` to connect to that local model

Important distinction:

- MLX is the fine-tuning tool
- LM Studio or Ollama is the local model server Codex connects to

## 5. Installation

### 5.1 Install Codex CLI

Install Codex CLI by one of the official supported methods.

Example with Homebrew:

```bash
brew install --cask codex
```

Verify:

```bash
codex --version
```

### 5.2 Install Python and Create an Environment

Use Python 3 on the Mac:

```bash
python3 -m venv ~/.venvs/mlx-ft
source ~/.venvs/mlx-ft/bin/activate
python -m pip install --upgrade pip
```

### 5.3 Install MLX-LM for Fine-Tuning

Install MLX-LM with training extras:

```bash
pip install "mlx-lm[train]"
```

### 5.4 Install a Local Model Server

Install one of:

- LM Studio
- Ollama

Codex currently expects the local OSS model to be served through one of those providers.

## 6. Prepare Before Disconnecting from the Network

If you want a strict air-gapped workflow, do your downloads first while still online:

- install Codex CLI
- install Python packages
- download the base model you want to fine-tune
- install and verify LM Studio or Ollama

Only after all required assets are present should you disconnect the Mac from the network.

For strict assurance:

- turn off Wi-Fi
- unplug Ethernet if used
- avoid background sync clients
- avoid cloud-mounted folders

## 7. Choose a Base Model

For a private coding assistant, start with a manageable instruct or coder model. Smaller models are easier to fine-tune and serve locally.

Typical good starting points:

- a 7B coding model
- a 14B coding model if your Mac has enough memory
- a 20B class model only if you have the hardware headroom

General rule:

- smaller model = easier fine-tuning and serving
- larger model = better capability but higher memory pressure

## 8. Prepare the Fine-Tuning Dataset

This is the most important step.

Do not point the trainer at a folder and expect it to "learn the repo." Fine-tuning requires a dataset of examples.

Your dataset should reflect the behavior you want from the model.

Good example categories:

- explain modules from your private codebase
- summarize internal architecture docs
- answer domain-specific technical questions
- refactor code in your preferred style
- write structured documents in your preferred format

### 8.1 Recommended Data Format

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

### 8.2 Create a Dataset Directory

Example:

```bash
mkdir -p ~/airgap-ft/data
```

Suggested files:

- `~/airgap-ft/data/train.jsonl`
- `~/airgap-ft/data/valid.jsonl`
- `~/airgap-ft/data/test.jsonl`

### 8.3 Dataset Quality Rules

Use these rules:

- remove secrets you do not want reproduced
- prefer clean, high-quality examples over raw volume
- keep answer style consistent
- keep prompts realistic
- hold out some examples for evaluation

Fine-tuning works best when the dataset teaches behavior, style, and domain response patterns. It is not the best tool for frequently changing factual content.

## 9. Fine-Tune Locally with MLX

Once your dataset is ready and your Mac is offline, run the fine-tuning job locally.

Example starting command:

```bash
mlx_lm.lora \
  --model /path/to/base-model \
  --train \
  --data ~/airgap-ft/data \
  --iters 600 \
  --batch-size 1 \
  --num-layers 4 \
  --adapter-path ~/airgap-ft/adapters
```

What this does:

- loads the local base model
- trains a LoRA adapter on your dataset
- writes adapter weights into `~/airgap-ft/adapters`

Notes:

- if the base model is quantized, MLX-LM can use a QLoRA-style workflow automatically
- the right iteration count depends on dataset size and quality
- start small and evaluate before running longer jobs

## 10. Test the Adapter

Before deployment, test the adapter locally.

Example:

```bash
mlx_lm.generate \
  --model /path/to/base-model \
  --adapter-path ~/airgap-ft/adapters \
  --prompt "Explain how the scheduler works in this private codebase."
```

You should compare test outputs against:

- held-out examples
- known good answers
- code style expectations

## 11. Fuse the Model for Serving

You can either keep the adapter separate or fuse it into a deployable model.

Example fuse command:

```bash
mlx_lm.fuse \
  --model /path/to/base-model \
  --adapter-path ~/airgap-ft/adapters \
  --save-path ~/airgap-ft/fused_model
```

This produces a model artifact you can load into your local serving stack.

## 12. Serve the Fine-Tuned Model Locally

Codex CLI does not load arbitrary raw checkpoints directly by itself. The practical path is:

1. load the fused or adapted model into LM Studio or Ollama
2. start the local server
3. point Codex at that local server using `--oss`

### 12.1 LM Studio Path

General shape:

- import the model into LM Studio
- start the local OpenAI-compatible server
- note the model identifier shown by LM Studio

### 12.2 Ollama Path

General shape:

- create or import the model into Ollama
- run the local Ollama server
- note the local model name

## 13. Use the Fine-Tuned Model with Codex CLI

Once the local model server is running:

```bash
codex --oss --local-provider lmstudio -m your-finetuned-model -C ~/SensitivePatent
```

Or with an extra writable directory:

```bash
codex --oss --local-provider lmstudio -m your-finetuned-model -C ~/SensitivePatent --add-dir ~/ResearchDocs
```

Equivalent Ollama shape:

```bash
codex --oss --local-provider ollama -m your-finetuned-model -C ~/SensitivePatent
```

Meaning:

- `--oss` selects the local OSS provider
- `--local-provider` selects which local server Codex uses
- `-m` selects the specific model exposed by that server
- `-C` sets the primary workspace
- `--add-dir` adds additional writable roots

## 14. Recommended Secure Codex Settings

Use conservative settings for sensitive work.

Interactive example:

```bash
codex \
  --oss \
  --local-provider lmstudio \
  -m your-finetuned-model \
  -C ~/SensitivePatent \
  --sandbox workspace-write \
  --ask-for-approval on-request
```

Recommended config example:

```toml
model_provider = "oss"
oss_provider = "lmstudio"
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

## 15. Important Security Boundaries

Be precise about the protection level:

- `--oss` means local model provider
- `network_access = false` means sandboxed shell commands cannot use the network
- neither of those alone guarantees a true physical air gap

To claim a real air-gapped workflow, you also need:

- the Mac disconnected or isolated from all external networks
- no external MCP servers
- no remote model provider configured
- no sync tools leaking data outside the machine

## 16. Fine-Tuning vs Retrieval

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

## 17. Common Mistakes

Avoid these:

- calling workspace scoping "training"
- assuming `--oss` alone means fully air-gapped
- feeding raw private repos directly into training without curation
- fine-tuning when retrieval would solve the problem better
- testing only on training examples

## 18. Minimal End-to-End Workflow

1. Install Codex CLI, MLX-LM, and a local server
2. Download the base model while still online
3. Build a clean JSONL dataset from the private workspace
4. Disconnect the Mac from the network
5. Fine-tune with MLX LoRA or QLoRA
6. Test the adapter
7. Fuse or package the model
8. Serve it locally through LM Studio or Ollama
9. Launch Codex with `--oss -m ...`
10. Work inside the scoped private workspace

## 19. Example Session

Example launch:

```bash
codex \
  --oss \
  --local-provider lmstudio \
  -m patent-coder-private-v1 \
  -C ~/Documents/SensitivePatent \
  --add-dir ~/Documents/PatentResearch \
  --sandbox workspace-write \
  --ask-for-approval on-request
```

Inside Codex, use:

- `/status` to verify model, sandbox, and writable roots

## 20. Final Takeaway

The correct mental model is:

- Codex scopes and uses your local workspace
- MLX fine-tunes a local model on a curated dataset derived from that workspace
- LM Studio or Ollama serves the resulting model locally
- `--oss` and `network_access = false` support a strong local-only workflow
- host-level isolation is still required for a true air gap

