const API_BASE = window.DOCX_BUILDER_API_URL || "";

async function requestJson(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export function fetchDraft() {
  return requestJson("/api/draft");
}

export function saveDraftToServer(doc) {
  return requestJson("/api/draft", {
    method: "PUT",
    body: JSON.stringify(doc),
  });
}

export function parseMarkupOnServer(rawText) {
  return requestJson("/api/parse", {
    method: "POST",
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export async function exportDocxOnServer(payload) {
  const res = await fetch(`${API_BASE}/api/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Ошибка экспорта: HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const pages = Number(res.headers.get("X-Docx-Pages") || "0");
  const fillerAdded = res.headers.get("X-Docx-Even-Filler") === "1";
  return { blob, pages, fillerAdded };
}
