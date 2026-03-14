from __future__ import annotations

import argparse
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple LoRA fine-tune from local JSONL data.")
    parser.add_argument("--model", required=True, help="Local model path or Hugging Face identifier.")
    parser.add_argument("--train-data", required=True, help="Path to train.jsonl")
    parser.add_argument("--valid-data", required=True, help="Path to valid.jsonl")
    parser.add_argument("--output-dir", required=True, help="Directory for LoRA artifacts")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=-1)
    return parser.parse_args()


def format_messages(example: dict) -> dict:
    messages = example["messages"]
    parts: list[str] = []
    for message in messages:
        parts.append(f"<|{message['role']}|>\n{message['content'].strip()}")
    return {"text": "\n\n".join(parts)}


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(
        "json",
        data_files={
            "train": args.train_data,
            "validation": args.valid_data,
        },
    )
    dataset = dataset.map(format_messages, remove_columns=dataset["train"].column_names)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def tokenize(example: dict) -> dict:
        return tokenizer(
            example["text"],
            truncation=True,
            max_length=args.max_length,
            padding="max_length",
        )

    tokenized = dataset.map(tokenize, batched=False)

    model = AutoModelForCausalLM.from_pretrained(args.model)
    module_names = {name for name, _ in model.named_modules()}
    if any(name.endswith("q_proj") for name in module_names):
        target_modules = ["q_proj", "v_proj"]
        fan_in_fan_out = False
    elif any(name.endswith("c_attn") for name in module_names):
        target_modules = ["c_attn"]
        fan_in_fan_out = True
    else:
        target_modules = ["c_proj"]
        fan_in_fan_out = False

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
        fan_in_fan_out=fan_in_fan_out,
    )
    model = get_peft_model(model, lora_config)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        save_strategy="epoch",
        eval_strategy="epoch",
        report_to="none",
        fp16=False,
        bf16=False,
        use_cpu=not torch.cuda.is_available(),
        do_train=True,
        do_eval=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    trainer.train()
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))


if __name__ == "__main__":
    main()
