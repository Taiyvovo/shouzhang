<script setup>
import { computed } from "vue";
import { useEditor } from "../stores/editor.js";
import BackgroundPanel from "./BackgroundPanel.vue";
import TextPanel from "./TextPanel.vue";
import StickerPanel from "./StickerPanel.vue";
import ImagePanel from "./ImagePanel.vue";
import LayerPanel from "./LayerPanel.vue";

const store = useEditor();
const panels = {
  background: BackgroundPanel,
  text: TextPanel,
  sticker: StickerPanel,
  image: ImagePanel,
  layer: LayerPanel,
};
const panelTitles = {
  background: ["画布设置", "尺寸、纸色与底纹"],
  text: ["文字排版", "字体、对齐与内容"],
  sticker: ["贴纸素材", "点一下放到画布中央"],
  image: ["图片素材", "上传照片或使用素材库"],
  layer: ["图层管理", "调整顺序、显示与删除"],
};
const currentPanel = computed(() => panels[store.activeTool] || TextPanel);
const currentTitle = computed(() => panelTitles[store.activeTool] || panelTitles.text);
</script>

<template>
  <aside
    class="w-80 shrink-0 bg-paper/95 border-r border-border overflow-hidden flex flex-col shadow-sm z-[1]"
  >
    <div class="px-5 pt-5 pb-4 border-b border-border/60">
      <p class="text-sm font-semibold text-ink">{{ currentTitle[0] }}</p>
      <p class="text-[11px] text-muted mt-1">{{ currentTitle[1] }}</p>
    </div>
    <div class="flex-1 overflow-y-auto panel-scroll">
      <Transition name="panel" mode="out-in">
        <component :is="currentPanel" :key="store.activeTool" />
      </Transition>
    </div>
  </aside>
</template>
