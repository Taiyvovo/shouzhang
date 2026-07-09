<script setup>
import { ref, computed, watch } from "vue";
import { useEditor } from "../stores/editor.js";
import { wrapText, hasMarkup, parseRichText, wrapSpans } from "../engine/text.js";

const props = defineProps({ element: Object, scale: Number });
const store = useEditor();

const isSelected = computed(() => store.selectedId === props.element.id);
const isSticker = computed(() => props.element.type === "sticker");
const isText = computed(() => props.element.type === "text");
const showHandles = computed(() => isSelected.value && (isSticker.value || (isText.value && el.value.text)));

const isDragging = ref(false);
const isResizing = ref(false);
const isRotating = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const dragRef = ref({ x: 0, y: 0, w: 0, h: 0, rotation: 0 });
const elScale = computed(() => props.scale || 1);

// ── Text helpers ──
const el = computed(() => props.element);
const font = computed(() => el.value.style?.font || {});
const fsize = computed(() => font.value.size || 36);
const fweight = computed(() => font.value.weight || 400);
const fcolor = computed(() => font.value.color || "#333");
const fline = computed(() => font.value.line_height || 1.6);
const fls = computed(() => font.value.letter_spacing || 0);
const ffam = computed(() => font.value.family || "sans-serif");
const falign = computed(() => el.value.align || "left");
const fvalign = computed(() => el.value.valign || "top");
const boxW = computed(() => el.value.w || 600);
const boxH = computed(() => el.value.h || 120);

function quotedFamily(fam) {
  if (!fam) return "sans-serif";
  return fam.includes(" ") ? `'${fam}'` : fam;
}

// ── Wrapped text (plain) ──
const wrappedText = computed(() => {
  if (el.value.type !== "text" || !el.value.text) return [];
  if (hasMarkup(el.value.text)) return [];
  const wrapped = wrapText(el.value.text, fsize.value, boxW.value, fls.value);
  return wrapped.split("\n");
});

// ── Rich text spans ──
const richLines = computed(() => {
  if (el.value.type !== "text" || !el.value.text) return [];
  if (!hasMarkup(el.value.text)) return [];
  const spans = parseRichText(el.value.text);
  return wrapSpans(spans, fsize.value, boxW.value, fls.value);
});

// ── Active lines (whichever mode) ──
const hasRich = computed(() => hasMarkup(el.value.text));
const allLines = computed(() => hasRich.value ? richLines.value : wrappedText.value);
const lineCount = computed(() => allLines.value.length || 1);

// ── Alignment ──
const totalH = computed(() => lineCount.value * fsize.value * fline.value);
const ascent = computed(() => fsize.value * 0.8);
const startY = computed(() => {
  if (fvalign.value === "middle") return (boxH.value - totalH.value) / 2 + ascent.value;
  if (fvalign.value === "bottom") return boxH.value - totalH.value + ascent.value;
  return ascent.value; // top
});

const anchor = computed(() => {
  if (falign.value === "center") return "middle";
  if (falign.value === "right") return "end";
  return "start";
});

function textX() {
  if (falign.value === "center") return boxW.value / 2;
  if (falign.value === "right") return boxW.value;
  return 0;
}

// ── Auto-resize text box height ──
watch([totalH, lineCount], () => {
  if (!isText.value || !el.value.text) return;
  const needed = totalH.value + fsize.value * 0.3; // small padding
  if (Math.abs(needed - (el.value.h || 120)) > 4) {
    store.updateElement(el.value.id, { h: Math.round(needed) }, true);
  }
});

// ── SVG position helpers ──
function getSVGPos(e) {
  const svgEl = document.querySelector(".shadow-xl");
  if (!svgEl) return { x: 0, y: 0 };
  const r = svgEl.getBoundingClientRect();
  return { x: (e.clientX - r.left) / elScale.value, y: (e.clientY - r.top) / elScale.value };
}

