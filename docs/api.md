# Python API 参考

## 模板系统

### TemplateRegistry

```python
from shouzhang.templates import TemplateRegistry

reg = TemplateRegistry()

# 加载模板
count = reg.load_dir("templates/builtin")          # 扫描目录全部 JSON
reg.register(template_object)                      # 注册单个模板

# 查询
tpl = reg.get("diary-classic")                     # 获取模板
all_templates = reg.list()                         # 全部
diary_only = reg.list(category="diary")            # 按分类
categories = reg.categories()                      # 分类列表

# 实例化
doc = reg.instantiate("diary-classic")             # 默认内容
doc = reg.instantiate("diary-classic", content={   # 替换内容
    "date": "2026-07-05",
    "body": "自定义文字..."
})
```

---

## 字体系统

### FontRegistry

```python
from shouzhang.engine.fonts import FontRegistry

reg = FontRegistry()
count = reg.scan("src/font")              # 扫描字体目录，返回文件数

# 查询
entry = reg.find("Noto Sans SC")          # 查找字族（匹配 closest weight）
entry = reg.find("Noto Sans SC", weight=700)  # 指定字重
entry.path                               # Path 对象 → 字体文件绝对路径
entry.family                             # str → 字族名
entry.weight                             # int → 字重 (100-900)
entry.italic                             # bool → 是否斜体

families = reg.list_families()            # 所有字族名列表
entries = reg.get_entries("Noto Sans SC") # 某字族所有变体
```

---

## 渲染管线

### DocumentCompiler

```python
from shouzhang.render import DocumentCompiler

compiler = DocumentCompiler(assets_root="assets/")
ir = compiler.compile(document)            # Document → RenderIR
```

### SVGCompiler

```python
from shouzhang.render import SVGCompiler

svgc = SVGCompiler(font_registry=font_reg) # font_registry 可选
svg = svgc.render(ir)                      # RenderIR → SVG 字符串

# 写入文件
Path("output.svg").write_text(svg, encoding="utf-8")

# 获取使用的字体列表
svgc.used_fonts  # set[str] — 非通用字体名
```

### Rasterizer

```python
from shouzhang.render import Rasterizer

raster = Rasterizer()

# 检查状态
raster.available()         # bool — 有可用后端？
raster.backend             # str — 当前后端名 ("resvg" / "cairosvg")
raster.has_browser()       # bool — 能找到 Edge/Chrome？

# 渲染到内存
png_bytes = raster.to_png(
    svg_string,
    output_width=1080,     # 输出宽度 (px)
    output_height=None,    # 输出高度 (自动按比例)
    scale=1.0,             # 缩放系数 (2.0 = 2x 高清)
    resources_dir=None,    # resvg 资源目录
    use_browser=False,     # 强制使用 Edge headless
)

# 渲染到文件
path = raster.to_file(
    svg_string,
    "output.png",
    output_width=1080,
    scale=1.0,
    use_browser=False,
)
```

---

## 完整示例（从零到 PNG）

```python
from pathlib import Path
from shouzhang.templates import TemplateRegistry
from shouzhang.engine.fonts import FontRegistry
from shouzhang.render import DocumentCompiler, SVGCompiler, Rasterizer

ROOT = Path(__file__).resolve().parent

# 1. 加载模板与字体
reg = TemplateRegistry()
reg.load_dir(ROOT / "templates" / "builtin")

font_reg = FontRegistry()
font_reg.scan(ROOT / "fonts")

# 2. 渲染管线
compiler = DocumentCompiler(assets_root=ROOT / "assets")
svg_compiler = SVGCompiler(font_registry=font_reg)
rasterizer = Rasterizer()

# 3. 逐个模板渲染
for tpl in reg.list():
    doc = reg.instantiate(tpl.id)
    ir = compiler.compile(doc)
    svg = svg_compiler.render(ir)

    # 写入 SVG
    (ROOT / f"{tpl.id}.svg").write_text(svg)

    # 写入 PNG（自定义字体用浏览器，否则 resvg）
    use_browser = bool(svg_compiler.used_fonts) and rasterizer.has_browser()
    rasterizer.to_file(svg, ROOT / f"{tpl.id}.png",
                       output_width=1080, use_browser=use_browser)
```

---

## 数据模型

```python
from shouzhang.models import (
    Document, Canvas, Layer,
    TextElement, ImageElement, StickerElement,
    TapeElement, ShapeElement, BackgroundElement,
    Style, FontStyle,
)

# 手动构建 Document（不用模板）
doc = Document(
    id="manual",
    name="手建文档",
    canvas=Canvas(width=1080, height=1527, background="#fff", pattern="lines"),
    layers=[
        Layer(id="l1", name="图层1", elements=[
            TextElement(
                id="title", x=100, y=100, w=880, h=80,
                text="标题文字",
                style=Style(font=FontStyle(family="serif", size=48, weight=700))
            ),
        ])
    ]
)
```

---

## 富文本工具

```python
from shouzhang.engine import (
    parse_rich_text,    # text → list[TextSpan]
    wrap_spans,         # list[TextSpan] → list[list[TextSpan]] (按行分组)
    wrap_text,          # str → str (自动换行，保留 \n 断行)
    has_markup,         # str → bool (是否含富文本标记)
    rich_plain_text,    # list[TextSpan] → str (拼回纯文本)
)

# 示例
spans = parse_rich_text("今天**天气**很好")
# → [TextSpan(text="今天"), TextSpan(text="天气", bold=True), TextSpan(text="很好")]

lines = wrap_spans(spans, size=36, box_width=500, letter_spacing=0)
# → [[TextSpan("今天"), TextSpan("天气", bold=True), TextSpan("很好")]]
```
