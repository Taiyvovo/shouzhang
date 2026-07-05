/* ====== 手账编辑器 v2 ====== */

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// ---- 状态 ----
const state = {
  canvas: { w: 1080, h: 1527, bg: "#fbfaf6" },
  elements: [],
  selectedId: null,
  tool: "select",
  zoom: 50, // percent
  zoomFit: true,
  stickers: {},
  fonts: [],
  curStickerCat: "",
  nextId: 1,
  _pan: { active: false, x: 0, y: 0, sx: 0, sy: 0 },
  _drag: { active: false, elId: null, sx: 0, sy: 0, ex: 0, ey: 0 },
  _resize: { active: false, elId: null, sx: 0, sy: 0, ew: 0, eh: 0 },
};

// ---- DOM ----
const D = {
  svg: $("#svgCanvas"),
  bgRect: $("#bgRect"),
  bgPattern: $("#bgPattern"),
  elGroup: $("#elementsGroup"),
  fontStyles: $("#fontStyles"),
  canvasWrap: $("#canvasWrap"),
  canvasView: $("#canvasView"),
  textEditor: $("#textEditor"),
  selCanvas: $("#selCanvas"),
  selBg: $("#selBg"),
  btnExport: $("#btnExport"),
  btnExportSVG: $("#btnExportSVG"),
  stickerTray: $("#stickerTray"),
  trayTabs: $("#trayTabs"),
  trayGrid: $("#trayGrid"),
  zoomLabel: $("#zoomLabel"),
  zoomSlider: $("#zoomSlider"),
  zoomOut: $("#zoomOut"),
  zoomIn: $("#zoomIn"),
  zoomFit: $("#zoomFit"),
  propsEmpty: $(".props-empty"),
  propsForm: $(".props-form"),
  propText: $("#propText"),
  propFamily: $("#propFamily"),
  propSize: $("#propSize"),
  propSizeVal: $("#propSizeVal"),
  propWeight: $("#propWeight"),
  propColor: $("#propColor"),
  propAlign: $("#propAlign"),
  propRot: $("#propRot"),
  propRotVal: $("#propRotVal"),
  propOpacity: $("#propOpacity"),
  propW: $("#propW"),
  propH: $("#propH"),
  btnDelete: $("#btnDelete"),
  toolBtns: $$(".tbtn[data-tool]"),
};

// ====== 初始化 ======
async function init() {
  await loadFonts();
  await loadStickers();
  await loadBgs();
  setupTools();
  setupCanvas();
  setupProps();
  setupExport();
  setupZoom();
  applyZoom();
  window.addEventListener("resize", () => { if (state.zoomFit) { fitZoom(); } });
}

async function loadFonts() {
  const r = await fetch("/api/fonts");
  state.fonts = (await r.json()).sort((a,b) => {
    const cjk = /cjk|sc|jp|kr|hans|hant|chinese|japanese|korean|娃娃|yuyu|oppo/i;
    return (cjk.test(a.family) ? 0 : 1) - (cjk.test(b.family) ? 0 : 1) || a.family.localeCompare(b.family);
  });
  D.propFamily.innerHTML = state.fonts.map(f => `<option value="${f.family}">${f.family} (${f.count})</option>`).join("")
    + '<option value="serif">serif (系统)</option><option value="sans-serif">sans-serif (系统)</option>';
}

async function loadStickers() {
  const r = await fetch("/api/stickers");
  state.stickers = (await r.json()).categories;
  const cats = Object.keys(state.stickers);
  if (!cats.length) return;
  state.curStickerCat = cats[0];
  D.trayTabs.innerHTML = cats.map(c => `<button class="tray-tab${c===cats[0]?" active":""}" data-cat="${c}">${c}</button>`).join("");
  D.trayTabs.querySelectorAll(".tray-tab").forEach(b => b.addEventListener("click", () => {
    state.curStickerCat = b.dataset.cat;
    D.trayTabs.querySelectorAll(".tray-tab").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    renderTrayGrid();
  }));
  renderTrayGrid();
}

