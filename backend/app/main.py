# backend/app/main.py
import os, io, time
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from .rag import rag_query, build_query_from_nutrition
from .vlm import classify, _clean_query  # helper for sanitizing labels
from .fdc import (
    FDCClient,
    pick_best_food,
    extract_serving,
    summarize_macros,
    tips_from_profile,
)

load_dotenv()

app = FastAPI(title="VLM Nutrition Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/debug_openai")
def debug_openai():
    return {
        "OPENAI_API_KEY_present": bool(os.getenv("OPENAI_API_KEY")),
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL"),
    }

# --- VLM only smoke test (no USDA) ---
@app.post("/api/vlm_smoke")
async def vlm_smoke(
    image: UploadFile = File(...),
    backend: str = Form("ollama"),
    model: Optional[str] = Form(None),
):
    try:
        img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")

    try:
        label, portion_g, conf, trace0 = classify(img, backend=backend, model=model)
        raw = trace0.get("raw")
        raw_text = (raw.get("message", {}) or {}).get("content") if isinstance(raw, dict) else None
        return {
            "label": label,
            "portion_g": portion_g,
            "confidence": conf,
            "raw_text": raw_text or trace0.get("raw_text"),
            "trace_backend": trace0.get("backend"),
            "requested_backend": backend,
            "requested_model": model,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VLM error: {repr(e)}")

# --- USDA only smoke test (no VLM) ---
@app.get("/api/usda_search")
def usda_search(q: str):
    try:
        client = FDCClient()
        s = client.search(q, page_size=5)
        return s
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"USDA error: {e}")

# --- Full pipeline: VLM + USDA + RAG ---
@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    backend: str = Form("ollama"),
    model: Optional[str] = Form(None),
):
    # --- Load image ---
    try:
        img = Image.open(io.BytesIO(await image.read())).convert("RGB")
    except Exception:
        return JSONResponse({"error": "Invalid image"}, status_code=400)

    # --- Step 1: Vision-language inference ---
    try:
        t0 = time.time()
        label, portion_g, conf, trace0 = classify(img, backend=backend, model=model)
        t_vlm = time.time() - t0
    except Exception as e:
        return JSONResponse({"error": f"VLM error: {e}"}, status_code=502)

    # Clean up the label for USDA queries
    safe_query = _clean_query(label)

    # --- Step 2: USDA lookup ---
    client = None
    try:
        client = FDCClient()
        t1 = time.time()
        search = client.search(safe_query, page_size=15)
    except Exception:
        # retry with fallback query (first token)
        fallback = safe_query.split()[0] if safe_query.split() else safe_query
        try:
            client = FDCClient()
            search = client.search(fallback, page_size=10)
        except Exception as e2:
            return JSONResponse({"error": f"USDA lookup failed: {e2}"}, status_code=502)

    best = pick_best_food(search)
    if not best:
        return {
            "label": label,
            "portion_g": portion_g,
            "confidence": conf,
            "fdc_match": None,
            "timings_s": {"vlm": round(t_vlm, 3), "fdc": 0.0},
            "trace": {"vlm": trace0},
            "requested_backend": backend,
            "requested_model": model,
        }

    try:
        fdc_id = int(best["fdcId"])
        details = client.details(fdc_id)
        t_fdc = time.time() - t1
    except Exception as e:
        return JSONResponse({"error": f"USDA details fetch failed: {e}"}, status_code=502)

    # --- Step 3: Nutrition + scaling ---
    serving_amt, serving_unit = extract_serving(details)
    profile = summarize_macros(details)
    scaled = profile.copy()
    if serving_unit and isinstance(serving_unit, str) and serving_unit.lower() == "g" and serving_amt:
        try:
            factor = float(portion_g) / float(serving_amt)
        except Exception:
            factor = 1.0
        for k in scaled:
            try:
                scaled[k] = round((scaled[k] or 0.0) * factor, 2)
            except Exception:
                pass
        serving_used = f"{portion_g:.0f} g (scaled from {serving_amt:.0f} g)"
    else:
        serving_used = f"{serving_amt} {serving_unit} (unscaled)"

    # --- Step 4: Tips (heuristic + RAG) ---
    # Existing heuristic tips
    base_tips = tips_from_profile(scaled)

    # RAG-based guidance
    try:
        rag_q = build_query_from_nutrition(label, scaled)
        rag_results = rag_query(rag_q, top_k=3)
        rag_tips = [r["text"] for r in rag_results]
    except Exception:
        rag_results = []
        rag_tips = []

    combined_tips = base_tips + rag_tips

    # --- Step 5: Compose response ---
    return {
        "label": label,
        "portion_g": portion_g,
        "confidence": conf,
        "serving_used": serving_used,
        "nutrition": scaled,
        "tips": combined_tips,
        "fdc_match": {
            "fdcId": fdc_id,
            "description": details.get("description"),
            "dataType": details.get("dataType"),
        },
        "timings_s": {"vlm": round(t_vlm, 3), "fdc": round(t_fdc, 3)},
        "trace": {"vlm": trace0, "rag": rag_results},
        "requested_backend": backend,
        "requested_model": model,
    }
