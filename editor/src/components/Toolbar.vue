<script setup>
import { ref } from "vue";
import { useEditor } from "../stores/editor.js";
import ExportDialog from "./ExportDialog.vue";

const store = useEditor();
const showExport = ref(false);

const tools = [
  { id: "background", label: "背景", icon: "▦" },
  { id: "text", label: "文字", icon: "T" },
  { id: "sticker", label: "贴纸", icon: "✦" },
  { id: "layer", label: "图层", icon: "☰" },
];

function handleCanvasClick() {
  store.deselectAll();
}
</script>

<template>
  <header
    class="h-12 flex items-center px-4 border-b border-border bg-white/80 backdrop-blur shrink-0 gap-1 select-none"
  >
    <span class="text-base font-semibold tracking-wide text-ink/80 mr-4"
      >手账编辑器</span
    >

    <button
      v-for="t in tools"
      :key="t.id"
      @click="store.activeTool = t.id"
      :class="[
        'px-3 py-1.5 rounded text-sm transition-colors',
        store.activeTool === t.id
          ? 'bg-ink text-white'
          : 'text-muted hover:bg-hover hover:text-ink',
      ]"
    >
      <span class="mr-1">{{ t.icon }}</span>
      {{ t.label }}
    </button>

    <div class="flex-1" />

    <button
      @click="store.undo()"
      class="px-2 py-1 text-muted hover:text-ink text-sm"
      title="撤销"
    >
      ↩
    </button>
    <button
      @click="store.redo()"
      class="px-2 py-1 text-muted hover:text-ink text-sm mr-2"
      title="重做"
    >
      ↪
    </button>

    <button
      @click="showExport = true"
      class="px-4 py-1.5 rounded bg-accent text-white text-sm font-medium hover:opacity-90 transition-opacity"
    >
      导出
    </button>
  </header>

  <ExportDialog v-if="showExport" @close="showExport = false" />
</template>
