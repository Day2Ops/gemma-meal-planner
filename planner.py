"""Shared MLX meal-planner logic for CLI and Gradio UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mlx_vlm import generate, load
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

DEFAULT_MODEL_PATH = "mlx-community/gemma-4-e2b-it-4bit"
PREFERENCES_PATH = Path(__file__).resolve().parent / ".family_preferences.json"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "meal_planner_prompt.txt"

_MODEL_CACHE: dict[str, tuple[Any, Any, Any]] = {}


class ModelOutputError(ValueError):
    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


def load_saved_preferences() -> str:
    default_preferences = "2 adults, 1 child"
    if not PREFERENCES_PATH.exists():
        return default_preferences

    parsed = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
    if isinstance(parsed, dict) and isinstance(parsed.get("family_preferences"), str):
        return parsed["family_preferences"]
    return default_preferences


def save_preferences(family_preferences: str) -> None:
    payload = {"family_preferences": family_preferences.strip()}
    PREFERENCES_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _get_model_parts(model_path: str) -> tuple[Any, Any, Any]:
    if model_path not in _MODEL_CACHE:
        model, processor = load(model_path)
        config = load_config(model_path)
        _MODEL_CACHE[model_path] = (model, processor, config)
    return _MODEL_CACHE[model_path]


def _extract_text(output: Any) -> str:
    text = output.text if hasattr(output, "text") else str(output)
    return text.strip()


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if "```" not in cleaned:
        return cleaned

    lines = cleaned.splitlines()
    fence_start = next(
        (idx for idx, line in enumerate(lines) if line.strip().startswith("```")), None
    )
    if fence_start is None:
        return cleaned
    fence_end = next(
        (
            idx
            for idx in range(fence_start + 1, len(lines))
            if lines[idx].strip().startswith("```")
        ),
        None,
    )
    if fence_end is None:
        body = lines[fence_start + 1 :]
    else:
        body = lines[fence_start + 1 : fence_end]
    return "\n".join(body).strip()


def _iter_json_object_candidates(text: str):
    for start in (idx for idx, char in enumerate(text) if char == "{"):
        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(text)):
            char = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    yield text[start : idx + 1]
                    break


def _autocomplete_json(text: str) -> str | None:
    stack: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in ("}", "]"):
            if not stack:
                return None
            expected = stack.pop()
            if char != expected:
                return None

    suffix = '"' if in_string else ""
    while stack:
        suffix += stack.pop()
    return (text + suffix).strip()


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fences(text)
    if not cleaned:
        raise ValueError("Model output was empty. Try again or increase max tokens.")

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Model JSON output must be an object.")
        return parsed
    except json.JSONDecodeError:
        pass

    for candidate in _iter_json_object_candidates(cleaned):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    first_object_start = cleaned.find("{")
    if first_object_start != -1:
        completed = _autocomplete_json(cleaned[first_object_start:])
        if completed:
            try:
                parsed = json.loads(completed)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

    if cleaned.startswith("{") and cleaned.count("{") > cleaned.count("}"):
        raise ValueError(
            "Model output appears truncated before closing JSON. Try increasing max tokens."
        )

    preview = cleaned[:240].replace("\n", "\\n")
    raise ValueError(f"Model output is not valid JSON. Output preview: {preview}")


def _load_prompt(family_preferences: str) -> str:
    if not PROMPT_PATH.exists():
        raise ValueError(f"Prompt file not found: {PROMPT_PATH}")

    template = PROMPT_PATH.read_text(encoding="utf-8")
    if "{family_preferences}" not in template:
        raise ValueError("Prompt file must include {family_preferences} placeholder.")
    return template.replace("{family_preferences}", family_preferences.strip())


def _repair_to_json_with_model(
    model: Any,
    processor: Any,
    config: Any,
    raw_output: str,
    verbose: bool,
) -> dict[str, Any]:
    repair_prompt = (
        "Convert the following draft into valid JSON only.\n"
        "Do not wrap in markdown or code fences.\n"
        "Preserve the same schema and values as much as possible.\n\n"
        f"{raw_output[:6000]}"
    )
    formatted_prompt = apply_chat_template(processor, config, repair_prompt, num_images=0)
    repaired = generate(
        model,
        processor,
        formatted_prompt,
        temperature=0.0,
        max_tokens=1536,
        verbose=verbose,
    )
    repaired_text = _extract_text(repaired)
    try:
        return _parse_json(repaired_text)
    except ValueError as exc:
        raise ModelOutputError(str(exc), raw_output=repaired_text) from exc


def generate_meal_plan(
    image_paths: list[str],
    family_preferences: str,
    model_path: str = DEFAULT_MODEL_PATH,
    max_tokens: int = 2048,
    verbose: bool = False,
) -> dict[str, Any]:
    if not image_paths:
        raise ValueError("At least one ingredient photo is required.")
    missing_paths = [path for path in image_paths if not Path(path).exists()]
    if missing_paths:
        missing_str = ", ".join(missing_paths)
        raise ValueError(f"Image file(s) not found: {missing_str}")

    model, processor, config = _get_model_parts(model_path)
    prompt = _load_prompt(family_preferences)
    formatted_prompt = apply_chat_template(
        processor, config, prompt, num_images=len(image_paths)
    )

    image_input: str | list[str]
    image_input = image_paths[0] if len(image_paths) == 1 else image_paths

    output = generate(
        model,
        processor,
        formatted_prompt,
        image=image_input,
        temperature=0.0,
        max_tokens=max_tokens,
        verbose=verbose,
    )
    first_text = _extract_text(output)
    try:
        return _parse_json(first_text)
    except ValueError:
        pass

    retry_tokens = min(max_tokens + 1024, 4096)
    if retry_tokens > max_tokens:
        retry_output = generate(
            model,
            processor,
            formatted_prompt,
            image=image_input,
            temperature=0.0,
            max_tokens=retry_tokens,
            verbose=verbose,
        )
        retry_text = _extract_text(retry_output)
        try:
            return _parse_json(retry_text)
        except ValueError:
            first_text = retry_text

    try:
        return _repair_to_json_with_model(model, processor, config, first_text, verbose)
    except ModelOutputError as exc:
        if not exc.raw_output:
            exc.raw_output = first_text
        raise
