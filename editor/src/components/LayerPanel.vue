<script setup>
import { useEditor } from "../stores/editor.js";
const store = useEditor();
</script>

<template>
  <div class="p-4 space-y-1">
    <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase mb-2">图层</h3>

    <div
      v-for="el in store.sortedElements.slice().reverse()"
      :key="el.id"
      @click="store.selectElement(el.id)"
      :class="[
        'flex items-center gap-1 px-2 py-2 rounded text-sm cursor-pointer transition-colors',
        store.selectedId === el.id
          ? 'bg-hover ring-1 ring-accent'
          : 'hover:bg-hover/50',
        el.visible === false ? 'opacity-50' : '',
      ]"
    >
      <span class="text-xs w-5 text-center text-muted shrink-0">
        {{ el.type === "text" ? "T" : el.type === "sticker" ? "✦" : "▢" }}
      </span>
      <span class="flex-1 truncate text-xs">
        {{ el.text || el.src?.split("/").pop() || el.type }}
      </span>
      <div class="flex gap-0.5 shrink-0">
        <button @click.stop="store.moveUp(el.id)" title="上移"
          class="w-6 h-6 flex items-center justify-center rounded hover:bg-hover text-muted hover:text-ink text-sm transition-colors">↑</button>
        <button @click.stop="store.moveDown(el.id)" title="下移"
          class="w-6 h-6 flex items-center justify-center rounded hover:bg-hover text-muted hover:text-ink text-sm transition-colors">↓</button>
        <button @click.stop="store.toggleVisibility(el.id)"
          :title="el.visible === false ? '显示' : '隐藏'"
          :class="['w-6 h-6 flex items-center justify-center rounded hover:bg-hover text-sm transition-colors', el.visible === false ? 'text-red-400' : 'text-muted hover:text-ink']">
          {{ el.visible === false ? "—" : "👁" }}
        </button>
        <button @click.stop="store.removeElement(el.id)" title="删除"
          class="w-6 h-6 flex items-center justify-center rounded hover:bg-red-50 text-muted hover:text-red-500 text-sm transition-colors">×</button>
      </div>
    </div>

    <p v-if="store.elements.length === 0" class="text-xs text-muted py-6 text-center">
      暂无元素，用文字/贴纸工具添加
    </p>
  </div>
</template>
