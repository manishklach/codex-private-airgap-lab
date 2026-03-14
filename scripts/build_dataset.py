from __future__ import annotations

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "samples" / "source"
DATA_DIR = ROOT / "data"


SYSTEM_PROMPTS = {
    "explain": "You are an expert assistant for a private local code and document workspace.",
    "summarize": "You summarize private technical and structured documents clearly and conservatively.",
    "refactor": "You are a careful refactoring assistant for a private local Python codebase.",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def clip(text: str, limit: int = 2200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n..."


def short_summary(path: Path, text: str) -> str:
    if path.suffix == ".py":
        return (
            f"{path.name} is a Python script in the sample corpus. "
            "It contains practical implementation logic that can be explained, summarized, "
            "or refactored as part of a local fine-tuning workflow."
        )
    return (
        f"{path.name} is a structured markdown or text document from the sample corpus. "
        "It contains domain-specific content that can be summarized or answered from directly."
    )


def make_examples(path: Path) -> list[dict]:
    text = read_text(path)
    excerpt = clip(text)
    examples: list[dict] = []

    examples.append(
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS["summarize"]},
                {
                    "role": "user",
                    "content": f"Summarize the following private file named {path.name}:\n\n{excerpt}",
                },
                {"role": "assistant", "content": short_summary(path, text)},
            ]
        }
    )

    if path.suffix == ".py":
        examples.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPTS["explain"]},
                    {
                        "role": "user",
                        "content": f"Explain what this Python file does and identify the main responsibilities:\n\n{excerpt}",
                    },
                    {
                        "role": "assistant",
                        "content": (
                            f"The file {path.name} is a Python implementation artifact in the local sample workspace. "
                            "Its main responsibilities are defined by the functions, imports, and path handling visible "
                            "in the excerpt. A correct answer should explain the data flow, external dependencies, and "
                            "where filesystem or network behavior is introduced."
                        ),
                    },
                ]
            }
        )
        examples.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPTS["refactor"]},
                    {
                        "role": "user",
                        "content": f"Refactor the following Python excerpt for readability without changing behavior:\n\n{excerpt}",
                    },
                    {
                        "role": "assistant",
                        "content": (
                            "A safe refactor should preserve behavior, keep imports explicit, separate filesystem helpers "
                            "from network helpers, and add only minimal comments where the control flow is non-obvious."
                        ),
                    },
                ]
            }
        )
    else:
        examples.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPTS["explain"]},
                    {
                        "role": "user",
                        "content": f"Answer questions grounded only in this private document excerpt from {path.name}:\n\n{excerpt}",
                    },
                    {
                        "role": "assistant",
                        "content": (
                            f"Answers for {path.name} should stay grounded in the document text, avoid inventing facts, "
                            "and clearly separate explicit document content from assumptions."
                        ),
                    },
                ]
            }
        )

    return examples


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    paths = sorted(p for p in SOURCE_DIR.iterdir() if p.is_file())
    all_examples: list[dict] = []
    for path in paths:
        all_examples.extend(make_examples(path))

    random.Random(42).shuffle(all_examples)

    total = len(all_examples)
    train_end = max(1, int(total * 0.7))
    valid_end = max(train_end + 1, int(total * 0.85)) if total > 2 else total

    train_rows = all_examples[:train_end]
    valid_rows = all_examples[train_end:valid_end]
    test_rows = all_examples[valid_end:]

    if not valid_rows and train_rows:
        valid_rows = [train_rows.pop()]
    if not test_rows and valid_rows:
        test_rows = [valid_rows.pop()]

    write_jsonl(DATA_DIR / "train.jsonl", train_rows)
    write_jsonl(DATA_DIR / "valid.jsonl", valid_rows)
    write_jsonl(DATA_DIR / "test.jsonl", test_rows)

    summary = {
        "source_files": [p.name for p in paths],
        "train_examples": len(train_rows),
        "valid_examples": len(valid_rows),
        "test_examples": len(test_rows),
    }
    (DATA_DIR / "dataset_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

