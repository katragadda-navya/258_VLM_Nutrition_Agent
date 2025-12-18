# backend/app/vlm.py
import os, base64, io, json, re
from typing import Optional
from PIL import Image

# Default model if the client doesn't pass one
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-vl:8b")

def _extract_from_text(text: str):
    """
    Pull out label, portion_grams, confidence from model output.
    Tries JSON first, then regex fallbacks.
    """
    label, portion, conf = None, None, None

    # Try to parse the first JSON-looking block
    m = re.search(r"\{.*\}", text, flags=re.S)
    if m:
        try:
            j = json.loads(m.group(0))
            label = j.get("label") or j.get("dish") or j.get("class")
            portion = j.get("portion_grams")
            conf = j.get("confidence")
        except Exception:
            pass

    # Fallbacks for label
    if not label:
        m = re.search(r'"label"\s*:\s*"([^"]+)"', text, flags=re.I)
        if m:
            label = m.group(1)
    if not label:
        m = re.search(r'label\s*[:=]\s*["\']?([A-Za-z0-9][^"\',\n]+)', text, flags=re.I)
        if m:
            label = m.group(1).strip()

    # Convert label to string if it's a list (some models return lists)
    if isinstance(label, list):
        label = label[0] if label else None
    
    # Ensure label is a string
    if label is not None:
        label = str(label)
    
    # Clean label for USDA
    if label:
        label = _clean_query(label)

    # Defaults if missing or unparsable
    try:
        portion = float(portion) if portion is not None else 250.0
    except Exception:
        portion = 250.0
    try:
        conf = float(conf) if conf is not None else 0.7
    except Exception:
        conf = 0.7

    return label or "unknown", portion, conf

def _clean_query(s: str) -> str:
    """Make a USDA-safe query: strip noise & limit length."""
    # Ensure s is a string (handle lists or other types)
    if isinstance(s, list):
        s = s[0] if s else ""
    s = str(s) if s is not None else ""
    s = s.replace("&", " and ").replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^A-Za-z0-9 /()-]", "", s)
    words = s.split()
    return " ".join(words[:6]) if words else s

# --- Performance helpers ---
def _image_to_b64_fast(image: Image.Image) -> str:
    """Downscale + JPEG encode to reduce tokens and speed up inference."""
    img = image.copy()
    img.thumbnail((1024, 1024))  # cap longest side
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def _image_to_data_url(image: Image.Image) -> str:
    """For OpenAI path: data URL (JPEG)."""
    img = image.copy()
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

# --- Backends ---
def infer_with_ollama(image: Image.Image, model: Optional[str] = None):
    from ollama import Client
    client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    prompt = (
        'Return STRICT JSON only with no extra text. '
        'Schema: {"label": <string>, "portion_grams": <float>, "confidence": <0-1>}. '
        'Prefer Food-101 style labels; if unsure, still pick one best label.'
    )

    b64 = _image_to_b64_fast(image)

    res = client.chat(
        model=(model or DEFAULT_OLLAMA_MODEL),   # pass-through
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [b64],
        }],
        options={
            "temperature": 0.2,
            "num_ctx": 512,                      # smaller context → less compute
            "num_thread": os.cpu_count() or 8,   # use available CPU threads
        },
        keep_alive="30m",  # keep weights in memory to avoid reloads
    )

    text = (res["message"]["content"] or "").strip()
    label, portion, conf = _extract_from_text(text)
    return label, portion, conf, {"backend": "ollama", "raw": res, "raw_text": text}

def infer_with_openai(image: Image.Image, model: str = "gpt-4o-mini"):
    from openai import OpenAI
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # This will show up as a clear error if env isn't loaded
        raise RuntimeError("OPENAI_API_KEY is not set in this process")

    # Force official OpenAI endpoint, ignore OPENAI_BASE_URL env
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1",
    )

    prompt = 'Return STRICT JSON: {"label": <dish>, "portion_grams": <float>, "confidence": <0-1>}'
    res = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_to_data_url(image)}},
            ],
        }],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    
    # Safely extract content
    text = ""
    if res and res.choices and len(res.choices) > 0:
        content = res.choices[0].message.content
        text = (content or "").strip()
    
    # Use _extract_from_text for consistency with Ollama
    label, portion, conf = _extract_from_text(text)
    return (
        label,
        portion,
        conf,
        {"backend": "openai", "raw": res.model_dump() if res else {}},
    )

def classify(image: Image.Image, backend: str = "ollama", model: Optional[str] = None):
    backend = (backend or "ollama").lower()
    if backend == "openai":
        return infer_with_openai(image, model or "gpt-4o-mini")
    return infer_with_ollama(image, model)  # falls back to DEFAULT_OLLAMA_MODEL
