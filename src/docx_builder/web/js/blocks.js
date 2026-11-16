const BLOCK_LABELS = {
  heading: "Заголовок",
  paragraph: "Текст",
  code: "Код",
  table: "Таблица",
  task: "Задача",
  page_break: "Разрыв страницы",
};

export function createDefaultBlock(type) {
  switch (type) {
    case "heading":
      return { type: "heading", text: "" };
    case "code":
      return { type: "code", title: "Листинг кода", code: "" };
    case "table":
      return {
        type: "table",
        title: "",
        headers: ["Колонка 1", "Колонка 2"],
        rows: [["", ""]],
      };
    case "task":
      return { type: "task", title: "", condition: "", io: "", hint: "", solution: "" };
    case "page_break":
      return { type: "page_break" };
    default:
      return { type: "paragraph", text: "" };
  }
}

export function autoResizeTextarea(el) {
  el.style.height = "auto";
  el.style.height = `${Math.max(el.scrollHeight, 36)}px`;
}

function makeActionBtn(label, title, onClick, isDanger = false) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = isDanger ? "icon-btn danger" : "icon-btn";
  btn.textContent = label;
  btn.title = title;
  btn.addEventListener("click", onClick);
  return btn;
}

function makeAutoTextarea(className, value, placeholder, onInput) {
  const ta = document.createElement("textarea");
  ta.className = className;
  ta.value = value || "";
  ta.placeholder = placeholder;
  ta.rows = 1;
  ta.addEventListener("input", () => {
    autoResizeTextarea(ta);
    onInput(ta.value);
  });
  requestAnimationFrame(() => autoResizeTextarea(ta));
  return ta;
}

