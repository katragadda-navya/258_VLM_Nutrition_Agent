🥗 VitaLens – A Vision-Language Food Recognition & Nutrition Agent

VitaLens is a full-stack Vision-Language Model (VLM) application that recognizes meals from images, estimates portion size, and retrieves grounded nutrition information using the USDA FoodData Central API.
It integrates modern VLMs (Qwen-VL, LLaVA, MiniCPM, GPT-4o) with real-world data sources and exposes a clean web interface built with FastAPI and React/Vite.

🌟 Key Capabilities

Vision-Language meal understanding
Identifies the most likely dish from a food photo and provides a confidence score.

Portion size estimation
Predicts approximate grams based solely on image content.

Grounded nutrient lookup
Uses the USDA FDC API to fetch calories, macros (protein, fat, carbohydrates), fiber, and sodium.

Personalized dietary guidance
Generates concise, human-readable nutrition tips tailored to the predicted meal.

Multiple model backends
Supports local Ollama models (qwen3-vl:8b, llava:7b-v1.6, MiniCPM-v2.6) and OpenAI VLMs (gpt-4o-mini, gpt-4o).

React UI with interactive visualization
Upload an image, select a model, and instantly view nutrition results, FDC matches, and raw JSON for debugging.

🏗️ System Architecture

FOOD_VLM_FASTAPI_REACT/
│
├── backend/
│   └── app/
│       ├── main.py        # API endpoints (analyze, smoke tests, USDA calls)
│       ├── vlm.py         # VLM integration (Ollama + OpenAI)
│       └── fdc.py         # USDA FoodData Central wrapper
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main UI for upload + results dashboard
│   │   └── lib/api.js     # fetchWithTimeout + form uploads
│   └── package.json
│
├── .env
└── README.md


🧠 Backend (FastAPI)

Implements the /api/analyze pipeline:
Accept image upload
Route to the chosen VLM backend
Normalize dish label
Query USDA API
Scale nutrient values to predicted grams
Return structured JSON with nutrients, tips, and timing breakdowns

💻 Frontend (React + Vite)

Switch between Ollama / OpenAI
Live image preview
Display dish name, portion, nutrition table, tips, and raw JSON
Includes a robust timeout wrapper to handle larger models
