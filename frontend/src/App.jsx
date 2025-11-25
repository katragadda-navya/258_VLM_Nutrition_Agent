import React, { useState, useEffect } from "react";
import { analyzeImage } from "./lib/api";

const OLLAMA_MODELS = [
  { id: "qwen3-vl:8b",     label: "Qwen3-VL 8B" },
  { id: "llava:7b-v1.6",   label: "LLaVA-1.6 7B" },
  { id: "minicpm-v:8b",    label: "MiniCPM-V 2.6 8B" },
];

const OPENAI_MODELS = [
  { id: "gpt-4o-mini",     label: "GPT-4o mini" },
  { id: "gpt-4o",          label: "GPT-4o" },
];

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [backend, setBackend] = useState("ollama");
  const [model, setModel] = useState("qwen3-vl:8b");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // keep a sensible default whenever backend flips
  useEffect(() => {
    setModel(backend === "ollama" ? "qwen3-vl:8b" : "gpt-4o-mini");
  }, [backend]);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setErr("");
  };

  const onAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setErr("");
    setResult(null);
    try {
      const data = await analyzeImage(file, { backend, model });
      setResult(data);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const modelOptions = backend === "ollama" ? OLLAMA_MODELS : OPENAI_MODELS;

  return (
    <div style={{ maxWidth: 820, margin: "2rem auto", fontFamily: "system-ui, Inter, Segoe UI, Roboto, sans-serif" }}>
      <h1>🥗 VLM Nutrition Agent</h1>

      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "1fr 1fr" }}>
        <label>
          Backend
          <select value={backend} onChange={(e) => setBackend(e.target.value)} style={{ display: "block", width: "100%", padding: 8 }}>
            <option value="ollama">ollama (local)</option>
            <option value="openai">openai (vision-capable)</option>
          </select>
        </label>

        <label>
          Model
          <select value={model} onChange={(e) => setModel(e.target.value)} style={{ display: "block", width: "100%", padding: 8 }}>
            {modelOptions.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </label>
      </div>

      <div style={{ marginTop: 12 }}>
        <input type="file" accept="image/*" onChange={onPick} />
        {preview && <img src={preview} alt="preview" style={{ display: "block", marginTop: 12, maxWidth: "100%", borderRadius: 12 }} />}
      </div>

      <button onClick={onAnalyze} disabled={!file || loading} style={{ marginTop: 12, padding: "10px 14px", borderRadius: 10 }}>
        {loading ? "Analyzing…" : "Analyze"}
      </button>

      {err && <p style={{ color: "crimson", marginTop: 12 }}>{err}</p>}

      {result && (
        <div style={{ marginTop: 16, padding: 16, border: "1px solid #eee", borderRadius: 12 }}>
          <h3>Result</h3>
          <p>
            <b>Prediction:</b> {result.label} — Portion: {Math.round(result.portion_g)} g (conf {Math.round((result.confidence || 0) * 100)}%)
          </p>
          {result.serving_used && <p><b>Serving used:</b> {result.serving_used}</p>}
          {result.fdc_match && (
            <p><b>FDC:</b> {result.fdc_match.description} <i>({result.fdc_match.dataType})</i></p>
          )}
          {result.timings_s && (
            <p><b>Timings:</b> VLM {result.timings_s.vlm}s • USDA {result.timings_s.fdc}s</p>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
            <Metric k="Calories (kcal)" v={result.nutrition?.calories_kcal} />
            <Metric k="Protein (g)" v={result.nutrition?.protein_g} />
            <Metric k="Carbs (g)" v={result.nutrition?.carb_g} />
            <Metric k="Fat (g)" v={result.nutrition?.fat_g} />
            <Metric k="Fiber (g)" v={result.nutrition?.fiber_g} />
            <Metric k="Sodium (mg)" v={result.nutrition?.sodium_mg} />
          </div>

          <div style={{ marginTop: 8 }}>
            <b>Tips</b>
            <ul>{(result.tips || []).map((t, i) => <li key={i}>{t}</li>)}</ul>
          </div>

          <details style={{ marginTop: 8 }}>
            <summary>Show raw</summary>
            <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
}

function Metric({ k, v }) {
  return (
    <div style={{ padding: 10, background: "#fafafa", borderRadius: 10, textAlign: "center" }}>
      <div style={{ fontSize: 12, color: "#666" }}>{k}</div>
      <div style={{ fontSize: 20, fontWeight: 600 }}>{v ?? "—"}</div>
    </div>
  );
}
