<script setup>
import { ref, computed, watch, onMounted, nextTick } from "vue";
import { useEditor } from "../stores/editor.js";
import CanvasElement from "./CanvasElement.vue";

const store = useEditor();

const container = ref(null);
const defsRef = ref(null);
const canvasScale = ref(0.5);
const clickOrigin = ref({ x: 0, y: 0 });

const svgWidth = computed(() => store.canvas.width * canvasScale.value);
const svgHeight = computed(() => store.canvas.height * canvasScale.value);

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

function onWheel(e) {
  if (e.ctrlKey) return; // Ctrl+scroll = browser default (page pan)
  e.preventDefault();
  const delta = e.deltaY > 0 ? -0.05 : 0.05;
  canvasScale.value = Math.max(0.2, Math.min(1.5, canvasScale.value + delta));
}
</script>

<template>
  <main
    ref="container"
    class="flex-1 overflow-auto flex items-start justify-center p-6 bg-panel/50"
    @wheel="onWheel"
  >
    <div
      :style="{ width: svgWidth + 'px', height: svgHeight + 'px' }"
    >
      <svg
        :width="svgWidth"
        :height="svgHeight"
        :viewBox="`0 0 ${store.canvas.width} ${store.canvas.height}`"
        xmlns="http://www.w3.org/2000/svg"
        class="shadow-xl ring-1 ring-border/50"
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

    <div
      class="fixed bottom-3 right-3 bg-white/80 text-xs text-muted px-2 py-1 rounded shadow"
    >
      {{ Math.round(canvasScale * 100) }}%
    </div>
  </main>
</template>
