from __future__ import annotations

from pathlib import Path

import gradio as gr
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_MODEL = REPO_ROOT / "artifacts" / "distilgpt2-base"
ADAPTER = REPO_ROOT / "artifacts" / "distilgpt2-copilot-sre-lora"


def load_model() -> tuple[AutoTokenizer, PeftModel]:
    tokenizer = AutoTokenizer.from_pretrained(str(BASE_MODEL), use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    has_pt = any((BASE_MODEL / name).exists() for name in ("pytorch_model.bin", "model.safetensors"))
    has_tf = (BASE_MODEL / "tf_model.h5").exists()

    model = AutoModelForCausalLM.from_pretrained(str(BASE_MODEL), from_tf=has_tf and not has_pt)
    model = PeftModel.from_pretrained(model, str(ADAPTER))
    model.eval()
    return tokenizer, model


TOKENIZER, MODEL = load_model()


def generate(prompt: str, max_new_tokens: int, temperature: float) -> str:
    prompt = prompt.strip()
    if not prompt:
        return ""

    inputs = TOKENIZER(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = MODEL.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=max(temperature, 1e-5),
            pad_token_id=TOKENIZER.eos_token_id,
        )
    return TOKENIZER.decode(outputs[0], skip_special_tokens=True)


demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Textbox(
            lines=8,
            label="Prompt",
            placeholder="Ask about the copilot-sre sample workspace...",
        ),
        gr.Slider(16, 256, value=96, step=8, label="Max New Tokens"),
        gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="Temperature"),
    ],
    outputs=gr.Textbox(lines=14, label="Model Output"),
    title="DistilGPT2 LoRA Demo",
    description="Local browser UI for the DistilGPT2 + copilot-sre LoRA demo in this repo.",
)


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
