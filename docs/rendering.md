# 渲染管线架构

完整的数据流从 JSON 模板到最终 PNG 输出。

## 概览

```
Template JSON
    ↓ [TemplateRegistry.load_dir / instantiate]
  Document (数据模型)
    ↓ [DocumentCompiler.compile]
  RenderIR (中间表示)
    ↓ [SVGCompiler.render]
  SVG 字符串 (矢量输出)
    ↓ [Rasterizer.to_png]
  PNG 字节 (光栅化输出)
```

---

## 第 0 层：数据模型 (`models/`)

### Document
```python
class Document:
    id: str              # 文档 ID
    name: str            # 文档名
    canvas: Canvas       # 画布设定
    layers: list[Layer]  # 图层列表
```

### Canvas
```python
class Canvas:
    width: float = 1080.0     # 画布宽度
    height: float = 1527.0    # 画布高度
    background: str           # 背景色
    pattern: Literal["none","lines","grid","dots"]
    pattern_color: str        # 图案颜色
    pattern_spacing: float    # 图案间距
```

### Layer
```python
class Layer:
    id: str
    name: str
    elements: list[ElementUnion]  # 元素列表（按 z_index 排序）
    visible: bool
    locked: bool
```

### ElementUnion
组合类型，根据 `type` 字段区分：
- `TextElement` (`type="text"`) — 文字
- `ImageElement` (`type="image"`) — 图片
- `StickerElement` (`type="sticker"`) — 贴纸
- `TapeElement` (`type="tape"`) — 胶带
- `ShapeElement` (`type="shape"`) — 形状（矩形/椭圆/线条/自定义路径）
- `BackgroundElement` (`type="background"`) — 背景图

---

## 第 1 层：模板 → Document (`templates/`)

### TemplateRegistry

```python
reg = TemplateRegistry()
reg.load_dir("templates/builtin")       # 扫描 JSON 文件
reg.get("diary-classic")                # 获取 Template 对象
doc = reg.instantiate("diary-classic")  # 生成 Document

# 带内容替换
doc = reg.instantiate("diary-classic", content={
    "date": "2026年7月5日",
    "body": "今天写的内容..."
})
```

内部流程：
1. 读 JSON → `Template` pydantic 模型
2. `instantiate()` 创建 1 个 `Layer`，把 `decorations`（装饰）和 `slots`（槽位）转为 `ElementUnion` 列表
3. 槽位按 `type` 分发：`text`→`TextElement`，`image`→`ImageElement`，`sticker`→`StickerElement`

---

## 第 2 层：Document → RenderIR (`render/doc_compiler.py`)

### DocumentCompiler

```python
compiler = DocumentCompiler(assets_root="assets/")
ir = compiler.compile(doc)  # -> RenderIR
```

处理流程：

1. **画布编译**：背景矩形 + 图案（横线/网格/点阵 → `DrawPath` 或 `DrawRect`）
2. **元素编译**（按 `z_index` 排序）：
   - `TextElement` → 自动换行（`wrap_text`）或富文本解析（`parse_rich_text` + `wrap_spans`） → `DrawText`
   - `ImageElement` → 路径解析 → `DrawImage`
   - `StickerElement` → 路径解析 → `DrawSVG`
   - `TapeElement` → 路径解析 → `DrawSVG`
   - `ShapeElement` → 形状分发 → `DrawRect` / `DrawPath`
   - `BackgroundElement` → SVG 路径 → `DrawSVG`
3. 每个元素用 `DrawGroup` 包裹（含 `Transform`：位移、旋转、缩放）+ 阴影 + 透明度

### RenderIR
```python
class RenderIR:
    width: float                     # 画布宽度
    height: float                    # 画布高度
    background: str                  # 背景色
    commands: list[DrawCommandUnion] # 渲染指令列表
```

### DrawCommandUnion（命令联合类型）

| 命令 | 用途 |
|---|---|
| `DrawRect(x,y,w,h,rx,ry,fill,stroke,...)` | 矩形/圆角矩形 |
| `DrawText(x,y,w,h,text,family,size,weight,color,spans,...)` | 文字（含富文本 spans） |
| `DrawImage(x,y,w,h,src,fit)` | 图片（base64 内嵌或路径） |
| `DrawPath(d,x,y,fill,stroke)` | 自定义路径（SVG d 值） |
| `DrawSVG(x,y,w,h,src)` | 嵌入外部 SVG（贴纸、背景） |
| `DrawGroup(transform,opacity,shadow,children)` | 分组（坐标变换容器） |

---

## 第 3 层：RenderIR → SVG (`render/svg_compiler.py`)

### SVGCompiler

```python
svg_compiler = SVGCompiler(font_registry=font_reg)
svg = svg_compiler.render(ir)  # -> SVG 字符串
```

