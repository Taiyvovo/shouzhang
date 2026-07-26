<script setup>
import { ref } from "vue";
import { useEditor } from "../stores/editor.js";
import ExportDialog from "./ExportDialog.vue";

const store = useEditor();
const showExport = ref(false);
const projectInput = ref(null);

const tools = [
  { id: "background", label: "画布", icon: "▦" },
  { id: "text", label: "文字", icon: "T" },
  { id: "sticker", label: "贴纸", icon: "✦" },
  { id: "image", label: "图片", icon: "▧" },
  { id: "layer", label: "图层", icon: "☷" },
];

function saveProject() {
  const blob = new Blob([JSON.stringify(store.projectData(), null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${store.projectName || "未命名手账"}.shouzhang`;
  link.click();
  URL.revokeObjectURL(url);
  store.markSaved();
}

function chooseProject() {
  if (store.isDirty && !window.confirm("当前工程尚未保存，确定要导入其他工程吗？")) return;
  projectInput.value?.click();
}

async function importProject(e) {
  const file = e.target.files?.[0];
  e.target.value = "";
  if (!file) return;
  try {
    if (file.size > 100 * 1024 * 1024) throw new Error("工程文件不能超过 100MB");
    const data = JSON.parse(await file.text());
    store.loadProject(data, file.name.replace(/\.shouzhang$/i, ""));
  } catch (error) {
    alert(`导入失败：${error.message}`);
  }
}
</script>

<template>
  <header
    class="h-16 flex items-center px-5 border-b border-border/80 bg-paper/90 backdrop-blur shrink-0 gap-4 select-none shadow-sm z-10"
  >
    <input ref="projectInput" type="file" accept=".shouzhang,application/json" class="hidden" @change="importProject" />

    <div class="flex items-center gap-3 min-w-0">
      <div class="w-9 h-9 rounded-xl bg-accent text-white flex items-center justify-center font-serif text-lg shadow-sm">手</div>
      <div class="min-w-0">
        <div class="flex items-center gap-1.5">
          <input
            v-model.trim="store.projectName"
            maxlength="100"
            class="w-36 bg-transparent text-sm font-semibold text-ink outline-none border-b border-transparent focus:border-accent/50 transition-colors"
            aria-label="工程名称"
          />
          <span v-if="store.isDirty" class="w-1.5 h-1.5 rounded-full bg-accent" title="有未保存更改" />
        </div>
        <div class="flex gap-3 mt-0.5">
          <button @click="saveProject" class="text-[11px] text-muted hover:text-ink transition-colors">保存工程</button>
          <button @click="chooseProject" class="text-[11px] text-muted hover:text-ink transition-colors">打开工程</button>
        </div>
      </div>
    </div>

    <nav class="flex items-center gap-1 p-1 bg-panel/80 border border-border/70 rounded-xl shadow-inner mx-auto">
      <button
        v-for="t in tools"
        :key="t.id"
        @click="store.activeTool = t.id"
        :class="[
          'tool-button px-3 py-1.5 rounded-lg text-xs transition-all duration-200',
          store.activeTool === t.id
            ? 'bg-white text-ink shadow-sm'
            : 'text-muted hover:bg-white/60 hover:text-ink',
        ]"
      >
        <span class="mr-1.5 text-sm">{{ t.icon }}</span>{{ t.label }}
      </button>
    </nav>

    <div class="flex items-center justify-end gap-1 min-w-52">
      <button @click="store.undo()" class="icon-button" title="撤销" aria-label="撤销">↩</button>
      <button @click="store.redo()" class="icon-button mr-2" title="重做" aria-label="重做">↪</button>
      <button
        @click="showExport = true"
        class="px-5 py-2 rounded-xl bg-ink text-paper text-xs font-medium hover:-translate-y-0.5 hover:shadow-md transition-all duration-200"
      >导出作品</button>
    </div>
  </header>

  <Transition name="modal">
    <ExportDialog v-if="showExport" @close="showExport = false" />
  </Transition>
</template>
