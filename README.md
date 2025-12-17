🥗 VitaLens – A Vision-Language Food Recognition & Nutrition Agent

The system combines:
A Vision–Language Model (VLM) (local via Ollama or hosted via OpenAI) for:
Dish classification (e.g., “burger_and_fries”)
Portion size estimation (grams)
The USDA FoodData Central (FDC) API for:
Mapping the predicted dish to a real food entry
Retrieving macro-nutrient information
A lightweight RAG component over curated nutrition tips for:
Personalized, human-readable guidance about the meal
A React + Vite frontend with image upload, backend/model selection, and result visualization.

1. High-level architecture
```text
+------------------------+         +------------------------+
|        Frontend        |         |        Backend         |
|  React (Vite) SPA      |  ---->  | FastAPI                |
|                        |   /api  |                        |
| - Image upload         |         |  /api/vlm_smoke        |
| - Backend/model select |         |  /api/usda_search      |
| - Result + tips view   |         |  /api/analyze          |
+------------------------+         +-----------+------------+
                                               |
                                               v
                           +-------------------+-------------------+
                           |     Vision–Language Models (VLM)     |
                           |        (chosen per request)           |
                           |                                       |
                           |   Ollama: qwen3-vl:8b, llava, ...     |
                           |   OpenAI: gpt-4o-mini, gpt-4o, ...    |
                           +-------------------+-------------------+
                                               |
                                               v
                         +---------------------+--------------------+
                         |        USDA FDC + RAG                    |
                         |                                          |
                         | - FDC search + details (macros)          |
                         | - Macro summarization + portion scaling  |
                         | - Heuristic tips (fdc.py)                |
                         | - RAG tips from backend/rag_docs         |
                         +------------------------------------------+
```
3. Features

🔍 Food recognition from images
VLM predicts a short dish label and portion size in grams.
Supports both local VLMs (Ollama) and remote models (OpenAI Vision).

⚖️ Calorie & macro estimation
Uses USDA FoodData Central to find the closest food entry.
Extracts calories, protein, fat, carbs, fiber, sodium, and sugars.
Scales nutrients to the predicted portion size.

💡 Dietary guidance via RAG
Nutrition profile is summarized into:
Heuristic tips (low fiber, high sodium, etc.)
RAG-based tips retrieved from backend/rag_docs using sentence embeddings.

🧪 Evaluation & model comparison
backend/app/eval_food101.py: benchmark script to compare multiple VLM backends on Food-101, reporting:
Top-1 accuracy
Latency per image
Lets you compare, e.g., qwen3-vl:8b vs other Ollama models vs OpenAI models.

🖥️ Simple but complete UI
Upload a food image.
Select backend (ollama or openai) and model.
Inspect prediction, macros, FDC match, timings, and all tips.
Toggle “Show raw” to see the full JSON returned by the backend.

3. Repository layout
```text
258_VLM_Nutrition_Agent/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app and HTTP endpoints
│   │   ├── vlm.py           # VLM wrappers (Ollama + OpenAI)
│   │   ├── fdc.py           # USDA FDC client + macro summarization + tips
│   │   ├── rag.py           # Tiny RAG over backend/rag_docs
│   │   ├── eval_food101.py  # Multi-model evaluation on Food-101
│   ├── rag_docs/            # Short nutrition guidance documents
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx          # React UI
    │   └── lib/api.js       # API client (calls /api/analyze)
    ├── package.json
    └── vite.config.*        # Vite config
```
4. Multi-model evaluation (Food-101)

To compare different VLM backends on a standard dataset, use
backend/app/eval_food101.py.
High-level steps (you may adapt to your environment):
Download or mount the Food-101 dataset.
Edit eval_food101.py to point to the dataset path and configure:
Models to test (e.g. ["qwen3-vl:8b", "llava:7b-v1.6"] for Ollama and/or OpenAI models).

Run:
cd backend
python -m app.eval_food101

The script will:
Run each model on a subset (or full) Food-101 test images.
Log per-model accuracy and average latency per image.
Produce CSV/JSON summaries that you can bring into your report.
This satisfies the “multi-model comparison on one dataset” requirement.

5. RAG nutrition tips

RAG is implemented in backend/app/rag.py using sentence-transformers:
At startup (lazy), all .md/.txt files under backend/rag_docs/ are embedded using all-MiniLM-L6-v2.
When /api/analyze is called, the backend:
Builds a query from the predicted dish name and macro profile.
Retrieves top-K relevant snippets with cosine similarity.
Appends those snippets to the heuristic tips.
You can customize the knowledge base by editing or adding markdown files under backend/rag_docs/.



Inspect prediction, macros, FDC match, timings, and all tips.

Toggle “Show raw” to see the full JSON returned by the backend.