渲染过程：

1. **`<defs>` 生成**：
   - 阴影滤镜（`<filter id="sh0">` 含 feGaussianBlur + feOffset + feMerge）
   - `@font-face` 声明（`<style>` 含自定义字体 file:// URI）
   - 贴纸 `<symbol>` 缓存
2. **背景矩形**：`<rect width="..." height="..." fill="...">`
3. **遍历 IR 命令**：
   - `DrawGroup` → `<g transform="...">`
   - `DrawRect` → `<rect>`
   - `DrawText` → `<text>` + `<tspan>` 序列
   - `DrawImage` → `<image href="data:image/png;base64,...">`
   - `DrawPath` → `<path d="...">`
   - `DrawSVG` → 读取 SVG 文件，提取 inner 内容，缩放嵌入
4. **字体名前引号处理**：含空格的字体名自动包单引号 `'Noto Sans SC'`

---

## 第 4 层：SVG → PNG (`render/rasterizer.py`)

### Rasterizer

```python
raster = Rasterizer()
png_bytes = raster.to_png(svg, output_width=1080)
raster.to_file(svg, "output.png", output_width=1080)
```

**三后端自动选择**：

| 后端 | 条件 | 速度 | 字体支持 |
|---|---|---|---|
| resvg-py | 无自定义字体 | 极快 (~0.1s) | 仅系统字体 |
| Edge headless | 有自定义字体 + 浏览器可用 | 慢 (~1.5s) | 100% CSS 字体 |
| cairosvg | 其他后端不可用时 | 中 | 有限 |

**Edge headless 实现**：
1. 将 SVG 包裹在 HTML 中（`<style>` 已在 SVG 的 `<defs>` 里含 `@font-face`）
2. 调用 `msedge --headless=new --disable-gpu --screenshot=out.png --window-size=W,H --force-device-scale-factor=N`
3. 从临时 PNG 读取字节
4. 清理临时文件

**清晰度控制**：`--force-device-scale-factor=N` 控制输出分辨率。设为 2 即 2x 高清。

---

## 辅助模块

### engine/text_layout.py（自动换行）

```
文本 → char_width() 估算字符宽度 → 贪心填行 → 超宽单词按字符拆分 → 换行后文本
```

- CJK 字符宽度 = font_size
- 大写字母 = 0.68×font_size
- 小写字母 = 0.55×font_size
- 数字 = 0.6×font_size
- 空格 = 0.28×font_size

### engine/rich_text.py（富文本解析）

- `parse_rich_text()`：字符级状态机，递归处理嵌套标记
- `wrap_spans()`：将带样式的 span 序列按宽度换行
- `_split_spans_by_lines()`：将平铺 spans 切成每行一组（供 SVG 渲染 `_render_rich_text` 使用）

### engine/fonts.py（字体发现）

- `FontRegistry.scan()`：递归遍历目录，解析 TTF/OTF 文件名 → 字族 + 字重 + 斜体
- `FontRegistry.find(family, weight, italic)`：模糊匹配，按字重差 + 斜体惩罚打分
- 字符名解析：`Font-WeightStyle.ttf` → `family="Font", weight=700, italic=True`

---

## 坐标系统

- SVG 坐标原点为左上角 (0,0)，X 右 Y 下
- 元素位置由父级 `DrawGroup` 的 `Transform` 控制
- 文字元素内部：`x=0, y=0` 相对坐标，`align` / `valign` 在 IR 内部计算 tspan 偏移
- 贴纸缩放：`sx = el.w / sticker.viewBox.width`，`sy = el.h / sticker.viewBox.height`

---

## 关键文件索引

| 文件 | 内容 |
|---|---|
| `models/style.py` | `FontStyle`, `Style`, `TextSpan` |
| `models/element.py` | `TextElement`, `StickerElement`, `ElementUnion` 等 7 种元素 |
| `models/document.py` | `Canvas`, `Layer`, `Document` |
| `engine/fonts.py` | `FontRegistry`, `FontEntry` — 字体扫描与匹配 |
| `engine/text_layout.py` | `wrap_text()` / `char_width()` — 自动换行 |
| `engine/rich_text.py` | `parse_rich_text()` / `wrap_spans()` — 富文本 |
| `render/protocol.py` | `RenderIR`, `DrawText`, `DrawGroup` 等 IR 定义 |
| `render/doc_compiler.py` | `DocumentCompiler` — Doc → IR |
| `render/svg_compiler.py` | `SVGCompiler` — IR → SVG |
| `render/rasterizer.py` | `Rasterizer` — SVG → PNG |
| `templates/registry.py` | `TemplateRegistry` — 模板加载 |