// ── Move ──
function onMoveStart(e) {
  if (isResizing.value || isRotating.value) return;
  store.selectElement(props.element.id);
  isDragging.value = true;
  const sp = getSVGPos(e);
  dragStart.value = { x: sp.x - props.element.x, y: sp.y - props.element.y };
  e.stopPropagation();
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onMoveEnd);
}
function onMove(e) {
  if (!isDragging.value) return;
  const sp = getSVGPos(e);
  store.updateElement(props.element.id, {
    x: Math.round(sp.x - dragStart.value.x),
    y: Math.round(sp.y - dragStart.value.y),
  }, true);
}
function onMoveEnd() {
  isDragging.value = false;
  store.saveHistory();
  document.removeEventListener("mousemove", onMove);
  document.removeEventListener("mouseup", onMoveEnd);
}

// ── Resize ──
function onResizeStart(e, corner) {
  isResizing.value = true;
  const sp = getSVGPos(e);
  dragRef.value = { x: sp.x, y: sp.y, w: el.value.w, h: el.value.h, cx: el.value.x, cy: el.value.y, corner };
  dragStart.value = { x: sp.x, y: sp.y };
  e.stopPropagation(); e.preventDefault();
  document.addEventListener("mousemove", onResize);
  document.addEventListener("mouseup", onResizeEnd);
}
function onResize(e) {
  if (!isResizing.value) return;
  const sp = getSVGPos(e);
  const dx = sp.x - dragStart.value.x;
  const dy = sp.y - dragStart.value.y;
  const ref = dragRef.value;
  const c = ref.corner || "se";
  const ratio = ref.h / ref.w || 1;
  let nx = ref.cx, ny = ref.cy, nw = ref.w, nh = ref.h;

  if (e.shiftKey) {
    // Proportional: use the larger of the two deltas
    const adx = Math.abs(dx), ady = Math.abs(dy);
    if (adx > ady || c === "e" || c === "w") {
      const dir = c.includes("e") ? 1 : -1;
      nw = Math.max(30, ref.w + dx * dir * (c.includes("e")?1:-1));
      nh = nw * ratio;
    } else {
      const dir = c.includes("s") ? 1 : -1;
      nh = Math.max(20, ref.h + dy * dir * (c.includes("s")?1:-1));
      nw = nh / ratio;
    }
  } else {
    if (c.includes("e")) nw = Math.max(30, ref.w + dx);
    if (c.includes("w")) { nx = ref.cx + dx; nw = Math.max(30, ref.w - dx); }
    if (c.includes("s")) nh = Math.max(20, ref.h + dy);
    if (c.includes("n")) { ny = ref.cy + dy; nh = Math.max(20, ref.h - dy); }
  }
  store.updateElement(el.value.id, { x: Math.round(nx), y: Math.round(ny), w: Math.round(nw), h: Math.round(nh) }, true);
}
function onResizeEnd() {
  isResizing.value = false;
  store.saveHistory();
  document.removeEventListener("mousemove", onResize);
  document.removeEventListener("mouseup", onResizeEnd);
}

// ── Rotate ──
function onRotateStart(e) {
  isRotating.value = true;
  e.stopPropagation(); e.preventDefault();
  document.addEventListener("mousemove", onRotate);
  document.addEventListener("mouseup", onRotateEnd);
}
function onRotate(e) {
  if (!isRotating.value) return;
  const sp = getSVGPos(e);
  const cx = el.value.x + el.value.w / 2;
  const cy = el.value.y + el.value.h / 2;
  const angle = Math.atan2(sp.y - cy, sp.x - cx) * (180 / Math.PI) + 90;
  store.updateElement(el.value.id, { rotation: Math.round(angle) });
}
function onRotateEnd() {
  isRotating.value = false;
  document.removeEventListener("mousemove", onRotate);
  document.removeEventListener("mouseup", onRotateEnd);
}

function onDoubleClick(e) {
  if (el.value.type === "text") {
    store.selectElement(el.value.id);
    store.activeTool = "text";
    e.stopPropagation();
  }
}

// ── Sticker viewBox ──
const stickerViewBox = computed(() => {
  if (el.value.type !== "sticker") return null;
  const src = el.value.src || "";
  const m = src.match(/viewBox="([^"]+)"/);
  if (m) {
    const parts = m[1].split(/\s+/);
    if (parts.length >= 4) return { w: Number(parts[2]), h: Number(parts[3]) };
  }
  return null;
});
</script>

