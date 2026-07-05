<script setup>
import { useEditor } from "../stores/editor.js";

const store = useEditor();

function addSticker(sticker) {
  store.addElement({
    type: "sticker",
    x: Math.round(store.canvas.width / 2 - 50),
    y: Math.round(store.canvas.height / 2 - 50),
    w: 80,
    h: 80,
    rotation: 0,
    src: sticker.thumb,
    _src: sticker.src,
    style: { font: {}, opacity: 1 },
  });
}
</script>

<template>
  <div class="p-4 space-y-3">
    <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase">
      贴纸
    </h3>

    <div class="flex gap-1 flex-wrap">
      <button
        v-for="cat in store.stickerCategories"
        :key="cat"
        @click="store.activeCategory = cat"
        :class="[
          'px-2 py-1 text-xs rounded transition-colors capitalize',
          store.activeCategory === cat
            ? 'bg-ink text-white'
            : 'text-muted hover:bg-hover',
        ]"
      >
        {{ cat }}
      </button>
    </div>

    <div class="grid grid-cols-3 gap-2">
      <div
        v-for="s in store.stickerData[store.activeCategory] || []"
        :key="s.src"
        @click="addSticker(s)"
        class="bg-white rounded border border-border/50 p-2 cursor-pointer hover:border-accent hover:shadow-sm transition-all flex flex-col items-center gap-1"
        :title="s.name"
      >
        <img :src="s.thumb" class="w-10 h-10 object-contain pointer-events-none" />
        <span class="text-[10px] text-muted truncate w-full text-center">
          {{ s.name }}
        </span>
      </div>
    </div>

    <p class="text-[11px] text-muted leading-relaxed pt-1">
      点击贴纸添加到画布中央，选中后在画布上拖拽移动和缩放
    </p>
  </div>
</template>
