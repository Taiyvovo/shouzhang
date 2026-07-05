<script setup>
import { onMounted, onUnmounted } from "vue";
import { useEditor } from "./stores/editor.js";
import Toolbar from "./components/Toolbar.vue";
import Sidebar from "./components/Sidebar.vue";
import Canvas from "./components/Canvas.vue";

const store = useEditor();

onMounted(async () => {
  await Promise.all([
    store.loadFonts(),
    store.loadStickers(),
    store.loadPresets(),
  ]);
});

function onKeyDown(e) {
  // Delete / Backspace → remove selected element
  if ((e.key === "Delete" || e.key === "Backspace") && store.selectedId) {
    const tag = document.activeElement?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    store.removeElement(store.selectedId);
    e.preventDefault();
  }
  // Ctrl+Z → undo
  if (e.ctrlKey && e.key === "z" && !e.shiftKey) {
    e.preventDefault();
    store.undo();
  }
  // Ctrl+Shift+Z or Ctrl+Y → redo
  if ((e.ctrlKey && e.key === "y") || (e.ctrlKey && e.shiftKey && e.key === "z")) {
    e.preventDefault();
    store.redo();
  }
}

onMounted(() => document.addEventListener("keydown", onKeyDown));
onUnmounted(() => document.removeEventListener("keydown", onKeyDown));
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden">
    <Toolbar />
    <div class="flex flex-1 overflow-hidden">
      <Sidebar />
      <Canvas />
    </div>
  </div>
</template>
