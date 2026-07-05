<script setup>
import { useEditor } from "../stores/editor.js";
import BackgroundPanel from "./BackgroundPanel.vue";
import TextPanel from "./TextPanel.vue";
import StickerPanel from "./StickerPanel.vue";
import LayerPanel from "./LayerPanel.vue";

const store = useEditor();
</script>

<template>
  <aside
    class="w-72 shrink-0 bg-white/60 border-r border-border overflow-y-auto flex flex-col"
  >
    <BackgroundPanel v-if="store.activeTool === 'background'" />
    <TextPanel v-if="store.activeTool === 'text'" />
    <StickerPanel v-if="store.activeTool === 'sticker'" />
    <LayerPanel v-if="store.activeTool === 'layer'" />
  </aside>
</template>
