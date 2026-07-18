"""Gemma4 Vision Meal Planner — analyze a fridge photo and produce a 7-day meal plan."""

import argparse
import json
import sys

MODEL_PATH = "mlx-community/gemma-4-e2b-it-4bit"

PROMPT = """Look at this fridge/pantry image and respond with ONLY valid JSON — no markdown, no code fences, no extra text.

The JSON must have exactly this structure:
{
  "visible_ingredients": ["<ingredient>", ...],
  "meal_plan": {
    "monday":    {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"},
    "tuesday":   {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"},
    "wednesday": {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"},
    "thursday":  {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"},
    "friday":    {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"},
    "saturday":  {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"},
    "sunday":    {"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>"}
  },
  "missing_ingredients": ["<ingredient>", ...]
}

Base the meal plan only on the visible ingredients. List any extra ingredients each meal would need in missing_ingredients."""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze a fridge/pantry photo and generate a 7-day meal plan."
    )
    parser.add_argument("image", help="Path to the fridge/pantry image file")
    parser.add_argument(
        "--model",
        default=MODEL_PATH,
        help=f"MLX model path or HF repo (default: {MODEL_PATH})",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=2048, help="Max tokens to generate"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose generation progress output",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config

    print(f"Loading model {args.model} …", file=sys.stderr)
    model, processor = load(args.model)
    config = load_config(args.model)

    formatted_prompt = apply_chat_template(
        processor, config, PROMPT, num_images=1
    )

    print("Generating meal plan …", file=sys.stderr)
    output = generate(
        model,
        processor,
        formatted_prompt,
        image=args.image,
        temperature=0.0,
        max_tokens=args.max_tokens,
        verbose=not args.quiet,
    )

    # GenerationResult has a .text attribute
    text = (output.text if hasattr(output, "text") else str(output)).strip()
    try:
        parsed = json.loads(text)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print("Warning: model output is not valid JSON — raw output follows:", file=sys.stderr)
        print(text)
        sys.exit(1)


if __name__ == "__main__":
    main()
