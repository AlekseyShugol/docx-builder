import {
  exportDocxOnServer,
  fetchDraft,
  parseMarkupOnServer,
} from "./api.js";
import { createDefaultBlock, renderBlockElement } from "./blocks.js";
import { createDocumentState, loadLocalDraft } from "./state.js";

const titleInput = document.getElementById("doc-title");
const subtitleInput = document.getElementById("doc-subtitle");
const blocksContainer = document.getElementById("blocks-container");
const emptyHint = document.getElementById("empty-hint");
const saveStatus = document.getElementById("save-status");
const cbSolutions = document.getElementById("cb-solutions");
const cbEven = document.getElementById("cb-even");
const toastEl = document.getElementById("toast");

const pasteDialog = document.getElementById("paste-dialog");
const pasteForm = document.getElementById("paste-form");
const pasteTextarea = document.getElementById("paste-textarea");
const fileOpenInput = document.getElementById("file-open-json");
const btnTheme = document.getElementById("btn-theme");

const THEME_KEY = "docx_builder_theme";

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";
  btnTheme.textContent = isDark ? "☀️" : "🌙";
  localStorage.setItem(THEME_KEY, isDark ? "dark" : "light");
}

btnTheme.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
});

applyTheme(localStorage.getItem(THEME_KEY) || "light");

let toastTimer = null;

function showToast(message) {
  toastEl.textContent = message;
  toastEl.hidden = false;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.hidden = true;
  }, 4000);
}

const state = createDocumentState((status) => {
  saveStatus.textContent = status;
});

function renderSheet() {
  const doc = state.getDoc();
  titleInput.value = doc.title;
  subtitleInput.value = doc.subtitle;

  blocksContainer.innerHTML = "";
  emptyHint.hidden = doc.blocks.length > 0;

  doc.blocks.forEach((blk, idx) => {
    const el = renderBlockElement(blk, idx, doc.blocks.length, {
      onChange: () => state.scheduleAutosave(),
      onMove: (i, delta) => {
        const target = i + delta;
        if (target < 0 || target >= doc.blocks.length) return;
        const [item] = doc.blocks.splice(i, 1);
        doc.blocks.splice(target, 0, item);
        renderSheet();
        state.scheduleAutosave();
      },
      onDelete: (i) => {
        doc.blocks.splice(i, 1);
        renderSheet();
        state.scheduleAutosave();
      },
    });
    blocksContainer.appendChild(el);
  });
}

function addBlocks(newBlocks) {
  const doc = state.getDoc();
  doc.blocks.push(...newBlocks);
  renderSheet();
  state.scheduleAutosave();
  requestAnimationFrame(() => {
    blocksContainer.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
}

titleInput.addEventListener("input", () => {
  state.getDoc().title = titleInput.value;
  state.scheduleAutosave();
});

subtitleInput.addEventListener("input", () => {
  state.getDoc().subtitle = subtitleInput.value;
  state.scheduleAutosave();
});

document.querySelectorAll("[data-add]").forEach((btn) => {
  btn.addEventListener("click", () => {
    addBlocks([createDefaultBlock(btn.dataset.add)]);
  });
});

document.getElementById("btn-new").addEventListener("click", () => {
  state.setDoc({ title: "", subtitle: "", blocks: [] }, true);
  renderSheet();
  showToast("Создан новый пустой лист");
});

document.getElementById("btn-paste").addEventListener("click", () => {
  pasteTextarea.value = "";
  pasteDialog.showModal();
  pasteTextarea.focus();
});

document.getElementById("btn-close-modal").addEventListener("click", () => pasteDialog.close());
document.getElementById("btn-cancel-modal").addEventListener("click", () => pasteDialog.close());

pasteForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const raw = pasteTextarea.value;
  if (!raw.trim()) {
    pasteDialog.close();
    return;
  }
  try {
    const { blocks } = await parseMarkupOnServer(raw);
    if (blocks.length > 0) {
      addBlocks(blocks);
      showToast(`Добавлено блоков: ${blocks.length}`);
    }
    pasteDialog.close();
  } catch (err) {
    showToast(`Не удалось разобрать текст: ${err.message}`);
  }
});

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function saveJsonFile() {
  const doc = state.getDoc();
  const blob = new Blob([JSON.stringify(doc, null, 2)], { type: "application/json;charset=utf-8" });
  const name = (doc.title.trim() || "document") + ".json";
  downloadBlob(blob, name);
}

document.getElementById("btn-save-json").addEventListener("click", saveJsonFile);
document.getElementById("btn-open-json").addEventListener("click", () => fileOpenInput.click());

fileOpenInput.addEventListener("change", async () => {
  const file = fileOpenInput.files?.[0];
  if (!file) return;
  try {
    const parsed = JSON.parse(await file.text());
    state.setDoc(parsed, true);
    renderSheet();
    showToast(`Открыт файл: ${file.name}`);
  } catch {
    showToast("Ошибка чтения JSON-файла");
  } finally {
    fileOpenInput.value = "";
  }
});

document.getElementById("btn-export-docx").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  try {
    const doc = state.getDoc();
    const { blob, pages, fillerAdded } = await exportDocxOnServer({
      ...doc,
      include_solutions: cbSolutions.checked,
      even_pages: cbEven.checked,
    });
    const filename = (doc.title.trim() || "document") + ".docx";
    downloadBlob(blob, filename);
    if (fillerAdded) {
      showToast(`Word сохранён (${pages} стр., добавлен лист самоконтроля)`);
    } else {
      showToast(`Word сохранён (${pages} стр.)`);
    }
  } catch (err) {
    showToast(err.message || "Ошибка при экспорте .docx");
  } finally {
    btn.disabled = false;
  }
});

window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
    e.preventDefault();
    saveJsonFile();
  }
});

async function bootstrap() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
  const localDraft = loadLocalDraft();
  if (localDraft) {
    state.setDoc(localDraft, false);
    renderSheet();
    return;
  }
  try {
    const draft = await fetchDraft();
    state.setDoc(draft, false);
    renderSheet();
  } catch {
    showToast("Не удалось загрузить черновик с сервера");
  }
}

bootstrap();
