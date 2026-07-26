<script setup>
import { ref, computed, watch } from "vue";
import { useEditor } from "../stores/editor.js";
import { wrapText, hasMarkup, parseRichText, wrapSpans, spanWidth } from "../engine/text.js";

const props = defineProps({ element: Object, scale: Number });
const store = useEditor();

const isSelected = computed(() => store.selectedId === props.element.id);
const isSticker = computed(() => props.element.type === "sticker");
const isImage = computed(() => props.element.type === "image");
const isVisual = computed(() => isSticker.value || isImage.value);
const isText = computed(() => props.element.type === "text");
const showHandles = computed(() => isSelected.value && (isVisual.value || isText.value));

const isDragging = ref(false);
const isResizing = ref(false);
const isRotating = ref(false);
const interactionSvg = ref(null);
const dragStart = ref({ x: 0, y: 0 });
const dragRef = ref({ x: 0, y: 0, w: 0, h: 0, rotation: 0 });
const elScale = computed(() => props.scale || 1);
const handleSize = computed(() => 12 / elScale.value);
const handleHalf = computed(() => handleSize.value / 2);
const handleRadius = computed(() => 7 / elScale.value);
const rotateGap = computed(() => 30 / elScale.value);
const controlStroke = computed(() => 1.5 / elScale.value);

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

function richLineX(spans) {
  const width = spans.reduce((sum, span) => sum + spanWidth(span, fsize.value, fls.value), 0);
  if (falign.value === "center") return (boxW.value - width) / 2;
  if (falign.value === "right") return boxW.value - width;
  return 0;
}

function richSpanX(spans, index) {
  return richLineX(spans) + spans
    .slice(0, index)
    .reduce((sum, span) => sum + spanWidth(span, fsize.value, fls.value), 0);
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
  const svgEl = e.target?.ownerSVGElement || e.currentTarget?.ownerSVGElement || interactionSvg.value;
  if (!svgEl) return { x: 0, y: 0 };
  const r = svgEl.getBoundingClientRect();
  return { x: (e.clientX - r.left) / elScale.value, y: (e.clientY - r.top) / elScale.value };
}

// ── Move ──
function onMoveStart(e) {
  if (isResizing.value || isRotating.value) return;
  store.selectElement(props.element.id);
  interactionSvg.value = e.currentTarget?.ownerSVGElement || e.target?.ownerSVGElement;
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
function onMoveEnd(e) {
  if (!isDragging.value) return;
  isDragging.value = false;
  interactionSvg.value = null;
  store.saveHistory();
  document.removeEventListener("mousemove", onMove);
  document.removeEventListener("mouseup", onMoveEnd);
}

// ── Resize ──
function onResizeStart(e, corner) {
  isResizing.value = true;
  interactionSvg.value = e.currentTarget?.ownerSVGElement || e.target?.ownerSVGElement;
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
      nw = Math.max(30, ref.w + (c.includes("e") ? dx : -dx));
      nh = nw * ratio;
    } else {
      nh = Math.max(20, ref.h + (c.includes("s") ? dy : -dy));
      nw = nh / ratio;
    }
    if (c.includes("w")) nx = ref.cx + ref.w - nw;
    if (c.includes("n")) ny = ref.cy + ref.h - nh;
  } else {
    if (c.includes("e")) nw = Math.max(30, ref.w + dx);
    if (c.includes("w")) { nw = Math.max(30, ref.w - dx); nx = ref.cx + ref.w - nw; }
    if (c.includes("s")) nh = Math.max(20, ref.h + dy);
    if (c.includes("n")) { nh = Math.max(20, ref.h - dy); ny = ref.cy + ref.h - nh; }
  }
  store.updateElement(el.value.id, { x: Math.round(nx), y: Math.round(ny), w: Math.round(nw), h: Math.round(nh) }, true);
}
function onResizeEnd() {
  if (!isResizing.value) return;
  isResizing.value = false;
  interactionSvg.value = null;
  store.saveHistory();
  document.removeEventListener("mousemove", onResize);
  document.removeEventListener("mouseup", onResizeEnd);
}

