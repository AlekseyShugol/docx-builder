import { saveDraftToServer } from "./api.js";

const LOCAL_DRAFT_KEY = "docx_builder_draft_v1";

export function loadLocalDraft() {
  try {
    const raw = localStorage.getItem(LOCAL_DRAFT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && Array.isArray(parsed.blocks)) {
      return parsed;
    }
  } catch {
    // ignore storage errors
  }
  return null;
}

export function createDocumentState(onStatusChange) {
  let doc = {
    title: "",
    subtitle: "",
    blocks: [],
  };
  let autosaveTimer = null;

  function saveLocal() {
    try {
      localStorage.setItem(LOCAL_DRAFT_KEY, JSON.stringify(doc));
    } catch {
      // ignore storage errors
    }
  }

  function scheduleAutosave() {
    saveLocal();
    onStatusChange("Сохранение...");
    if (autosaveTimer) {
      clearTimeout(autosaveTimer);
    }
    autosaveTimer = setTimeout(async () => {
      try {
        await saveDraftToServer(doc);
        onStatusChange("Изменения сохранены");
      } catch {
        onStatusChange("Сохранено локально");
      }
    }, 600);
  }

  return {
    getDoc() {
      return doc;
    },
    setDoc(nextDoc, triggerSave = false) {
      doc = {
        title: nextDoc?.title || "",
        subtitle: nextDoc?.subtitle || "",
        blocks: Array.isArray(nextDoc?.blocks) ? nextDoc.blocks : [],
      };
      if (triggerSave) {
        scheduleAutosave();
      }
    },
    scheduleAutosave,
  };
}
