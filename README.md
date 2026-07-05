# 手账编辑器 (Shouzhang)

网页版手账/日记排版工具。拖拖拽拽就能做一页好看的手账，导出高清 PNG 或 SVG。目前还是偏日记的工具。

## 截图

![shouzhang](https://github.com/Taiyvovo/shouzhang/blob/main/img1.png?raw=true)
![shouzhang](https://github.com/Taiyvovo/shouzhang/blob/main/img2.png?raw=true)

## 特性

- **可视化编辑** — 拖拽排版 + 实时预览，所见即所得
- **自动换行** — 中英文混排、CJK 感知、单词不断开
- **富文本** — `**粗体**` `*斜体*` `__下划线__` `~~傍点~~` `[c=色]` `[s=号]`
- **自定义字体** — 38 种字体（Noto、Fusion Pixel），丢 TTF 进目录即用
- **贴纸装饰** — 23 种内建贴纸，拖入即用，支持缩放旋转
- **画布预设** — A5/A4/方形，丢 JSON 进目录即扩展
- **背景纹理** — 横线、网格、点阵、牛皮纸、薄荷色
- **双格式导出** — PNG（1x/2x/3x 超采样）+ SVG 矢量
- **撤销重做** — 50 步历史，Ctrl+Z/Y
- **图层管理** — 排序、显隐、删除

## 快速开始

```bash
# 安装依赖
pip install fastapi uvicorn
cd editor && npm install && cd ..

# 下载开源字体（可选，不下载也能用系统字体）
python scripts/download_fonts.py

# 一键启动（后端 + 前端）
python run.py
```

浏览器自动打开 `http://localhost:5173`。Ctrl+C 停止。

## 命令行渲染

不用界面也可以批量渲染模板：

```bash
python examples/demo.py
# 输出到 examples/out/*.png + *.svg
```

## 扩展

| 资源 | 方法 |
|---|---|
| 新贴纸 | 放 SV 到 `assets/stickers/<分类>/` |
| 新字体 | 放 TTF/OTF 到 `src/font/` |
| 新画布 | 放 JSON 到 `assets/presets/` |
| 新模板 | 放 JSON 到 `src/shouzhang/templates/builtin/` |

全部自动扫描，不需要改代码。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Tailwind CSS + Pinia |
| 后端 | FastAPI + Python |
| 渲染 | SVG 管线 → resvg / Edge headless |
| 排版 | 自研引擎（字符宽度估算 + 贪心换行 + 富文本解析） |

## 架构

```
Template JSON → Document → RenderIR → SVG → PNG
    ↕
 Pinia Store → Vue SVG Canvas (实时预览)
```

前端预览和后端导出共用同一套排版算法（`engine/text.js` ≈ `engine/text_layout.py`），保证一致性。

## 文档

- [模板格式](docs/templates.md)
- [字体系统](docs/fonts.md)
- [富文本语法](docs/richtext.md)
- [渲染架构](docs/rendering.md)
- [API 参考](docs/api.md)
- [素材清单](docs/assets.md)

## 许可

MIT
