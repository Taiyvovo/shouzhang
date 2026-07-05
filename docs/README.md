# 手账排版引擎（shouzhang）

将 JSON 模板渲染为可打印的手账/日记页面。支持自定义字体、富文本标记、贴纸装饰、背景纹理。输出高分辨率 PNG + SVG 矢量文件。

## 安装

```bash
pip install -e .
```

## 启动网页编辑器

```bash
python run.py
```

自动启动后端 API + 前端 Vite 开发服务器，浏览器自动打开 `http://localhost:5173`。Ctrl+C 全部停止。

## 命令行渲染

```bash
python examples/demo.py
```

输出见 `examples/out/`，每个模板生成 `.svg` + `.png` 两个文件。

## 自定义模板

在 `src/shouzhang/templates/builtin/` 下新建 `.json` 文件，下次运行 demo 自动加载。格式参考 → [docs/templates.md](docs/templates.md)

## 文档索引

| 文档 | 内容 |
|---|---|
| [templates.md](docs/templates.md) | 模板 JSON 完整格式、画布、图层、元素 |
| [fonts.md](docs/fonts.md) | 字体系统、如何选择/使用自定义字体 |
| [richtext.md](docs/richtext.md) | 富文本标记语法（粗体/斜体/下划线/颜色/字号） |
| [rendering.md](docs/rendering.md) | 渲染管线架构与实现原理 |
| [api.md](docs/api.md) | Python API 参考 |

## 功能一览

- 1080×1527 (A5 竖版) / 1527×1080 (横版) 两种画布
- 自动换行（中英文混排、CJK 感知、单词断词）
- 富文本：`**粗体**` `*斜体*` `__下划线__` `~~傍点~~` `[c=#色]` `[s=号]`
- 98+ 字体支持（EN / ZH-SC / ZH-TC / JA / KO）
- 23 种内建贴纸 × 4 大类（emotion / item / plant / weather）
- 2 种背景纹理（牛皮纸 / 薄荷网格）
- SVG 矢量输出 + PNG 光栅化（resvg / Edge headless）
- 像素字体原生渲染（15 种 Fusion Pixel 变体）
