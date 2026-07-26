<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useEditor } from "../stores/editor.js";
import CanvasElement from "./CanvasElement.vue";

const store = useEditor();

const container = ref(null);
const defsRef = ref(null);
const svgWrapper = ref(null);
const canvasScale = ref(0.5);
const clickOrigin = ref({ x: 0, y: 0 });
const viewportSize = ref({ width: 0, height: 0 });
const isPanning = ref(false);
const spacePressed = ref(false);
const panStart = ref({ x: 0, y: 0, left: 0, top: 0 });
let resizeObserver;

const svgWidth = computed(() => store.canvas.width * canvasScale.value);
const svgHeight = computed(() => store.canvas.height * canvasScale.value);
const stageStyle = computed(() => ({
  width: `${Math.max(viewportSize.value.width, svgWidth.value + 96)}px`,
  height: `${Math.max(viewportSize.value.height, svgHeight.value + 96)}px`,
}));

// ── Dynamic @font-face for used custom fonts ──
function injectFontCSS() {
  const used = new Set();
  const generic = ["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"];
  store.elements.forEach((el) => {
    const fam = el.style?.font?.family;
    if (fam && !generic.includes(fam)) used.add(fam);
  });
  let css = "";
  for (const fam of used) {
    css += `@font-face{font-family:"${fam}";src:url("/api/font-file/${encodeURIComponent(fam)}");}\n`;
  }

  // Inject into SVG <defs>
  const defs = defsRef.value;
  if (defs) {
    let styleEl = defs.querySelector("style");
    if (!styleEl) {
      styleEl = document.createElementNS("http://www.w3.org/2000/svg", "style");
      defs.appendChild(styleEl);
    }
    styleEl.textContent = css;
  }

  // Also inject into HTML <head> for broader scope
  let headStyle = document.getElementById("font-face-inject");
  if (!headStyle) {
    headStyle = document.createElement("style");
    headStyle.id = "font-face-inject";
    document.head.appendChild(headStyle);
  }
  headStyle.textContent = css;
}

watch(
  () => store.elements.map((e) => e.id + e.style?.font?.family).join(","),
  () => nextTick(injectFontCSS),
  { immediate: true }
);

const patternLines = computed(() => {
  const s = store.canvas;
  if (s.pattern === "lines") {
    const lines = [];
    for (let y = 36; y < s.height; y += 36)
      lines.push(`M 0 ${y} L ${s.width} ${y}`);
    return lines.join(" ");
  }
  if (s.pattern === "grid") {
    const lines = [];
    for (let y = 36; y < s.height; y += 36)
      lines.push(`M 0 ${y} L ${s.width} ${y}`);
    for (let x = 36; x < s.width; x += 36)
      lines.push(`M ${x} 0 L ${x} ${s.height}`);
    return lines.join(" ");
  }
  return "";
});

const patternDots = computed(() => {
  if (store.canvas.pattern !== "dots") return "";
  const dots = [];
  for (let y = 36; y < store.canvas.height; y += 36) {
    for (let x = 36; x < store.canvas.width; x += 36) {
      dots.push(`M ${x} ${y} h 0`);
    }
  }
  return dots.join(" ");
});

// ── Click vs drag tracking ──
function onSvgMouseDown(e) {
  clickOrigin.value = { x: e.clientX, y: e.clientY };
}

// Click: if clicking the canvas background (SVG itself or bg rect/path), add text or deselect
function onCanvasClick(e) {
  const dx = Math.abs(e.clientX - clickOrigin.value.x);
  const dy = Math.abs(e.clientY - clickOrigin.value.y);
  if (dx > 3 || dy > 3) return; // dragged, not clicked
  const tag = e.target.tagName;
  // Only react to clicks on background elements (rect, path, svg itself)
  if (["svg", "rect", "path"].includes(tag)) {
    if (store.activeTool === "text") {
      const rect = container.value.getBoundingClientRect();
      const svgEl = container.value.querySelector("svg");
      const svgRect = svgEl.getBoundingClientRect();
      const x = Math.round(
        (e.clientX - svgRect.left) / canvasScale.value
      );
      const y = Math.round(
        (e.clientY - svgRect.top) / canvasScale.value
      );
      store.addElement({
        type: "text",
        x: Math.max(0, x - 10),
        y: Math.max(0, y - 10),
        w: 600,
        h: 120,
        rotation: 0,
        align: "left",
        valign: "top",
        text: "",
        style: {
          font: {
            family: "serif",
            size: 36,
            weight: 400,
            color: "#333333",
            line_height: 1.6,
            letter_spacing: 0,
          },
          opacity: 1,
        },
      });
    } else {
      store.deselectAll();
    }
  }
}

function setZoom(nextScale, clientX, clientY) {
  const viewport = container.value;
  const svg = svgWrapper.value;
  if (!viewport || !svg) return;
  const next = Math.max(0.1, Math.min(4, Math.round(nextScale * 100) / 100));
  if (next === canvasScale.value) return;

  const viewportRect = viewport.getBoundingClientRect();
  const svgRect = svg.getBoundingClientRect();
  const anchorX = clientX ?? viewportRect.left + viewportRect.width / 2;
  const anchorY = clientY ?? viewportRect.top + viewportRect.height / 2;
  const canvasX = (anchorX - svgRect.left) / canvasScale.value;
  const canvasY = (anchorY - svgRect.top) / canvasScale.value;

  canvasScale.value = next;
  nextTick(() => {
    const nextRect = svg.getBoundingClientRect();
    viewport.scrollLeft += nextRect.left + canvasX * next - anchorX;
    viewport.scrollTop += nextRect.top + canvasY * next - anchorY;
  });
}

