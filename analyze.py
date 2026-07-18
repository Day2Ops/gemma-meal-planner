"""Gemma4 Vision Meal Planner — analyze ingredient photos and produce a 7-day meal plan."""

import argparse
import json
import sys
from pathlib import Path

from planner import DEFAULT_MODEL_PATH, generate_meal_plan, load_saved_preferences

DEFAULT_IMAGE_PATH = str((Path(__file__).resolve().parent / ".." / "fridge.jpg").resolve())


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze ingredient photos and generate a 7-day meal plan."
    )
    parser.add_argument(
        "image",
        nargs="*",
        default=[DEFAULT_IMAGE_PATH],
        help=f"Path(s) to ingredient image file(s) (default: {DEFAULT_IMAGE_PATH})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_PATH,
        help=f"MLX model path or HF repo (default: {DEFAULT_MODEL_PATH})",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=2048, help="Max tokens to generate"
    )
    parser.add_argument(
        "--family-preferences",
        default=load_saved_preferences(),
        help='Family preferences/context (default from memory, e.g. "2 adults, 1 child")',
    )
    parser.add_argument(
        "--additional-feedback",
        default="",
        help="Extra feedback to refine the proposed weekly plan",
    )
    parser.add_argument(
        "--plan-approved",
        action="store_true",
        help="Mark plan as approved so the model returns shopping needs",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose generation progress output",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("Generating meal plan …", file=sys.stderr)
    try:
        parsed = generate_meal_plan(
            image_paths=args.image,
            family_preferences=args.family_preferences,
            additional_feedback=args.additional_feedback,
            plan_approved=args.plan_approved,
            model_path=args.model,
            max_tokens=args.max_tokens,
            verbose=args.verbose,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        print(json.dumps(parsed, indent=2))
    except BrokenPipeError:
        sys.exit(0)


if __name__ == "__main__":
    main()
