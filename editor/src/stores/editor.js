import { defineStore } from "pinia";
import { ref, computed } from "vue";

let _uid = 0;
function uid() {
  return `el_${++_uid}_${Date.now().toString(36)}`;
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

  // ── History (undo) ──
  const history = ref([]);
  const historyIndex = ref(-1);

  // ── Fonts / Stickers / Presets (loaded from API) ──
  const fontFamilies = ref([]);
  const stickerData = ref({});
  const presets = ref(null);

  // ── Computed ──
  const sortedElements = computed(() =>
    [...elements.value].sort((a, b) => a.z_index - b.z_index)
  );

  const selected = computed(() =>
    elements.value.find((e) => e.id === selectedId.value) || null
  );

  const stickerCategories = computed(() => Object.keys(stickerData.value));

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
    const el = elements.value.find((e) => e.id === id);
    if (!el) return;
    el.z_index += 1;
    saveHistory();
  }

  function moveDown(id) {
    const el = elements.value.find((e) => e.id === id);
    if (!el || el.z_index <= 0) return;
    el.z_index -= 1;
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
    history.value.push(JSON.parse(JSON.stringify(elements.value)));
    historyIndex.value = history.value.length - 1;
    if (history.value.length > 50) {
      history.value.shift();
      historyIndex.value--;
    }
  }

  function undo() {
    if (historyIndex.value <= 0) return;
    historyIndex.value--;
    elements.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]));
  }

  function redo() {
    if (historyIndex.value >= history.value.length - 1) return;
    historyIndex.value++;
    elements.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]));
  }

  // ── Serialize for export ──
  function toRenderPayload() {
    return {
      canvas: canvas.value,
      elements: elements.value.map((e) => ({
        id: e.id,
        type: e.type,
        x: e.x,
        y: e.y,
        w: e.w,
        h: e.h,
        rotation: e.rotation || 0,
        z_index: e.z_index || 0,
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

  async function loadPresets() {
    const r = await fetch("/api/presets");
    presets.value = await r.json();
  }

  return {
    canvas,
    elements,
    activeTool,
    activeCategory,
    selectedId,
    selected,
    fontFamilies,
    stickerData,
    stickerCategories,
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
    toRenderPayload,
    loadFonts,
    loadStickers,
    loadPresets,
  };
});