function renderTableBody(block, tableEl, onChange) {
  tableEl.innerHTML = "";
  const headers = Array.isArray(block.headers) ? block.headers : [];
  const rows = Array.isArray(block.rows) ? block.rows : [];
  const colCount = Math.max(headers.length, ...rows.map((r) => r.length), 1);

  while (headers.length < colCount) headers.push(`Колонка ${headers.length + 1}`);
  block.headers = headers;

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headers.forEach((h, cIdx) => {
    const th = document.createElement("th");
    const inp = document.createElement("input");
    inp.type = "text";
    inp.value = h;
    inp.placeholder = `Заголовок ${cIdx + 1}`;
    inp.addEventListener("input", () => {
      block.headers[cIdx] = inp.value;
      onChange();
    });
    th.appendChild(inp);
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  tableEl.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row, rIdx) => {
    while (row.length < colCount) row.push("");
    const tr = document.createElement("tr");
    row.forEach((cellVal, cIdx) => {
      const td = document.createElement("td");
      const inp = document.createElement("input");
      inp.type = "text";
      inp.value = cellVal;
      inp.addEventListener("input", () => {
        block.rows[rIdx][cIdx] = inp.value;
        onChange();
      });
      td.appendChild(inp);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tableEl.appendChild(tbody);
}

export function renderBlockElement(block, index, total, handlers) {
  const wrap = document.createElement("article");
  wrap.className = "sheet-block";

  const header = document.createElement("div");
  header.className = "block-header";

  const badge = document.createElement("span");
  badge.className = "block-badge";
  badge.textContent = BLOCK_LABELS[block.type] || "Блок";

  const actions = document.createElement("div");
  actions.className = "block-actions";
  if (index > 0) {
    actions.appendChild(makeActionBtn("↑", "Поднять выше", () => handlers.onMove(index, -1)));
  }
  if (index < total - 1) {
    actions.appendChild(makeActionBtn("↓", "Опустить ниже", () => handlers.onMove(index, 1)));
  }
  actions.appendChild(makeActionBtn("✕", "Удалить блок", () => handlers.onDelete(index), true));

  header.append(badge, actions);
  wrap.appendChild(header);

  const onChange = handlers.onChange;

  if (block.type === "heading") {
    const inp = document.createElement("input");
    inp.type = "text";
    inp.className = "doc-input heading-input";
    inp.value = block.text || "";
    inp.placeholder = "Введите заголовок раздела...";
    inp.addEventListener("input", () => {
      block.text = inp.value;
      onChange();
    });
    wrap.appendChild(inp);
  } else if (block.type === "code") {
    const box = document.createElement("div");
    box.className = "code-box";

    const boxHdr = document.createElement("div");
    boxHdr.className = "code-box-header";
    const titleInp = document.createElement("input");
    titleInp.type = "text";
    titleInp.className = "code-title-input";
    titleInp.value = block.title || "Листинг кода";
    titleInp.placeholder = "Подпись к коду...";
    titleInp.addEventListener("input", () => {
      block.title = titleInp.value;
      onChange();
    });
    boxHdr.appendChild(titleInp);

    const codeTa = makeAutoTextarea(
      "code-textarea",
      block.code,
      "// Вставьте или напишите код...",
      (val) => {
        block.code = val;
        onChange();
      },
    );
    box.append(boxHdr, codeTa);
    wrap.appendChild(box);
  } else if (block.type === "table") {
    const box = document.createElement("div");
    box.className = "table-box";

    const tb = document.createElement("div");
    tb.className = "table-toolbar";

    const titleInp = document.createElement("input");
    titleInp.type = "text";
    titleInp.className = "table-title-input";
    titleInp.value = block.title || "";
    titleInp.placeholder = "Название таблицы (необязательно)...";
    titleInp.addEventListener("input", () => {
      block.title = titleInp.value;
      onChange();
    });

    const ctrls = document.createElement("div");
    ctrls.className = "table-controls";
    const tableEl = document.createElement("table");
    tableEl.className = "doc-table";

    const addCtrl = (text, fn) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "table-ctrl-btn";
      b.textContent = text;
      b.addEventListener("click", () => {
        fn();
        renderTableBody(block, tableEl, onChange);
        onChange();
      });
      ctrls.appendChild(b);
    };

    addCtrl("+ Строка", () => {
      const cols = Math.max(block.headers?.length || 2, 1);
      block.rows = block.rows || [];
      block.rows.push(new Array(cols).fill(""));
    });
    addCtrl("− Строка", () => {
      if (block.rows?.length > 1) block.rows.pop();
    });
    addCtrl("+ Колонка", () => {
      block.headers = block.headers || [];
      block.headers.push(`Колонка ${block.headers.length + 1}`);
      (block.rows || []).forEach((r) => r.push(""));
    });
    addCtrl("− Колонка", () => {
      if ((block.headers?.length || 0) > 1) {
        block.headers.pop();
        (block.rows || []).forEach((r) => r.pop());
      }
    });

    tb.append(titleInp, ctrls);

    const scroll = document.createElement("div");
    scroll.className = "table-scroll";
    renderTableBody(block, tableEl, onChange);
    scroll.appendChild(tableEl);

    box.append(tb, scroll);
    wrap.appendChild(box);
  } else if (block.type === "task") {
    const card = document.createElement("div");
    card.className = "task-card";

    const titleInp = document.createElement("input");
    titleInp.type = "text";
    titleInp.className = "doc-input task-title-input";
    titleInp.value = block.title || "";
    titleInp.placeholder = "Название задачи (например: Задача 1. Сумма чисел)...";
    titleInp.addEventListener("input", () => {
      block.title = titleInp.value;
      onChange();
    });
    card.appendChild(titleInp);

    card.appendChild(
      makeAutoTextarea(
        "doc-textarea paragraph-textarea",
        block.condition,
        "Условие задачи...",
        (val) => {
          block.condition = val;
          onChange();
        },
      ),
    );

    const ioBox = document.createElement("div");
    ioBox.className = "io-box";
    const ioLbl = document.createElement("div");
    ioLbl.className = "task-section-label";
    ioLbl.textContent = "Пример входных и выходных данных";
    ioBox.append(
      ioLbl,
      makeAutoTextarea("code-textarea", block.io, "Вход: ...\nВыход: ...", (val) => {
        block.io = val;
        onChange();
      }),
    );
    card.appendChild(ioBox);

    const hintRow = document.createElement("div");
    hintRow.className = "task-hint-row";
    const hintPrefix = document.createElement("span");
    hintPrefix.className = "task-hint-prefix";
    hintPrefix.textContent = "Рекомендация:";
    const hintInp = document.createElement("input");
    hintInp.type = "text";
    hintInp.className = "doc-input";
    hintInp.value = block.hint || "";
    hintInp.placeholder = "Подсказка (необязательно)...";
    hintInp.addEventListener("input", () => {
      block.hint = hintInp.value;
      onChange();
    });
    hintRow.append(hintPrefix, hintInp);
    card.appendChild(hintRow);

    const solBox = document.createElement("div");
    solBox.className = "code-box";
    const solHdr = document.createElement("div");
    solHdr.className = "code-box-header";
    const solLbl = document.createElement("div");
    solLbl.className = "task-section-label";
    solLbl.style.marginBottom = "0";
    solLbl.textContent = "Решение (необязательно)";
    solHdr.appendChild(solLbl);
    solBox.append(
      solHdr,
      makeAutoTextarea("code-textarea", block.solution, "// Код решения...", (val) => {
        block.solution = val;
        onChange();
      }),
    );
    card.appendChild(solBox);

    wrap.appendChild(card);
  } else if (block.type === "page_break") {
    const line = document.createElement("div");
    line.className = "page-break-line";
    line.textContent = "Новая страница (Page Break)";
    wrap.appendChild(line);
  } else {
    wrap.appendChild(
      makeAutoTextarea(
        "doc-textarea paragraph-textarea",
        block.text,
        "Введите текст. Каждый перенос строки — новый абзац. Для списка начните строку с «• ».",
        (val) => {
          block.text = val;
          onChange();
        },
      ),
    );
  }

  return wrap;
}
