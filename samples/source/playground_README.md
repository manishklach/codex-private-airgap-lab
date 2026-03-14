# Tarot 3-Card Picker

A standalone Python script that generates an interactive, single-file HTML tarot application.

The app lays out the full 78-card deck, lets users draw **exactly 3 cards**, and produces a structured **Past / Present / Future** predictive reading.

## Features

- Full 78-card tarot deck (Major + Minor Arcana)
- Interactive card selection (pick 3 cards only)
- Automatic upright/reversed orientation handling
- Staged reading output:
  - Past
  - Present
  - Future
- Predictive synthesis engine with:
  - Pattern summary (major count, reversed count, dominant element)
  - Trajectory analysis
  - Likely path vs risk path
  - Domain outlooks (relationships, career, finances, wellbeing)
  - Action guidance + confidence line
- Theme presets:
  - Mint
  - Parchment
  - White
- Focus modes:
  - General
  - Love
  - Career
  - Money
- Smooth UI animation with `prefers-reduced-motion` support
- No framework/dependencies required for runtime output (just open generated HTML)

## Project Structure

- `tarot_picker.py` - Python generator script
- `tarot_picker.html` - Generated interactive HTML output

## Requirements

- Python 3.9+

## Install

1. Clone the repository:

```bash
git clone https://github.com/manishklach/tarot-predictive-picker.git
cd tarot-predictive-picker
```

2. Verify Python:

```bash
python --version
```

3. Generate the HTML app:

```bash
python tarot_picker.py
```

4. Open the generated file:

- `tarot_picker.html`

Or generate and open directly:

```bash
python tarot_picker.py --open
```

## Quick Start

1. Generate the HTML:

```bash
python tarot_picker.py
```

2. Open the generated file:

- `tarot_picker.html`

Or generate and open automatically:

```bash
python tarot_picker.py --open
```

## Usage

1. Choose a **Theme** and **Focus**.
2. Click cards to pick 3.
3. After the third pick:
   - deck collapses to selected cards
   - predictive reading appears in staged layout
4. Click **Reset & Shuffle** to start a new reading.

## Command Options

```bash
python tarot_picker.py --output custom_name.html --open
```

- `--output` : output HTML path (default: `tarot_picker.html`)
- `--open` : open generated file in default browser

## How Prediction Works (High-Level)

The engine is deterministic and rule-based (no external LLM calls):

- card archetype metadata (major/minor)
- position weighting (past/present/future)
- orientation effects (upright/reversed)
- suit/element balancing and compatibility
- focus-mode domain weighting

It outputs a symbolic forecast intended for reflection and guidance.

## Customization

You can easily tweak:

- card interpretations (`MAJOR_META`, `RANK_META`, `SUIT_META`)
- scoring weights (`POSITION_WEIGHTS`, focus weights)
- UI themes (CSS variables under `body[data-theme=...]`)
- layout/animations (CSS keyframes and classes)

## Disclaimer

This application provides symbolic and interpretive guidance for personal reflection.
It is not deterministic prediction and should not replace professional advice (medical, legal, financial, or mental health).

## License

If you are publishing to GitHub, add your preferred license (for example: MIT) in a `LICENSE` file.
