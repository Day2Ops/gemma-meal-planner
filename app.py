"""Gradio UI for local Gemma 4 meal planning with ingredient photos."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr

from planner import (
    DEFAULT_MODEL_PATH,
    ModelOutputError,
    generate_meal_plan,
    load_saved_preferences,
    save_preferences,
)

DEFAULT_IMAGE_PATH = (Path(__file__).resolve().parent / ".." / "fridge.jpg").resolve()


def _default_images() -> list[str] | None:
    if DEFAULT_IMAGE_PATH.exists():
        return [str(DEFAULT_IMAGE_PATH)]
    return None


def run_planner(
    image_files: list[str] | str | None,
    family_preferences: str,
    model_path: str,
    max_tokens: int,
    show_raw_on_error: bool,
) -> tuple[dict[str, Any], str, Any, Any, str]:
    if image_files is None:
        raise gr.Error("Please upload at least one ingredient photo.")

    paths = image_files if isinstance(image_files, list) else [image_files]
    if not paths:
        raise gr.Error("Please upload at least one ingredient photo.")

    save_preferences(family_preferences)
    try:
        result = generate_meal_plan(
            image_paths=paths,
            family_preferences=family_preferences,
            model_path=model_path,
            max_tokens=max_tokens,
            verbose=False,
        )
        return (
            result,
            "",
            gr.update(visible=False, value=False),
            gr.update(visible=False, value=""),
            "",
        )
    except ModelOutputError as exc:
        raw = exc.raw_output or "<no raw output captured>"
        return (
            {},
            f"ERROR: {exc}",
            gr.update(visible=True),
            gr.update(visible=show_raw_on_error, value=raw if show_raw_on_error else ""),
            raw,
        )
    except ValueError as exc:
        return (
            {},
            f"ERROR: {exc}",
            gr.update(visible=False, value=False),
            gr.update(visible=False, value=""),
            "",
        )


def toggle_raw_output(show_raw_on_error: bool, raw_output_cache: str) -> Any:
    visible = show_raw_on_error and bool(raw_output_cache)
    return gr.update(visible=visible, value=raw_output_cache if visible else "")


with gr.Blocks(title="Gemma 4 Meal Planner (MLX)") as demo:
    gr.Markdown("## Gemma 4 Meal Planner (local MLX)")
    gr.Markdown(
        "Upload ingredient photos and provide family context (for example: `2 adults, 1 child`)."
    )

    with gr.Row():
        with gr.Column():
            family_preferences = gr.Textbox(
                label="Family preferences/context",
                value=load_saved_preferences(),
                lines=3,
                placeholder="2 adults, 1 child; no peanuts; budget-friendly dinners",
            )
            model_path = gr.Textbox(
                label="Model",
                value=DEFAULT_MODEL_PATH,
            )
            max_tokens = gr.Slider(
                label="Max tokens",
                minimum=512,
                maximum=4096,
                step=128,
                value=3072,
            )
            show_raw_on_error = gr.Checkbox(
                label="Show raw model output when generation fails",
                value=False,
                visible=False,
            )
            image_files = gr.File(
                label="Ingredient photos",
                file_count="multiple",
                file_types=["image"],
                type="filepath",
                value=_default_images(),
            )
            submit = gr.Button("Generate 7-day plan", variant="primary")
        with gr.Column():
            result_json = gr.JSON(label="Meal plan JSON")
            status_output = gr.Textbox(label="Status", lines=3, interactive=False)
            raw_output = gr.Textbox(
                label="Raw model output (error mode)",
                lines=14,
                interactive=False,
                visible=False,
            )
            raw_output_cache = gr.State("")

    submit.click(
        fn=run_planner,
        inputs=[image_files, family_preferences, model_path, max_tokens, show_raw_on_error],
        outputs=[result_json, status_output, show_raw_on_error, raw_output, raw_output_cache],
    )
    show_raw_on_error.change(
        fn=toggle_raw_output,
        inputs=[show_raw_on_error, raw_output_cache],
        outputs=[raw_output],
    )


if __name__ == "__main__":
    demo.launch()
