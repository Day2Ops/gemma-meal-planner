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
    additional_feedback: str,
    plan_approved: bool,
    plan_controls_visible: bool,
    model_path: str,
    max_tokens: int,
    show_raw_on_error: bool,
) -> tuple[
    Any, Any, Any, Any, Any, Any, str, Any, Any, bool
]:
    if image_files is None:
        raise gr.Error("Please upload at least one ingredient photo.")

    paths = image_files if isinstance(image_files, list) else [image_files]
    if not paths:
        raise gr.Error("Please upload at least one ingredient photo.")

    save_preferences(family_preferences)
    effective_feedback = additional_feedback if plan_controls_visible else ""
    effective_plan_approved = plan_approved if plan_controls_visible else False
    try:
        result = generate_meal_plan(
            image_paths=paths,
            family_preferences=family_preferences,
            additional_feedback=effective_feedback,
            plan_approved=effective_plan_approved,
            model_path=model_path,
            max_tokens=max_tokens,
            verbose=False,
        )
        identified_ingredients = result.get("identified_ingredients", [])
        weekly_meal_plan = result.get("weekly_meal_plan", [])
        shopping_list = result.get("shopping_list", [])
        return (
            identified_ingredients,
            weekly_meal_plan,
            shopping_list,
            gr.update(visible=False, value=""),
            gr.update(visible=False, value=False),
            gr.update(visible=False, value=""),
            "",
            gr.update(visible=True),
            gr.update(visible=True),
            True,
        )
    except ModelOutputError as exc:
        raw = exc.raw_output or "<no raw output captured>"
        return (
            [],
            [],
            [],
            gr.update(visible=True, value=f"ERROR: {exc}"),
            gr.update(visible=True),
            gr.update(visible=show_raw_on_error, value=raw if show_raw_on_error else ""),
            raw,
            gr.update(visible=plan_controls_visible),
            gr.update(visible=plan_controls_visible),
            plan_controls_visible,
        )
    except ValueError as exc:
        return (
            [],
            [],
            [],
            gr.update(visible=True, value=f"ERROR: {exc}"),
            gr.update(visible=False, value=False),
            gr.update(visible=False, value=""),
            "",
            gr.update(visible=plan_controls_visible),
            gr.update(visible=plan_controls_visible),
            plan_controls_visible,
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
            additional_feedback = gr.Textbox(
                label="Additional feedback to refine the plan",
                lines=2,
                placeholder="Example: less spicy dinners, more pasta, quicker weekday meals",
                visible=False,
            )
            plan_approved = gr.Checkbox(
                label="Plan approved (generate shopping list)",
                value=False,
                visible=False,
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
            identified_ingredients_output = gr.JSON(label="identified_ingredients")
            weekly_meal_plan_output = gr.JSON(label="weekly_meal_plan")
            shopping_list_output = gr.JSON(label="shopping_list")
            status_output = gr.Textbox(label="Status", lines=3, interactive=False, visible=False)
            raw_output = gr.Textbox(
                label="Raw model output (error mode)",
                lines=14,
                interactive=False,
                visible=False,
            )
            raw_output_cache = gr.State("")
            plan_controls_visible = gr.State(False)

    submit.click(
        fn=run_planner,
        inputs=[
            image_files,
            family_preferences,
            additional_feedback,
            plan_approved,
            plan_controls_visible,
            model_path,
            max_tokens,
            show_raw_on_error,
        ],
        outputs=[
            identified_ingredients_output,
            weekly_meal_plan_output,
            shopping_list_output,
            status_output,
            show_raw_on_error,
            raw_output,
            raw_output_cache,
            additional_feedback,
            plan_approved,
            plan_controls_visible,
        ],
    )
    show_raw_on_error.change(
        fn=toggle_raw_output,
        inputs=[show_raw_on_error, raw_output_cache],
        outputs=[raw_output],
    )


if __name__ == "__main__":
    demo.launch()