function renderTrayGrid() {
  const items = state.stickers[state.curStickerCat] || [];
  D.trayGrid.innerHTML = "";
  items.forEach(s => {
    const div = document.createElement("div");
    div.className = "tray-item";
    div.title = s.name;
    div.dataset.src = s.path;
    // 加载 SVG 内容
    fetch("/api/sticker-svg/" + s.path)
      .then(r => r.text())
      .then(svgText => {
        const inner = svgText.replace(/<svg[^>]*>/, "").replace(/<\/svg>/, "").trim();
        div.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="44" height="44" style="pointer-events:none">${inner}</svg>`;
      })
      .catch(() => { div.textContent = "?"; });
    div.addEventListener("click", () => addSticker(state.canvas.w/2, state.canvas.h/2, s.path));
    D.trayGrid.appendChild(div);
  });
}

async function loadBgs() {
  const r = await fetch("/api/backgrounds");
  const bgs = await r.json();
  D.selBg.innerHTML = '<option value="">纯色背景</option>' + bgs.map(b => `<option value="${b.name}">${b.name}</option>`).join("");
}

// ====== 工具 ======
function setupTools() {
  D.toolBtns.forEach(btn => btn.addEventListener("click", () => {
    state.tool = btn.dataset.tool;
    D.toolBtns.forEach(b => b.classList.toggle("active", b.dataset.tool === state.tool));
    D.stickerTray.style.display = state.tool === "sticker" ? "flex" : "none";
    if (state.tool !== "sticker") hideTextEditor();
  }));
}

// ====== 画布缩放 ======
function setupZoom() {
  D.zoomSlider.addEventListener("input", () => { state.zoomFit = false; state.zoom = +D.zoomSlider.value; applyZoom(); });
  D.zoomOut.addEventListener("click", () => { state.zoomFit = false; state.zoom = Math.max(10, state.zoom - 10); D.zoomSlider.value = state.zoom; applyZoom(); });
  D.zoomIn.addEventListener("click", () => { state.zoomFit = false; state.zoom = Math.min(200, state.zoom + 10); D.zoomSlider.value = state.zoom; applyZoom(); });
  D.zoomFit.addEventListener("click", () => { state.zoomFit = true; fitZoom(); });
  D.selCanvas.addEventListener("change", () => {
    const [w,h] = D.selCanvas.value.split("_").map(Number);
    state.canvas.w = w; state.canvas.h = h;
    D.svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    D.bgRect.setAttribute("width", w); D.bgRect.setAttribute("height", h);
    if (state.zoomFit) fitZoom(); else applyZoom();
  });
  D.selBg.addEventListener("change", async () => {
    const id = D.selBg.value;
    state.canvas.bg = "#fbfaf6";
    D.bgPattern.innerHTML = "";
    if (id) {
      const r = await fetch(`/api/background/${id}`);
      const t = await r.text();
      const m = t.match(/fill="([^"]+)"/);
      if (m) state.canvas.bg = m[1];
      const inner = t.replace(/<svg[^>]*>/, "").replace(/<\/svg>/, "").trim();
      if (inner) { const g = document.createElementNS("http://www.w3.org/2000/svg","g"); g.innerHTML = inner; D.bgPattern.appendChild(g); }
    }
    syncCanvas();
  });
}

function fitZoom() {
  const wrap = D.canvasWrap;
  const pad = 40;
  const s = Math.floor(Math.min((wrap.clientWidth - pad) / state.canvas.w, (wrap.clientHeight - pad) / state.canvas.h) * 100);
  state.zoom = Math.max(10, Math.min(200, s));
  D.zoomSlider.value = state.zoom;
  applyZoom();
}

function applyZoom() {
  const s = state.zoom / 100;
  D.canvasView.style.transform = `scale(${s})`;
  D.canvasView.style.width = state.canvas.w + "px";
  D.canvasView.style.height = state.canvas.h + "px";
  D.svg.setAttribute("viewBox", `0 0 ${state.canvas.w} ${state.canvas.h}`);
  D.bgRect.setAttribute("width", state.canvas.w);
  D.bgRect.setAttribute("height", state.canvas.h);
  D.zoomLabel.textContent = state.zoom + "%";
  D.zoomSlider.value = state.zoom;
}

// ====== 画布交互 ======
function setupCanvas() {
  D.canvasView.addEventListener("mousedown", onCanvasMouseDown);
  window.addEventListener("mousemove", onCanvasMouseMove);
  window.addEventListener("mouseup", onCanvasMouseUp);
  D.canvasView.addEventListener("dblclick", onCanvasDblClick);
  window.addEventListener("keydown", onKeyDown);
}

function svgPoint(e) {
  const rect = D.canvasView.getBoundingClientRect();
  const s = state.zoom / 100;
  return { x: (e.clientX - rect.left) / s, y: (e.clientY - rect.top) / s };
}

function onCanvasMouseDown(e) {
  hideTextEditor();
  const pt = svgPoint(e);

  // 中键平移画布
  if (e.button === 1) { state._pan.active = true; state._pan.x = e.clientX; state._pan.y = e.clientY; state._pan.sx = D.canvasWrap.scrollLeft; state._pan.sy = D.canvasWrap.scrollTop; e.preventDefault(); return; }

  // 点击 resize 手柄
  const handle = e.target.closest(".svg-resize-handle");
  if (handle) {
    const elG = handle.closest(".svg-element");
    if (!elG) return;
    const el = state.elements.find(x => x.id === elG.dataset.id);
    if (!el) return;
    state._resize.active = true; state._resize.elId = el.id;
    state._resize.sx = pt.x; state._resize.sy = pt.y;
    state._resize.ew = el.w; state._resize.eh = el.h;
    e.preventDefault(); e.stopPropagation(); return;
  }

  // 点击元素
  const elG = e.target.closest(".svg-element");
  if (elG) {
    const el = state.elements.find(x => x.id === elG.dataset.id);
    if (!el) return;
    selectElement(el.id);
    state._drag.active = true; state._drag.elId = el.id;
    state._drag.sx = pt.x; state._drag.sy = pt.y;
    state._drag.ex = el.x; state._drag.ey = el.y;
    e.preventDefault(); return;
  }

  // 空白区域
  if (state.tool === "text") {
    addText(pt.x, pt.y);
  } else if (state.tool === "sticker") {
    const cats = Object.keys(state.stickers);
    const cat = state.curStickerCat || cats[0];
    const items = state.stickers[cat];
    if (items?.length) addSticker(pt.x, pt.y, items[0].path);
  } else {
    deselectAll();
  }
}

function onCanvasMouseMove(e) {
  // 平移
  if (state._pan.active) {
    D.canvasWrap.scrollLeft = state._pan.sx - (e.clientX - state._pan.x);
    D.canvasWrap.scrollTop = state._pan.sy - (e.clientY - state._pan.y);
    return;
  }
  // 拖拽
  if (state._drag.active) {
    const pt = svgPoint(e);
    const el = state.elements.find(x => x.id === state._drag.elId);
    if (!el) return;
    el.x = Math.round(state._drag.ex + (pt.x - state._drag.sx));
    el.y = Math.round(state._drag.ey + (pt.y - state._drag.sy));
    syncCanvas();
    return;
  }
  // 缩放尺寸
  if (state._resize.active) {
    const pt = svgPoint(e);
    const el = state.elements.find(x => x.id === state._resize.elId);
    if (!el) return;
    el.w = Math.max(10, Math.round(state._resize.ew + (pt.x - state._resize.sx)));
    el.h = Math.max(10, Math.round(state._resize.eh + (pt.y - state._resize.sy)));
    syncCanvas();
    return;
  }
}

function onCanvasMouseUp() {
  state._drag.active = false;
  state._resize.active = false;
  state._pan.active = false;
}

function onCanvasDblClick(e) {
  const elG = e.target.closest(".svg-element");
  if (!elG) return;
  const el = state.elements.find(x => x.id === elG.dataset.id);
  if (!el || el.type !== "text") return;
  selectElement(el.id);
  showTextEditor(el);
}

function onKeyDown(e) {
  if (e.key === "Delete" && state.selectedId) { deleteSelected(); return; }
  if (e.key === "Escape") { deselectAll(); hideTextEditor(); return; }
  if (!e.ctrlKey && !e.metaKey) {
    if (e.key === "v") switchTool("select");
    if (e.key === "t") switchTool("text");
    if (e.key === "s") switchTool("sticker");
  }
}

function switchTool(t) {
  state.tool = t;
  D.toolBtns.forEach(b => b.classList.toggle("active", b.dataset.tool === t));
  D.stickerTray.style.display = t === "sticker" ? "flex" : "none";
}

// ====== 文字编辑浮层 ======
function showTextEditor(el) {
  D.textEditor.style.display = "block";
  D.textEditor.textContent = el.text;
  D.textEditor.style.left = (el.x * state.zoom / 100) + "px";
  D.textEditor.style.top = (el.y * state.zoom / 100) + "px";
  D.textEditor.style.width = (el.w * state.zoom / 100) + "px";
  D.textEditor.style.minHeight = (el.h * state.zoom / 100) + "px";
  D.textEditor.style.fontSize = (el.size * state.zoom / 100) + "px";
  D.textEditor.style.fontFamily = (el.family || "sans-serif");
  D.textEditor.style.color = el.color || "#333";
  D.textEditor.focus();
  D.textEditor._elId = el.id;
}

function hideTextEditor() {
  if (D.textEditor.style.display === "none") return;
  const el = state.elements.find(x => x.id === D.textEditor._elId);
  if (el) { el.text = D.textEditor.textContent || ""; syncCanvas(); D.propText.value = el.text; }
  D.textEditor.style.display = "none";
  D.textEditor._elId = null;
}

D.textEditor.addEventListener("blur", hideTextEditor);
D.textEditor.addEventListener("input", () => {
  const el = state.elements.find(x => x.id === D.textEditor._elId);
  if (el) D.propText.value = D.textEditor.textContent || "";
});

// ====== 元素操作 ======
function addText(x, y) {
  const el = { id: "e" + (state.nextId++), type: "text", x: Math.round(x), y: Math.round(y), w: 340, h: 60,
    text: "输入文字", family: "serif", size: 36, weight: 400, color: "#333", align: "left", rotation: 0, opacity: 1 };
  state.elements.push(el);
  syncCanvas();
  selectElement(el.id);
  setTimeout(() => showTextEditor(el), 100);
}

function addSticker(x, y, src) {
  const el = { id: "e" + (state.nextId++), type: "sticker", x: Math.round(x - 40), y: Math.round(y - 40), w: 80, h: 80,
    src, rotation: 0, opacity: 1 };
  state.elements.push(el);
  syncCanvas();
  selectElement(el.id);
}

function selectElement(id) {
  hideTextEditor();
  state.selectedId = id;
  syncCanvas();
  showProps();
}

function deselectAll() {
  hideTextEditor();
  state.selectedId = null;
  syncCanvas();
  hideProps();
}

function deleteSelected() {
  if (!state.selectedId) return;
  state.elements = state.elements.filter(e => e.id !== state.selectedId);
  deselectAll();
}

// ====== 画布同步 ======
function syncCanvas() {
  const g = D.elGroup;
  g.innerHTML = "";

  // 字体 @font-face
  const usedFonts = new Set();
  state.elements.forEach(el => {
    if (el.type === "text" && el.family && !/^(serif|sans-serif|monospace|cursive|fantasy)$/i.test(el.family)) {
      usedFonts.add(el.family);
    }
  });
  let fontCss = "";
  for (const fam of usedFonts) {
    const entry = state.fonts.find(f => f.family.toLowerCase() === fam.toLowerCase());
    if (entry) {
      // 通过 API 获取字体文件路径
      fontCss += `@font-face{font-family:"${fam}";src:url("/api/font-file/${encodeURIComponent(fam)}");}\n`;
    }
  }
  D.fontStyles.textContent = fontCss;

  state.elements.forEach(el => {
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("data-id", el.id);
    group.setAttribute("transform", `translate(${el.x},${el.y}) rotate(${el.rotation||0},${el.w/2},${el.h/2})`);
    group.setAttribute("opacity", el.opacity != null ? el.opacity : "1");
    group.classList.add("svg-element");
    if (el.id === state.selectedId) group.classList.add("selected");

    if (el.type === "text") {
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      const anchor = { left: "start", center: "middle", right: "end" }[el.align || "left"];
      const xMap = { left: 0, center: el.w / 2, right: el.w };
      text.setAttribute("x", xMap[el.align || "left"]);
      text.setAttribute("y", (el.size || 24) * 0.8);
      text.setAttribute("font-family", el.family || "sans-serif");
      text.setAttribute("font-size", el.size || 24);
      text.setAttribute("font-weight", el.weight || 400);
      text.setAttribute("fill", el.color || "#333");
      text.setAttribute("text-anchor", anchor);
      text.setAttribute("style", "pointer-events:none");
      const lines = (el.text || "").split("\n");
      if (lines.length <= 1) {
        text.textContent = el.text || "";
      } else {
        const lh = (el.size || 24) * 1.4;
        lines.forEach((line, i) => {
          const tspan = document.createElementNS("http://www.w3.org/2000/svg","tspan");
          tspan.setAttribute("x", xMap[el.align || "left"]);
          tspan.setAttribute("dy", i === 0 ? "0" : lh);
          tspan.textContent = line;
          text.appendChild(tspan);
        });
      }
      group.appendChild(text);
    } else if (el.type === "sticker") {
      const img = document.createElementNS("http://www.w3.org/2000/svg", "image");
      img.setAttribute("href", "/api/sticker-svg/" + el.src);
      img.setAttribute("width", el.w);
      img.setAttribute("height", el.h);
      img.setAttribute("preserveAspectRatio", "xMidYMid meet");
      img.setAttribute("style", "pointer-events:none");
      img.setAttribute("draggable", "false");
      group.appendChild(img);
    }

    // resize 手柄
    const rh = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rh.setAttribute("x", el.w - 8); rh.setAttribute("y", el.h - 8);
    rh.setAttribute("width", 8); rh.setAttribute("height", 8);
    rh.classList.add("svg-resize-handle");
    rh.setAttribute("data-handle", "se");
    group.appendChild(rh);

    g.appendChild(group);
  });

  D.bgRect.setAttribute("fill", state.canvas.bg);
}

// ====== 属性面板 ======
function showProps() {
  const el = state.elements.find(e => e.id === state.selectedId);
  if (!el) return hideProps();
  D.propsEmpty.style.display = "none";
  D.propsForm.style.display = "block";
  const isText = el.type === "text";

  // 文字专用
  D.propText.parentElement.style.display = isText ? "" : "none";
  D.propFamily.parentElement.style.display = isText ? "" : "none";
  document.querySelector(".prop-row:has(#propSize)").style.display = isText ? "flex" : "none";
  document.querySelector(".prop-row:has(#propWeight)").style.display = isText ? "flex" : "none";
  document.querySelector(".prop-row:has(#propColor)").style.display = isText ? "flex" : "none";
  document.querySelector(".prop-row:has(#propAlign)").style.display = isText ? "flex" : "none";

  if (isText) {
    D.propText.value = el.text || "";
    D.propFamily.value = el.family || "sans-serif";
    D.propSize.value = el.size || 24;
    D.propSizeVal.textContent = el.size || 24;
    D.propWeight.value = el.weight || 400;
    D.propColor.value = el.color || "#333333";
    D.propAlign.value = el.align || "left";
  }
  D.propRot.value = el.rotation || 0;
  D.propRotVal.textContent = (el.rotation || 0) + "°";
  D.propOpacity.value = el.opacity != null ? el.opacity : 1;
  D.propW.value = el.w;
  D.propH.value = el.h;
}

function hideProps() {
  D.propsEmpty.style.display = "";
  D.propsForm.style.display = "none";
}

function updateProp(k, v) {
  const el = state.elements.find(e => e.id === state.selectedId);
  if (!el) return;
  el[k] = v;
  syncCanvas();
  if (k === "rotation") D.propRotVal.textContent = v + "°";
  if (k === "size") D.propSizeVal.textContent = v;
}

function setupProps() {
  D.propText.addEventListener("input", () => updateProp("text", D.propText.value));
  D.propFamily.addEventListener("change", () => { updateProp("family", D.propFamily.value); syncCanvas(); });
  D.propSize.addEventListener("input", () => updateProp("size", parseFloat(D.propSize.value)));
  D.propWeight.addEventListener("change", () => updateProp("weight", parseInt(D.propWeight.value)));
  D.propColor.addEventListener("input", () => updateProp("color", D.propColor.value));
  D.propAlign.addEventListener("change", () => updateProp("align", D.propAlign.value));
  D.propRot.addEventListener("input", () => updateProp("rotation", parseFloat(D.propRot.value)));
  D.propOpacity.addEventListener("input", () => updateProp("opacity", parseFloat(D.propOpacity.value)));
  D.propW.addEventListener("input", () => updateProp("w", parseFloat(D.propW.value) || 10));
  D.propH.addEventListener("input", () => updateProp("h", parseFloat(D.propH.value) || 10));
  D.btnDelete.addEventListener("click", deleteSelected);
}

// ====== 导出 ======
function setupExport() {
  D.btnExport.addEventListener("click", exportPNG);
  D.btnExportSVG.addEventListener("click", exportSVG);
}

async function exportPNG() {
  D.btnExport.textContent = "..."; D.btnExport.disabled = true;
  try {
    const r = await fetch("/api/render", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    if (!r.ok) throw new Error("渲染失败 " + r.status);
    downloadBlob(await r.blob(), "手账.png");
  } catch(e) { alert(e.message); }
  finally { D.btnExport.textContent = "导出 PNG"; D.btnExport.disabled = false; }
}

function exportSVG() {
  const svg = buildClientSVG();
  const blob = new Blob([svg], { type: "image/svg+xml" });
  downloadBlob(blob, "手账.svg");
}

function downloadBlob(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name; a.click();
  URL.revokeObjectURL(a.href);
}

function buildPayload() {
  return {
    width: state.canvas.w, height: state.canvas.h, background: state.canvas.bg,
    elements: state.elements.map(el => ({
      id: el.id, type: el.type, x: el.x, y: el.y, w: el.w, h: el.h,
      rotation: el.rotation||0, opacity: el.opacity,
      text: el.text, family: el.family, size: el.size, weight: el.weight, color: el.color, align: el.align,
      src: el.src,
    })),
  };
}

function buildClientSVG() {
  const esc = (s) => String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  const fv = (v) => v === Math.floor(v) ? String(v) : v.toFixed(3).replace(/0+$/,"").replace(/\.$/,"");
  let parts = [`<svg xmlns="http://www.w3.org/2000/svg" width="${state.canvas.w}" height="${state.canvas.h}" viewBox="0 0 ${state.canvas.w} ${state.canvas.h}">`,
    `<rect width="${state.canvas.w}" height="${state.canvas.h}" fill="${esc(state.canvas.bg)}"/>`];
  if (D.bgPattern.innerHTML) parts.push(D.bgPattern.innerHTML);
  state.elements.forEach(el => {
    parts.push(`<g transform="translate(${fv(el.x)},${fv(el.y)}) rotate(${fv(el.rotation||0)},${fv(el.w/2)},${fv(el.h/2)})" opacity="${fv(el.opacity)}">`);
    if (el.type === "text") {
      const anc = {left:"start",center:"middle",right:"end"}[el.align||"left"];
      const xm = {left:0,center:fv(el.w/2),right:fv(el.w)};
      parts.push(`<text x="${xm[el.align||'left']}" y="${fv((el.size||24)*0.8)}" font-family="${esc(el.family||'sans-serif')}" font-size="${fv(el.size||24)}" font-weight="${el.weight||400}" fill="${esc(el.color||'#333')}" text-anchor="${anc}">${esc(el.text||'')}</text>`);
    } else if (el.type === "sticker") {
      parts.push(`<image href="${esc(el.src)}" width="${fv(el.w)}" height="${fv(el.h)}" preserveAspectRatio="xMidYMid meet"/>`);
    }
    parts.push("</g>");
  });
  parts.push("</svg>");
  return parts.join("\n");
}

// ====== 启动 ======
init();
