<script setup>
import { ref } from "vue";
import { useEditor } from "../stores/editor.js";

const store = useEditor();

const bgColors = [
  { hex: "#fbfaf6", name: "暖白" },
  { hex: "#ffffff", name: "纯白" },
  { hex: "#f5f0e8", name: "牛皮纸" },
  { hex: "#f2f7f2", name: "薄荷" },
  { hex: "#1a1a2e", name: "深蓝" },
  { hex: "#0a0e14", name: "纯黑" },
  { hex: "#fdf6e3", name: "奶油" },
  { hex: "#faf0e6", name: "亚麻" },
];

const patterns = [
  { id: "none", name: "无" },
  { id: "lines", name: "横线" },
  { id: "grid", name: "网格" },
  { id: "dots", name: "点阵" },
];
</script>

<template>
  <div class="p-4 space-y-4">
    <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase">
      画布预设
    </h3>

    <!-- Presets -->
    <div class="space-y-1" v-if="store.presets">
      <button
        v-for="p in store.presets.canvases"
        :key="p.id"
        @click="store.applyPreset(p)"
        class="w-full text-left px-3 py-2 rounded text-sm hover:bg-hover transition-colors"
        :class="{
          'bg-hover ring-1 ring-accent':
            store.canvas.width === p.width &&
            store.canvas.height === p.height,
        }"
      >
        <div class="font-medium">{{ p.name }}</div>
        <div class="text-xs text-muted">{{ p.width }} × {{ p.height }}</div>
      </button>
    </div>

    <!-- Custom size -->
    <div>
      <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase mb-2">
        自定义
      </h3>
      <div class="flex gap-2">
        <input
          type="number"
          :value="store.canvas.width"
          @change="
            store.setCanvasSize(
              Number($event.target.value),
              store.canvas.height
            )
          "
          class="w-full px-2 py-1 border border-border rounded text-sm bg-white/70"
          placeholder="宽"
        />
        <span class="text-muted self-center">×</span>
        <input
          type="number"
          :value="store.canvas.height"
          @change="
            store.setCanvasSize(
              store.canvas.width,
              Number($event.target.value)
            )
          "
          class="w-full px-2 py-1 border border-border rounded text-sm bg-white/70"
          placeholder="高"
        />
      </div>
    </div>

    <!-- Background color -->
    <div>
      <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase mb-2">
        背景色
      </h3>
      <div class="grid grid-cols-4 gap-2">
        <button
          v-for="c in bgColors"
          :key="c.hex"
          @click="store.setCanvas({ background: c.hex })"
          :class="[
            'w-full aspect-square rounded border-2 transition-colors',
            store.canvas.background === c.hex
              ? 'border-accent'
              : 'border-border/50',
          ]"
          :style="{ background: c.hex }"
          :title="c.name"
        />
      </div>
    </div>

    <!-- Pattern -->
    <div>
      <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase mb-2">
        底纹
      </h3>
      <div class="flex gap-1">
        <button
          v-for="p in patterns"
          :key="p.id"
          @click="store.setCanvas({ pattern: p.id })"
          :class="[
            'px-3 py-1.5 rounded text-sm transition-colors',
            store.canvas.pattern === p.id
              ? 'bg-ink text-white'
              : 'text-muted hover:bg-hover',
          ]"
        >
          {{ p.name }}
        </button>
      </div>
    </div>
  </div>
</template>
