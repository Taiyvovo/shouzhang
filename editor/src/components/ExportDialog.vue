<script setup>
import { ref } from "vue";
import { useEditor } from "../stores/editor.js";

const emit = defineEmits(["close"]);
const store = useEditor();

const format = ref("png");
const exportWidth = ref(1080);
const scale = ref(1);
const exporting = ref(false);

async function doExport() {
  exporting.value = true;
  try {
    const payload = store.toRenderPayload();
    const r = await fetch(
      `/api/render?format=${format.value}&width=${exportWidth.value}&scale=${scale.value}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    if (!r.ok) throw new Error("Export failed");
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shouzhang.${format.value}`;
    a.click();
    URL.revokeObjectURL(url);
    emit("close");
  } catch (e) {
    alert("导出失败：" + e.message);
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <div
    class="fixed inset-0 bg-black/20 flex items-center justify-center z-50"
    @click.self="emit('close')"
  >
    <div class="bg-white rounded-xl shadow-2xl p-6 w-80 space-y-4">
      <h3 class="text-lg font-semibold text-ink">导出</h3>

      <!-- Format -->
      <div>
        <label class="text-xs text-muted block mb-2">格式</label>
        <div class="flex gap-2">
          <button
            @click="format = 'png'"
            :class="[
              'flex-1 py-2 rounded text-sm font-medium transition-colors',
              format === 'png'
                ? 'bg-ink text-white'
                : 'border border-border text-muted hover:bg-hover',
            ]"
          >
            PNG
          </button>
          <button
            @click="format = 'svg'"
            :class="[
              'flex-1 py-2 rounded text-sm font-medium transition-colors',
              format === 'svg'
                ? 'bg-ink text-white'
                : 'border border-border text-muted hover:bg-hover',
            ]"
          >
            SVG
          </button>
        </div>
      </div>

      <!-- Width -->
      <div>
        <label class="text-xs text-muted block mb-1"
          >宽度：{{ exportWidth }}px</label
        >
        <input
          type="range"
          v-model.number="exportWidth"
          min="540"
          max="2160"
          step="54"
          class="w-full"
        />
        <div class="flex justify-between text-[10px] text-muted">
          <span>540</span>
          <span>1080</span>
          <span>2160 (2x)</span>
        </div>
      </div>

      <!-- PNG extra options -->
      <div v-if="format === 'png'">
        <label class="text-xs text-muted block mb-1">超采样</label>
        <select
          v-model.number="scale"
          class="w-full px-2 py-1.5 border border-border rounded text-sm bg-white/70"
        >
          <option :value="1">1x 标准</option>
          <option :value="2">2x 高清</option>
          <option :value="3">3x 超高清</option>
        </select>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 pt-2">
        <button
          @click="emit('close')"
          class="flex-1 py-2 rounded text-sm border border-border text-muted hover:bg-hover transition-colors"
        >
          取消
        </button>
        <button
          @click="doExport"
          :disabled="exporting"
          class="flex-1 py-2 rounded text-sm bg-accent text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {{ exporting ? "导出中..." : `导出 ${format.toUpperCase()}` }}
        </button>
      </div>
    </div>
  </div>
</template>
