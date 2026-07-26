import { defineStore } from "pinia";
import { ref, computed } from "vue";

let _uid = 0;
function uid() {
  return `el_${++_uid}_${Date.now().toString(36)}`;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export const useEditor = defineStore("editor", () => {
  // ── Canvas ──
  const canvas = ref({
    width: 1080,
    height: 1527,
    background: "#fbfaf6",
    pattern: "lines",
  });

  // ── Elements ──
  const elements = ref([]);

  // ── Tools ──
  const activeTool = ref("text"); // "background" | "text" | "sticker" | "layer"
  const selectedId = ref(null);
  const activeCategory = ref("emotion");
  const activeImageCategory = ref("basic");
  const projectName = ref("未命名手账");

  // ── History (undo) ──
  const history = ref([{ canvas: clone(canvas.value), elements: [] }]);
  const historyIndex = ref(0);

  // ── Fonts / Stickers / Presets (loaded from API) ──
  const fontFamilies = ref([]);
  const stickerData = ref({});
  const imageData = ref({});
  const presets = ref(null);
  const savedFingerprint = ref(JSON.stringify({
    name: projectName.value,
    canvas: canvas.value,
    elements: [],
  }));

  // ── Computed ──
  const sortedElements = computed(() =>
    [...elements.value].sort((a, b) => a.z_index - b.z_index)
  );

  const selected = computed(() =>
    elements.value.find((e) => e.id === selectedId.value) || null
  );

  const stickerCategories = computed(() => Object.keys(stickerData.value));
  const imageCategories = computed(() => Object.keys(imageData.value));
  const isDirty = computed(() => projectFingerprint() !== savedFingerprint.value);

  function projectFingerprint() {
    return JSON.stringify({
      name: projectName.value,
      canvas: canvas.value,
      elements: elements.value,
    });
  }

  // ── Canvas ──
  function setCanvas(c) {
    canvas.value = { ...canvas.value, ...c };
    saveHistory();
  }

  function applyPreset(preset) {
    canvas.value = { ...canvas.value, ...preset };
    saveHistory();
  }

  function setCanvasSize(w, h) {
    canvas.value.width = w;
    canvas.value.height = h;
    saveHistory();
  }

  // ── Elements CRUD ──
  function addElement(el) {
    // Remove any existing empty text boxes before adding new one
    const empties = elements.value.filter((e) => e.type === "text" && !e.text);
    elements.value = elements.value.filter((e) => e.type !== "text" || e.text);
    const e = { ...el, id: el.id || uid() };
    if (e.z_index === undefined) {
      e.z_index = elements.value.length;
    }
    elements.value.push(e);
    selectedId.value = e.id;
    saveHistory();
    return e;
  }

  function updateElement(id, patch, silent = false) {
    const idx = elements.value.findIndex((e) => e.id === id);
    if (idx === -1) return;
    elements.value[idx] = { ...elements.value[idx], ...patch };
    if (!silent) saveHistory();
  }

  function removeElement(id) {
    elements.value = elements.value.filter((e) => e.id !== id);
    if (selectedId.value === id) selectedId.value = null;
    saveHistory();
  }

  function selectElement(id) {
    // If selecting a different element, cleanup old empty text
    if (selectedId.value && selectedId.value !== id) {
      const old = elements.value.find((e) => e.id === selectedId.value);
      if (old && old.type === "text" && !old.text) {
        removeElement(selectedId.value);
      }
    }
    selectedId.value = id;
  }

  function deselectAll() {
    // Auto-remove empty text boxes
    if (selectedId.value) {
      const el = elements.value.find((e) => e.id === selectedId.value);
      if (el && el.type === "text" && !el.text) {
        removeElement(selectedId.value);
        return;
      }
    }
    selectedId.value = null;
  }

  // ── Layer ops ──
  function moveUp(id) {
    const ordered = sortedElements.value;
    const index = ordered.findIndex((e) => e.id === id);
    if (index === -1 || index === ordered.length - 1) return;
    [ordered[index], ordered[index + 1]] = [ordered[index + 1], ordered[index]];
    ordered.forEach((element, position) => { element.z_index = position; });
    saveHistory();
  }

  function moveDown(id) {
    const ordered = sortedElements.value;
    const index = ordered.findIndex((e) => e.id === id);
    if (index <= 0) return;
    [ordered[index], ordered[index - 1]] = [ordered[index - 1], ordered[index]];
    ordered.forEach((element, position) => { element.z_index = position; });
    saveHistory();
  }

  function toggleVisibility(id) {
    const el = elements.value.find((e) => e.id === id);
    if (!el) return;
    el.visible = !(el.visible !== false);
    saveHistory();
  }

  // ── Undo ──
  function saveHistory() {
    history.value = history.value.slice(0, historyIndex.value + 1);
    history.value.push({
      canvas: clone(canvas.value),
      elements: clone(elements.value),
    });
    historyIndex.value = history.value.length - 1;
    if (history.value.length > 50) {
      history.value.shift();
      historyIndex.value--;
    }
  }

  function undo() {
    if (historyIndex.value <= 0) return;
    historyIndex.value--;
    restoreHistory(history.value[historyIndex.value]);
  }

  function redo() {
    if (historyIndex.value >= history.value.length - 1) return;
    historyIndex.value++;
    restoreHistory(history.value[historyIndex.value]);
  }

  function restoreHistory(snapshot) {
    canvas.value = clone(snapshot.canvas);
    elements.value = clone(snapshot.elements);
    if (!elements.value.some((e) => e.id === selectedId.value)) selectedId.value = null;
  }

  function projectData() {
    return {
      format: "shouzhang-project",
      version: 1,
      name: projectName.value,
      canvas: clone(canvas.value),
      elements: clone(elements.value),
    };
  }

  function markSaved() {
    savedFingerprint.value = projectFingerprint();
  }

  function loadProject(data, fallbackName = "未命名手账") {
    if (!data || data.format !== "shouzhang-project" || data.version !== 1) {
      throw new Error("不是有效的手账工程文件");
    }
    if (!data.canvas || !Array.isArray(data.elements)) {
      throw new Error("工程文件缺少画布或元素数据");
    }
    const width = Number(data.canvas.width);
    const height = Number(data.canvas.height);
    if (!(width > 0 && width <= 10000 && height > 0 && height <= 10000)) {
      throw new Error("工程文件的画布尺寸无效");
    }
    if (data.elements.length > 500) throw new Error("工程文件中的元素过多");
    canvas.value = clone(data.canvas);
    elements.value = clone(data.elements);
    projectName.value = String(data.name || fallbackName).slice(0, 100);
    selectedId.value = null;
    history.value = [{ canvas: clone(canvas.value), elements: clone(elements.value) }];
    historyIndex.value = 0;
    markSaved();
  }

  // ── Serialize for export ──
  function toRenderPayload() {
    return {
      canvas: canvas.value,
      elements: elements.value.filter((e) => e.visible !== false).map((e) => ({
        id: e.id,
        type: e.type,
        x: e.x,
        y: e.y,
        w: e.w,
        h: e.h,
        rotation: e.rotation || 0,
        z_index: e.z_index || 0,
        visible: e.visible !== false,
        align: e.align || "left",
        valign: e.valign || "top",
        style: {
          font: {
            family: e.style?.font?.family || "sans-serif",
            size: e.style?.font?.size || 36,
            weight: e.style?.font?.weight || 400,
            color: e.style?.font?.color || "#333333",
            line_height: e.style?.font?.line_height || 1.6,
            letter_spacing: e.style?.font?.letter_spacing || 0,
          },
          opacity: e.style?.opacity ?? 1,
        },
        text: e.text || "",
        src: e._src || e.src || "",
        file: e._src || "",
        default: e.text || "",
      })),
    };
  }

  // ── Load data from API ──
  async function loadFonts() {
    const r = await fetch("/api/fonts");
    const d = await r.json();
    fontFamilies.value = d.families;
  }

  async function loadStickers() {
    const r = await fetch("/api/stickers");
    const d = await r.json();
    stickerData.value = d.categories;
  }

  async function loadImages() {
    const r = await fetch("/api/images");
    if (!r.ok) throw new Error("图片素材加载失败");
    const d = await r.json();
    imageData.value = d.categories;
    if (!imageData.value[activeImageCategory.value]) {
      activeImageCategory.value = Object.keys(imageData.value)[0] || "basic";
    }
  }

  async function loadPresets() {
    const r = await fetch("/api/presets");
    presets.value = await r.json();
  }

  return {
    canvas,
    elements,
    activeTool,
    activeCategory,
    activeImageCategory,
    projectName,
    selectedId,
    selected,
    fontFamilies,
    stickerData,
    stickerCategories,
    imageData,
    imageCategories,
    isDirty,
    presets,
    sortedElements,
    setCanvas,
    applyPreset,
    setCanvasSize,
    addElement,
    updateElement,
    removeElement,
    selectElement,
    deselectAll,
    moveUp,
    moveDown,
    toggleVisibility,
    saveHistory,
    undo,
    redo,
    projectData,
    markSaved,
    loadProject,
    toRenderPayload,
    loadFonts,
    loadStickers,
    loadImages,
    loadPresets,
  };
});
