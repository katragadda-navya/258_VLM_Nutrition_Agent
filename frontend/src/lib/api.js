// frontend/src/lib/api.js
const API = (path) => `http://localhost:8000${path}`;

export async function analyzeImage(
  file,
  { backend = "ollama", model = "qwen3-vl:8b", timeoutMs = 600000 } = {} // 10 min
) {
  const form = new FormData();
  form.append("image", file);
  form.append("backend", backend);
  if (model) form.append("model", model);

  const res = await fetchWithTimeout(API("/api/analyze"), {
    method: "POST",
    body: form,
    timeout: timeoutMs,
  });

  if (!res.ok) {
    const text = await res.text();
    try {
      const j = JSON.parse(text);
      throw new Error(j.error || text);
    } catch {
      throw new Error(`API ${res.status}: ${text}`);
    }
  }
  return res.json();
}

function fetchWithTimeout(resource, options = {}) {
  const { timeout = 600000 } = options; // default 10 min
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  return fetch(resource, { ...options, signal: controller.signal }).finally(() =>
    clearTimeout(id)
  );
}