function zoomBy(amount) {
  setZoom(canvasScale.value + amount);
}

function fitCanvas() {
  const viewport = container.value;
  if (!viewport) return;
  const availableWidth = Math.max(100, viewport.clientWidth - 96);
  const availableHeight = Math.max(100, viewport.clientHeight - 96);
  const next = Math.min(
    availableWidth / store.canvas.width,
    availableHeight / store.canvas.height,
    1,
  );
  canvasScale.value = Math.max(0.1, Math.floor(next * 100) / 100);
  nextTick(() => {
    viewport.scrollLeft = Math.max(0, (viewport.scrollWidth - viewport.clientWidth) / 2);
    viewport.scrollTop = Math.max(0, (viewport.scrollHeight - viewport.clientHeight) / 2);
  });
}

function onWheel(e) {
  const svg = svgWrapper.value;
  if (!svg || !svg.contains(e.target)) return;
  e.preventDefault();
  e.stopPropagation();
  const direction = e.deltaY > 0 ? -1 : 1;
  const step = Math.max(0.05, canvasScale.value * 0.12);
  setZoom(canvasScale.value + direction * step, e.clientX, e.clientY);
}

function onKeyDown(e) {
  if (e.code !== "Space" || ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
  spacePressed.value = true;
  e.preventDefault();
}

function onKeyUp(e) {
  if (e.code === "Space") spacePressed.value = false;
}

function onPanStart(e) {
  if (e.button !== 1 && !(e.button === 0 && spacePressed.value)) return;
  const viewport = container.value;
  if (!viewport) return;
  e.preventDefault();
  e.stopPropagation();
  isPanning.value = true;
  panStart.value = {
    x: e.clientX,
    y: e.clientY,
    left: viewport.scrollLeft,
    top: viewport.scrollTop,
  };
  document.addEventListener("mousemove", onPanMove);
  document.addEventListener("mouseup", onPanEnd);
}

function onPanMove(e) {
  if (!isPanning.value || !container.value) return;
  container.value.scrollLeft = panStart.value.left - (e.clientX - panStart.value.x);
  container.value.scrollTop = panStart.value.top - (e.clientY - panStart.value.y);
}

function onPanEnd() {
  isPanning.value = false;
  document.removeEventListener("mousemove", onPanMove);
  document.removeEventListener("mouseup", onPanEnd);
}

// Use native listener to ensure passive:false (so preventDefault works)
onMounted(() => {
  const el = container.value;
  if (el) {
    el.addEventListener("wheel", onWheel, { passive: false });
    resizeObserver = new ResizeObserver(([entry]) => {
      viewportSize.value = {
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      };
    });
    resizeObserver.observe(el);
  }
  window.addEventListener("keydown", onKeyDown);
  window.addEventListener("keyup", onKeyUp);
  nextTick(fitCanvas);
});
onUnmounted(() => {
  const el = container.value;
  if (el) el.removeEventListener("wheel", onWheel);
  resizeObserver?.disconnect();
  window.removeEventListener("keydown", onKeyDown);
  window.removeEventListener("keyup", onKeyUp);
  document.removeEventListener("mousemove", onPanMove);
  document.removeEventListener("mouseup", onPanEnd);
});
</script>

<template>
  <section class="relative flex-1 min-w-0 overflow-hidden">
    <main
      ref="container"
      class="workspace-bg w-full h-full overflow-auto"
      :class="isPanning ? 'cursor-grabbing select-none' : spacePressed ? 'cursor-grab' : ''"
      @mousedown.capture="onPanStart"
    >
      <div :style="stageStyle" class="flex items-center justify-center">
        <div
          ref="svgWrapper"
          :style="{ width: svgWidth + 'px', height: svgHeight + 'px' }"
          class="canvas-sheet shrink-0"
        >
          <svg
            :width="svgWidth"
            :height="svgHeight"
            :viewBox="`0 0 ${store.canvas.width} ${store.canvas.height}`"
            xmlns="http://www.w3.org/2000/svg"
            class="shadow-2xl ring-1 ring-white/80"
            @click="onCanvasClick"
            @mousedown="onSvgMouseDown"
          >
            <defs ref="defsRef" />

            <rect
              class="background"
              :width="store.canvas.width"
              :height="store.canvas.height"
              :fill="store.canvas.background"
            />

            <path
              v-if="patternLines"
              :d="patternLines"
              fill="none"
              stroke="rgba(160,150,130,0.2)"
              stroke-width="1"
            />

            <path
              v-if="patternDots"
              :d="patternDots"
              fill="none"
              stroke="rgba(160,150,130,0.2)"
              stroke-width="1.5"
              stroke-linecap="round"
            />

            <CanvasElement
              v-for="el in store.sortedElements"
              :key="el.id"
              :element="el"
              :scale="canvasScale"
            />
          </svg>
        </div>
      </div>
    </main>

    <div
      class="absolute bottom-4 right-4 flex items-center gap-1 bg-paper/95 backdrop-blur text-[11px] text-muted p-1 rounded-xl border border-border/70 shadow-md"
    >
      <button class="zoom-button" title="缩小" aria-label="缩小" @click="zoomBy(-0.1)">−</button>
      <button class="min-w-14 px-2 h-8 rounded-lg hover:bg-hover transition-colors" title="适应窗口" @click="fitCanvas">
        {{ Math.round(canvasScale * 100) }}%
      </button>
      <button class="zoom-button" title="放大" aria-label="放大" @click="zoomBy(0.1)">＋</button>
      <span class="w-px h-4 bg-border mx-0.5" />
      <button class="px-2 h-8 rounded-lg hover:bg-hover transition-colors" title="适应窗口" @click="fitCanvas">适应</button>
    </div>
  </section>
</template>
