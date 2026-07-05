<script setup>
import { watch } from "vue";
import { useEditor } from "../stores/editor.js";

const store = useEditor();

// Ensure selected element auto-expands height when text grows
watch(
  () => store.selected?.text,
  (text) => {
    if (!store.selected || store.selected.type !== "text") return;
    const lines = (text || "").split("\n");
    const size = store.selected.style?.font?.size || 36;
    const lh = store.selected.style?.font?.line_height || 1.6;
    const needed = Math.max(60, lines.length * size * lh + size * 0.8 + 20);
    if (needed > (store.selected.h || 60)) {
      store.updateElement(store.selected.id, { h: needed });
    }
  }
);

function updateFont(patch) {
  if (!store.selected) return;
  store.updateElement(store.selected.id, {
    style: {
      ...store.selected.style,
      font: { ...(store.selected.style?.font || {}), ...patch },
    },
  });
}
</script>

<template>
  <div class="p-4 space-y-3">
    <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase">
      文字工具
    </h3>

    <p class="text-xs text-muted leading-relaxed">
      在画布上点击放置文字框，选中后在此编辑属性。双击画布上的文字可快速聚焦输入。
    </p>

    <!-- Font family -->
    <div>
      <label class="text-xs text-muted block mb-1">字体</label>
      <select
        :value="store.selected?.style?.font?.family || 'serif'"
        @change="updateFont({ family: $event.target.value })"
        class="w-full px-2 py-1.5 border border-border rounded text-sm bg-white/70"
      >
        <optgroup label="系统字体">
          <option value="serif">系统·衬线 (serif)</option>
          <option value="sans-serif">系统·无衬线 (sans-serif)</option>
          <option value="monospace">系统·等宽 (monospace)</option>
        </optgroup>
        <optgroup label="自定义字体">
          <option v-for="f in store.fontFamilies" :key="f" :value="f">
            {{ f }}
          </option>
        </optgroup>
      </select>
    </div>

    <!-- Font size -->
    <div>
      <label class="text-xs text-muted block mb-1">
        字号：{{ store.selected?.style?.font?.size || 36 }}px
      </label>
      <div class="flex gap-2 items-center">
        <input
          type="range"
          :value="store.selected?.style?.font?.size || 36"
          @input="updateFont({ size: Number($event.target.value) })"
          min="12"
          max="120"
          class="flex-1"
        />
        <input
          type="number"
          :value="store.selected?.style?.font?.size || 36"
          @change="updateFont({ size: Number($event.target.value) })"
          min="8"
          max="200"
          class="w-14 px-1 py-0.5 border border-border rounded text-xs text-center bg-white/70"
        />
      </div>
    </div>

    <!-- Weight -->
    <div>
      <label class="text-xs text-muted block mb-1">粗细</label>
      <div class="flex gap-1">
        <button
          v-for="w in [300, 400, 700, 900]"
          :key="w"
          @click="updateFont({ weight: w })"
          :class="[
            'flex-1 py-1 text-xs rounded transition-colors',
            (store.selected?.style?.font?.weight || 400) === w
              ? 'bg-ink text-white'
              : 'hover:bg-hover text-muted',
          ]"
        >
          {{ { 300: "细", 400: "常", 700: "粗", 900: "超粗" }[w] }}
        </button>
      </div>
    </div>

    <!-- Color -->
    <div>
      <label class="text-xs text-muted block mb-1">颜色</label>
      <div class="flex gap-2 items-center">
        <input
          type="color"
          :value="store.selected?.style?.font?.color || '#333333'"
          @input="updateFont({ color: $event.target.value })"
          class="w-8 h-8 rounded border border-border cursor-pointer"
        />
        <span class="text-xs text-muted">{{
          store.selected?.style?.font?.color || "#333"
        }}</span>
      </div>
    </div>

    <!-- Line height -->
    <div>
      <label class="text-xs text-muted block mb-1">行高</label>
      <select
        :value="store.selected?.style?.font?.line_height || 1.6"
        @change="updateFont({ line_height: Number($event.target.value) })"
        class="w-full px-2 py-1.5 border border-border rounded text-sm bg-white/70"
      >
        <option :value="1.2">1.2 紧凑</option>
        <option :value="1.6">1.6 标准</option>
        <option :value="2.0">2.0 松散</option>
        <option :value="2.5">2.5 超松</option>
      </select>
    </div>

    <!-- Alignment -->
    <div>
      <label class="text-xs text-muted block mb-1">水平对齐</label>
      <div class="flex gap-1">
        <button v-for="a in ['left','center','right']" :key="a"
          @click="store.selected && store.updateElement(store.selected.id, { align: a })"
          :class="['flex-1 py-1 text-xs rounded transition-colors', (store.selected?.align || 'left') === a ? 'bg-ink text-white' : 'hover:bg-hover text-muted']">
          {{ { left: '左', center: '中', right: '右' }[a] }}
        </button>
      </div>
    </div>
    <div>
      <label class="text-xs text-muted block mb-1">垂直对齐</label>
      <div class="flex gap-1">
        <button v-for="v in ['top','middle','bottom']" :key="v"
          @click="store.selected && store.updateElement(store.selected.id, { valign: v })"
          :class="['flex-1 py-1 text-xs rounded transition-colors', (store.selected?.valign || 'top') === v ? 'bg-ink text-white' : 'hover:bg-hover text-muted']">
          {{ { top: '上', middle: '中', bottom: '下' }[v] }}
        </button>
      </div>
    </div>

    <!-- Text content -->
    <div>
      <label class="text-xs text-muted block mb-1">
        内容 {{ store.selected?.type === 'text' ? '(Shift+Enter 换行)' : '' }}
      </label>
      <textarea
        v-if="store.selected?.type === 'text'"
        :value="store.selected.text"
        @input="
          store.updateElement(store.selected.id, {
            text: $event.target.value,
          })
        "
        rows="4"
        class="w-full px-2 py-1.5 border border-border rounded text-sm bg-white/70 resize-none"
        placeholder="输入文字，按回车换行..."
      />
      <p v-else class="text-xs text-muted py-2">
        选中一个文字元素进行编辑
      </p>
    </div>

    <!-- Delete -->
    <button
      v-if="store.selected"
      @click="store.removeElement(store.selected.id)"
      class="w-full py-1.5 text-xs text-red-500 hover:bg-red-50 rounded transition-colors"
    >
      删除此元素
    </button>
  </div>
</template>