<template>
  <g
    v-if="element.visible !== false"
    :transform="`translate(${element.x},${element.y}) rotate(${element.rotation || 0},${element.w/2},${element.h/2})`"
    :class="{ 'cursor-move': !isResizing && !isRotating }"
    @mousedown="onMoveStart"
    @dblclick="onDoubleClick"
  >
    <!-- Text: placeholder when empty -->
    <rect
      v-if="element.type === 'text' && !element.text"
      :width="element.w"
      :height="element.h"
      fill="rgba(232,168,56,0.08)"
      stroke="#e8a838"
      stroke-width="1"
      stroke-dasharray="4"
      rx="2"
    />

    <!-- Text: plain (wrapped) -->
    <template v-if="element.type === 'text' && element.text && !hasRich">
      <text
        v-for="(line, li) in allLines"
        :key="'p'+li"
        :x="textX()"
        :y="startY + li * fsize * fline"
        :font-family="quotedFamily(ffam)"
        :font-size="fsize"
        :font-weight="fweight"
        :fill="fcolor"
        :text-anchor="anchor"
        :opacity="element.style?.opacity || 1"
      >{{ line }}</text>
    </template>

    <!-- Text: rich (spans) -->
    <template v-if="element.type === 'text' && element.text && hasRich">
      <text
        v-for="(spans, li) in allLines"
        :key="'r'+li"
        :text-anchor="anchor"
        :opacity="element.style?.opacity || 1"
      >
        <tspan
          v-for="(sp, si) in spans"
          :key="si"
          :x="textX()"
          :y="startY + li * fsize * fline"
          :font-family="quotedFamily(ffam)"
          :font-size="sp.size || fsize"
          :font-weight="sp.bold ? 700 : fweight"
          :font-style="sp.italic ? 'italic' : 'normal'"
          :fill="sp.color || fcolor"
        >{{ sp.text }}</tspan>
      </text>
    </template>

    <!-- Sticker -->
    <image
      v-if="element.type === 'sticker' && element.src"
      :href="element.src"
      :width="element.w"
      :height="element.h"
      :preserveAspectRatio="stickerViewBox ? 'xMidYMid meet' : 'none'"
      :opacity="element.style?.opacity || 1"
    />

    <!-- Selection border -->
    <rect
      v-if="isSelected"
      x="0" y="0"
      :width="element.w || 200"
      :height="element.h || 80"
      fill="none"
      stroke="#e8a838"
      stroke-width="1.5"
      rx="1"
      pointer-events="none"
    />

    <!-- Resize handles (text & sticker) -->
    <template v-if="showHandles">
      <rect x="-7" y="-7" width="14" height="14" fill="white" stroke="#e8a838" stroke-width="2" rx="2"
            class="cursor-nwse-resize" @mousedown.stop="onResizeStart($event, 'nw')" />
      <rect :x="element.w - 7" y="-7" width="14" height="14" fill="white" stroke="#e8a838" stroke-width="2" rx="2"
            class="cursor-nesw-resize" @mousedown.stop="onResizeStart($event, 'ne')" />
      <rect x="-7" :y="element.h - 7" width="14" height="14" fill="white" stroke="#e8a838" stroke-width="2" rx="2"
            class="cursor-nesw-resize" @mousedown.stop="onResizeStart($event, 'sw')" />
      <rect :x="element.w - 7" :y="element.h - 7" width="14" height="14" fill="white" stroke="#e8a838" stroke-width="2" rx="2"
            class="cursor-nwse-resize" @mousedown.stop="onResizeStart($event, 'se')" />

      <!-- Rotation handle (sticker only) -->
      <template v-if="isSticker">
        <line :x1="element.w / 2" :y1="0" :x2="element.w / 2" :y2="-30" stroke="#e8a838" stroke-width="1" pointer-events="none" />
        <circle :cx="element.w / 2" :cy="-34" r="7" fill="white" stroke="#e8a838" stroke-width="2"
                class="cursor-grab" @mousedown.stop="onRotateStart" />
      </template>
    </template>
  </g>
</template>
