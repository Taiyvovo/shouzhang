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
  // Don't intercept when editing text
  const tag = document.activeElement?.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || document.activeElement?.isContentEditable) return;

  if (e.key === "Delete" || e.key === "Backspace") {
    if (store.selectedId) {
      store.removeElement(store.selectedId);
      e.preventDefault();
    }
  }
  // Undo / Redo
  if (e.ctrlKey && e.key === "z" && !e.shiftKey) {
    e.preventDefault(); store.undo();
  }
  if ((e.ctrlKey && e.key === "y") || (e.ctrlKey && e.shiftKey && e.key === "z")) {
    e.preventDefault(); store.redo();
  }
  // Arrow keys (only when no input focused)
  if (e.key === "ArrowLeft") {
    e.preventDefault(); store.undo();
  }
  if (e.key === "ArrowRight") {
    e.preventDefault(); store.redo();
  }
  if (e.key === "ArrowUp" && store.selectedId) {
    e.preventDefault(); store.moveUp(store.selectedId);
  }
  if (e.key === "ArrowDown" && store.selectedId) {
    e.preventDefault(); store.moveDown(store.selectedId);
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
