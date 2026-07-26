<script setup>
import { ref } from "vue";
import { useEditor } from "../stores/editor.js";

const store = useEditor();
const uploadInput = ref(null);

function addImage(src, originalSrc, name, naturalWidth = 600, naturalHeight = 400) {
  const maxSize = 600;
  const ratio = Math.min(1, maxSize / naturalWidth, maxSize / naturalHeight);
  const w = Math.max(40, Math.round(naturalWidth * ratio));
  const h = Math.max(40, Math.round(naturalHeight * ratio));
  store.addElement({
    type: "image",
    name,
    x: Math.round((store.canvas.width - w) / 2),
    y: Math.round((store.canvas.height - h) / 2),
    w,
    h,
    rotation: 0,
    src,
    _src: originalSrc || undefined,
    style: { font: {}, opacity: 1 },
  });
}

function imageSize(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
    image.onerror = () => reject(new Error("无法读取图片尺寸"));
    image.src = src;
  });
}

async function uploadImage(e) {
  const file = e.target.files?.[0];
  e.target.value = "";
  if (!file) return;
  try {
    if (!['image/png', 'image/jpeg'].includes(file.type)) throw new Error("只支持 PNG 和 JPEG 图片");
    if (file.size > 8 * 1024 * 1024) throw new Error("图片不能超过 8MB");
    const dataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("图片读取失败"));
      reader.readAsDataURL(file);
    });
    const size = await imageSize(dataUrl);
    addImage(dataUrl, null, file.name, size.width, size.height);
  } catch (error) {
    alert(`上传失败：${error.message}`);
  }
}

async function addLibraryImage(image) {
  try {
    const size = await imageSize(image.thumb);
    addImage(image.thumb, image.src, image.name, size.width, size.height);
  } catch (error) {
    alert(`添加失败：${error.message}`);
  }
}
</script>

<template>
  <div class="p-4 space-y-4">
    <div>
      <h3 class="text-sm font-medium text-ink/60 tracking-wide uppercase">图片</h3>
      <p class="text-xs text-muted mt-1">上传的图片会完整保存在工程文件中。</p>
    </div>

    <input ref="uploadInput" type="file" accept="image/png,image/jpeg" class="hidden" @change="uploadImage" />
    <button
      class="w-full py-2 rounded border border-accent text-sm text-ink hover:bg-hover transition-colors"
      @click="uploadInput?.click()"
    >
      上传 PNG / JPEG
    </button>

    <template v-if="store.imageCategories.length">
      <div class="flex gap-1 flex-wrap">
        <button
          v-for="category in store.imageCategories"
          :key="category"
          class="px-2 py-1 text-xs rounded transition-colors"
          :class="store.activeImageCategory === category ? 'bg-ink text-white' : 'text-muted hover:bg-hover'"
          @click="store.activeImageCategory = category"
        >{{ category }}</button>
      </div>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="image in store.imageData[store.activeImageCategory] || []"
          :key="image.src"
          class="aspect-square rounded border border-border bg-white p-1 hover:border-accent transition-colors"
          :title="image.name"
          @click="addLibraryImage(image)"
        >
          <img :src="image.thumb" :alt="image.name" class="w-full h-full object-contain" />
        </button>
      </div>
    </template>
    <p v-else class="text-xs text-muted leading-relaxed">
      素材库为空。可将图片放入 <code>assets/images</code>，刷新后会显示在这里。
    </p>
  </div>
</template>
