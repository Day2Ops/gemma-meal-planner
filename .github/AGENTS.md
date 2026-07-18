# AGENTS — How assistants and automation should interact with this repo

Purpose: provide concise, actionable context for any automated assistant (editor AI, CI helper, chat agent) working with this project.

Summary
- Project: Local family meal planner using Gemma 4 via `mlx_vlm`.
- Components: `app.py` (Gradio UI), `analyze.py` (CLI), `planner.py` (shared MLX orchestration), `prompts/` (generation templates), `.family_preferences.json` (saved prefs).

Run commands

```bash
uv run app.py
uv run python gemma-meal-planner/analyze.py fridge.jpg
```

Key notes for agents
- The model API (`mlx_vlm.generate`) can return structured objects; extract human text via the `.text` attribute.
- Keep heavy runtime imports (mlx_vlm) inside `if __name__ == "__main__"` or `main()` when adding CLI helpers so `--help` and static analysis work without runtime deps.
- Prompts are in `prompts/meal_planner_prompt.txt` and are the authoritative schema for JSON output.

Where to look
- UI: `app.py`
- Core logic & parsing: `planner.py`
- CLI wrapper: `analyze.py`
- Prompt template: `prompts/meal_planner_prompt.txt`

Verification / quick checks
- `uv run python gemma-meal-planner/analyze.py --help`
- Inspect `prompts/meal_planner_prompt.txt` for expected JSON schema

If making changes that affect the JSON schema, update both `prompts/meal_planner_prompt.txt` and the README `JSON Output Schema` section.
