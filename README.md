# Gemma Meal Planner (MLX + Gradio)

Local multimodal meal planner using Gemma 4 on Apple Silicon with `uv`.

## Setup

```bash
uv sync
```

## CLI

```bash
uv run analyze.py fridge1.jpg fridge2.jpg \
  --family-preferences "2 adults, 1 child; no peanuts" \
  | python3 -m json.tool
```

## Gradio UI

```bash
uv run app.py
```

The UI sends both:
1. Family context/preferences text
2. Uploaded ingredient photos

to the local MLX model (`mlx-community/gemma-4-e2b-it-4bit` by default).

Family preferences are remembered in `.family_preferences.json` and preloaded on next launch.

Prompt template is in `prompts/meal_planner_prompt.txt` so you can iterate on it without touching Python code.

If parsing fails, enable **"Show raw model output when generation fails"** in the UI to inspect the exact model response.
