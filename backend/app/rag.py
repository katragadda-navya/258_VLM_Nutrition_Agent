# backend/app/rag.py
import os
import glob
import json
from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

_CORPUS = None        # type: List[Tuple[str, str]]
_EMBEDDINGS = None    # type: np.ndarray
_MODEL = None         # type: SentenceTransformer


def _load_corpus(doc_dir: str) -> List[Tuple[str, str]]:
    """
    Load all .txt/.md docs from doc_dir.
    Returns list of (filename, text).
    """
    docs: List[Tuple[str, str]] = []
    patterns = ["*.md", "*.txt"]
    for pat in patterns:
        for path in glob.glob(os.path.join(doc_dir, pat)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text:
                    docs.append((os.path.basename(path), text))
            except Exception:
                continue
    return docs


def _ensure_index():
    """
    Lazily load the corpus and build embeddings once
    for the lifetime of the process.
    """
    global _CORPUS, _EMBEDDINGS, _MODEL
    if _CORPUS is not None and _EMBEDDINGS is not None and _MODEL is not None:
        return

    doc_dir = os.path.join(os.path.dirname(__file__), "..", "rag_docs")
    doc_dir = os.path.abspath(doc_dir)

    _CORPUS = _load_corpus(doc_dir)
    if not _CORPUS:
        _CORPUS = [("empty", "No nutrition guidance documents found.")]
    # Small, fast embedding model
    _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts = [text for _, text in _CORPUS]
    _EMBEDDINGS = _MODEL.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # a: (d,), b: (n, d) with L2-normalized rows -> cosine = dot product
    return b @ a


def rag_query(query: str, top_k: int = 3) -> List[dict]:
    """
    Retrieve top_k snippets relevant to the query.
    Returns list of {source, text, score}.
    """
    _ensure_index()

    q_emb = _MODEL.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    scores = _cosine_sim(q_emb, _EMBEDDINGS)
    idx = np.argsort(-scores)[:top_k]

    results: List[dict] = []
    for i in idx:
        fname, text = _CORPUS[i]
        results.append({
            "source": fname,
            "text": text,
            "score": float(scores[i]),
        })
    return results


def build_query_from_nutrition(label: str, nutrition: dict) -> str:
    """
    Build a natural-language query using dish name and macros
    to steer retrieval.
    """
    calories = nutrition.get("calories") or nutrition.get("energy_kcal") or 0
    protein = nutrition.get("protein", 0)
    fat = nutrition.get("fat", 0)
    carbs = nutrition.get("carbs", 0)
    fiber = nutrition.get("fiber", 0)
    sodium = nutrition.get("sodium", 0)

    info = {
        "dish": label,
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs,
        "fiber": fiber,
        "sodium": sodium,
    }

    return (
        "Given the following meal nutrition, suggest 2–3 evidence-based, practical "
        "tips on how to improve the meal (e.g., lower sodium, increase fiber, "
        "balance macros) using the knowledge base.\n"
        f"Nutrition JSON: {json.dumps(info)}"
    )