// ── Rotate ──
function onRotateStart(e) {
  isRotating.value = true;
  interactionSvg.value = e.currentTarget?.ownerSVGElement || e.target?.ownerSVGElement;
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
  store.updateElement(el.value.id, { rotation: Math.round(angle) }, true);
}
function onRotateEnd() {
  if (!isRotating.value) return;
  isRotating.value = false;
  interactionSvg.value = null;
  store.saveHistory();
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
        :letter-spacing="fls || undefined"
      >{{ line }}</text>
    </template>

    <!-- Text: rich (spans) -->
    <template v-if="element.type === 'text' && element.text && hasRich">
      <text
        v-for="(spans, li) in allLines"
        :key="'r'+li"
        text-anchor="start"
        :opacity="element.style?.opacity || 1"
        :letter-spacing="fls || undefined"
      >
        <tspan
          v-for="(sp, si) in spans"
          :key="si"
          :x="richSpanX(spans, si)"
          :y="startY + li * fsize * fline"
          :font-family="quotedFamily(ffam)"
          :font-size="sp.size || fsize"
          :font-weight="sp.bold ? 700 : fweight"
          :font-style="sp.italic ? 'italic' : 'normal'"
          :fill="sp.color || fcolor"
          :text-decoration="sp.underline ? 'underline' : undefined"
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

    <!-- Image -->
    <image
      v-if="element.type === 'image' && element.src"
      :href="element.src"
      :width="element.w"
      :height="element.h"
      preserveAspectRatio="xMidYMid meet"
      :opacity="element.style?.opacity || 1"
    />

    <!-- Selection border -->
    <rect
      v-if="isSelected"
      x="0" y="0"
      :width="element.w || 200"
      :height="element.h || 80"
      fill="none"
      stroke="#d98c72"
      :stroke-width="controlStroke"
      rx="1"
      pointer-events="none"
    />

    <!-- Resize and rotation controls -->
    <template v-if="showHandles">
      <rect :x="-handleHalf" :y="-handleHalf" :width="handleSize" :height="handleSize" fill="#fffdf8" stroke="#d98c72" :stroke-width="controlStroke" :rx="2 / elScale"
            class="cursor-nwse-resize" @mousedown.stop.prevent="onResizeStart($event, 'nw')" />
      <rect :x="element.w - handleHalf" :y="-handleHalf" :width="handleSize" :height="handleSize" fill="#fffdf8" stroke="#d98c72" :stroke-width="controlStroke" :rx="2 / elScale"
            class="cursor-nesw-resize" @mousedown.stop.prevent="onResizeStart($event, 'ne')" />
      <rect :x="-handleHalf" :y="element.h - handleHalf" :width="handleSize" :height="handleSize" fill="#fffdf8" stroke="#d98c72" :stroke-width="controlStroke" :rx="2 / elScale"
            class="cursor-nesw-resize" @mousedown.stop.prevent="onResizeStart($event, 'sw')" />
      <rect :x="element.w - handleHalf" :y="element.h - handleHalf" :width="handleSize" :height="handleSize" fill="#fffdf8" stroke="#d98c72" :stroke-width="controlStroke" :rx="2 / elScale"
            class="cursor-nwse-resize" @mousedown.stop.prevent="onResizeStart($event, 'se')" />

      <line :x1="element.w / 2" :y1="0" :x2="element.w / 2" :y2="-rotateGap" stroke="#d98c72" :stroke-width="controlStroke" pointer-events="none" />
      <circle :cx="element.w / 2" :cy="-rotateGap" :r="handleRadius" fill="#fffdf8" stroke="#d98c72" :stroke-width="controlStroke"
              class="cursor-grab" @mousedown.stop.prevent="onRotateStart" />
    </template>
  </g>
</template>
