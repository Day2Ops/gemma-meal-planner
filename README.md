# 🍳 Family Meal Saver: Gemma 4 Meal Planner 

**Built for the GDG Faro Gemma Hackathon 2026** [2]

Meal planning is often a stressful, time-consuming daily chore for parents, frequently resulting in unused ingredients and food waste. **Family Meal Saver** is a local, AI-powered application designed to eliminate this stress while making meal planning an engaging, fun activity for kids to help their parents with. 

By allowing a child to simply snap a picture of the ingredients currently in the fridge or pantry, the app instantly proposes a full, tailored 7-day family meal plan and generates a precise shopping list for the missing items.

## 🚀 The Gemma 4 Superpowers We Leveraged

To solve this problem natively and securely, this app utilizes three core Gemma 4 capabilities:
*   **Local Frontier Intelligence:** Runs entirely locally on Apple Silicon (M1 MacBook Pro) without relying on cloud APIs. We use the quantized `mlx-community/gemma-4-e2b-it-4bit` model for laptop efficiency [1].
*   **Multimodal Understanding:** The app accepts photos of your fridge or table [1]. Gemma 4 analyzes the image to identify usable food items and incorporates them into the recipes.
*   **Native Function Calling (Structured Output):** Gemma 4 processes the family composition alongside the identified ingredients to generate a strict, parsed weekly plan and a dedicated shopping list.

## 🛠 Tech Stack
*   **Model:** Gemma 4 QAT (`mlx-community/gemma-4-e2b-it-4bit`) via Apple **MLX** [1]
*   **Frontend UI:** **Gradio** for a simple, mobile-friendly interface [1]
*   **Dependency Management:** **uv** for blazing-fast local Python setup [1]

## 💡 How It Works (The Flow)

The Gradio UI sends both the family context/preferences and the uploaded ingredient photos to the local MLX model [1].

1.  **Identify Ingredients:** The model scans the uploaded photo for usable items [2].
2.  **Propose Weekly Plan:** A kid-friendly, 7-day meal plan is generated using the available ingredients [2].
3.  **Refine:** The user can provide additional feedback to tweak the meals [2].
4.  **Generate Shopping Needs:** Once the plan is approved, the app finalizes the missing items needed for the week [2].

*Note: Family preferences are automatically remembered in `.family_preferences.json` and preloaded on your next launch [1]. If you want to tweak the AI's behavior, the prompt template is cleanly separated in `prompts/meal_planner_prompt.txt` so you can iterate without touching the Python code [1].*

## ⚙️ Setup & Installation

**Prerequisites:** Apple Silicon Mac (M1/M2/M3) and `uv` installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/Day2Ops/gemma-meal-planner.git
   cd gemma-meal-planner
2. Install dependencies and run via uv:  
`uv run app.py`  
3. Open the Gradio App:  
`Running on local URL:  http://127.0.0.1:7861`

🐛 Troubleshooting
If the structured JSON parsing fails during generation, simply enable "Show raw model output when generation fails" in the Gradio UI to inspect the exact model response and debug the output.