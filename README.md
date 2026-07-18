# 🍳 Family Meal Saver: Gemma 4 Meal Planner

**Built for the GDG Faro Gemma Hackathon 2026**

Family Meal Saver is a local, AI-powered family meal planner that transforms fridge photos into a kid-friendly, 7-day dinner plan and an optional shopping list for missing ingredients.

## Key Points

- Runs locally on Apple Silicon using a quantized Gemma 4 model via MLX
- Multimodal: accepts photos of ingredients and family preferences
- Outputs a strict JSON object (see "JSON Output Schema" below) so downstream tooling can parse results reliably

## Tech Stack

- Model: `mlx-community/gemma-4-e2b-it-4bit` (via `mlx_vlm`)
- UI: `gradio`
- Dependency/runtime helper: `uv`

## How it works

1. Upload ingredient photos and provide family context.
2. The model identifies usable ingredients.
3. It proposes a 7-day dinner plan that prioritizes available items.
4. If the plan is approved, the app returns a shopping list of missing items.

Preferences are saved to `.family_preferences.json`. The prompt template that controls generation is in `prompts/meal_planner_prompt.txt`.

## Setup & Quick Run

Prerequisites: Apple Silicon Mac (M1/M2/M3) and `uv` installed.

```bash
git clone https://github.com/Day2Ops/gemma-meal-planner.git
cd gemma-meal-planner
uv run app.py
```

Open the Gradio app at the URL shown in the console (typically `http://127.0.0.1:7861`).

## CLI Usage

The repository includes a CLI wrapper `analyze.py` for scripted runs.

Run:

```bash
uv run python gemma-meal-planner/analyze.py [IMAGE ...] [--model MODEL] [--max-tokens N] [--family-preferences "..."] [--additional-feedback "..."] [--plan-approved] [--verbose]
```

Flags:

- `--model`: Model path or HF repo (default: `mlx-community/gemma-4-e2b-it-4bit`)
- `--max-tokens`: Maximum tokens to generate (default: 2048)
- `--family-preferences`: Family context (default loaded from `.family_preferences.json`)
- `--additional-feedback`: Extra instructions to refine the plan
- `--plan-approved`: Mark plan as approved so the model includes a shopping list
- `--verbose`: Show generation progress

Example:

```bash
uv run python gemma-meal-planner/analyze.py fridge.jpg --family-preferences "2 adults, 1 child" --plan-approved
```

## JSON Output Schema

The model is instructed to emit a strict JSON object. The playground prompt (`prompts/meal_planner_prompt.txt`) defines the expected schema; a minimal reproduction is below:

```json
{
   "plan_status": "proposal|final",
   "identified_ingredients": ["list", "of", "found", "items"],
   "weekly_meal_plan": [
      {
         "day": "Monday",
         "meal_name": "Fun Veggie Tacos",
         "description": "Crunchy tacos packed with beans, cheese, and tomatoes!",
         "ingredients_used_from_fridge": ["tomatoes", "cheese"],
         "ingredients_needed": ["taco shells", "black beans"]
      }
   ],
   "feedback_request": "Question(s) to refine the plan",
   "shopping_list": ["taco shells", "black beans"]
}
```

The application (`planner.py`) parses model output robustly (direct JSON parse → extract JSON-like substrings → autocomplete truncated JSON → request model-assisted repair) and raises a readable error when parsing fails.

## Troubleshooting

- If parsing fails, enable "Show raw model output when generation fails" in the Gradio UI to inspect the raw text.
- `mlx_vlm.generate` may return a GenerationResult object — use `output.text` (or `_extract_text()` helper) to get the text content.

---

For development details, see `planner.py`, `app.py`, `analyze.py`, and the `prompts/` folder.