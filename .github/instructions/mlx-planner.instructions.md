---
description: "Use when editing planner.py or working on model integration and JSON parsing. Covers model loading, output extraction, and repair flow."
applyTo: "gemma-meal-planner/planner.py"
---

Key points for `planner.py` edits:

- Use `_get_model_parts(model_path)` to load `model, processor, config` and rely on the internal `_MODEL_CACHE`.
- When reading model output, prefer `_extract_text(output)` — many model wrappers return objects where the textual payload is in `.text`.
- The parsing pipeline is intentionally robust: direct `json.loads` of cleaned output, then extraction of JSON-like substrings, then autocomplete-based repair, and finally model-assisted repair via `_repair_to_json_with_model()`.
- If raising or catching `ModelOutputError`, include or inspect `raw_output` for debugging and surface that to interactive UIs.

When modifying prompt construction, update `prompts/meal_planner_prompt.txt` and align the README `JSON Output Schema` if schema changes are made.
