"""手账编辑器后端 — FastAPI 服务"""
from pathlib import Path
import base64
import json as _json

from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from shouzhang.templates import TemplateRegistry
from shouzhang.engine.fonts import FontRegistry
from shouzhang.render import DocumentCompiler, SVGCompiler, Rasterizer


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONTS = ROOT / "src" / "font"
TEMPLATES = ROOT / "src" / "shouzhang" / "templates" / "builtin"

font_reg = FontRegistry()
font_reg.scan(FONTS)

compiler = DocumentCompiler(assets_root=ASSETS)
raster = Rasterizer()

app = FastAPI(title="手账编辑器")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── 数据模型 ──

class FontStyle(BaseModel):
    family: str = "sans-serif"
    size: float = 36
    weight: int = 400
    color: str = "#333333"
    line_height: float = 1.6
    letter_spacing: float = 0

class Style(BaseModel):
    font: FontStyle = Field(default_factory=FontStyle)
    opacity: float = 1.0

class CanvasModel(BaseModel):
    width: float = 1080
    height: float = 1527
    background: str = "#fbfaf6"
    pattern: str = "none"

class Element(BaseModel):
    id: str
    type: str
    x: float = 0
    y: float = 0
    w: float = 200
    h: float = 80
    rotation: float = 0
    z_index: int = 0
    align: str = "left"
    valign: str = "top"
    style: Style = Field(default_factory=Style)
    text: str = ""
    src: str = ""
    file: str = ""
    default: str = ""

class RenderRequest(BaseModel):
    canvas: CanvasModel = Field(default_factory=CanvasModel)
    elements: list[Element] = Field(default_factory=list)

# ── API ──

@app.get("/api/font-css")
def api_font_css():
    """生成 @font-face CSS，字体通过 /api/font-file 代理"""
    lines = []
    seen = set()
    for family in sorted(font_reg.list_families()):
        entries = font_reg.get_entries(family)
        for entry in entries:
            key = (entry.family, entry.weight, entry.italic)
            if key in seen:
                continue
            seen.add(key)
            fstyle = "italic" if entry.italic else "normal"
            fn = entry.path.name
            lines.append(
                f'@font-face {{ font-family: "{entry.family}"; '
                f'src: url("/api/font-file?family={entry.family}&weight={entry.weight}&italic={str(entry.italic).lower()}"); '
                f'font-weight: {entry.weight}; '
                f'font-style: {fstyle}; }}'
            )
    css = "\n".join(lines)
    return Response(css, media_type="text/css")


@app.get("/api/font-file/{family:path}")
def api_font_file_path(family: str):
    """通过字族名直接获取字体文件，URL 编码支持含空格/中文的字体名"""
    entry = font_reg.find(family)
    if not entry:
        return Response("font not found: " + family, status_code=404)
    data = entry.path.read_bytes()
    return Response(data, media_type="font/ttf")


@app.get("/api/fonts")
def api_fonts():
    families = font_reg.list_families()
    return {"families": families}

@app.get("/api/stickers")
def api_stickers():
    cats = {}
    stickers_dir = ASSETS / "stickers"
    for cat_dir in sorted(stickers_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        items = []
        for svg_file in sorted(cat_dir.glob("*.svg")):
            name = svg_file.stem
            svg_bytes = svg_file.read_bytes()
            b64 = base64.b64encode(svg_bytes).decode()
            items.append({
                "name": name,
                "src": f"stickers/{cat_dir.name}/{svg_file.name}",
                "thumb": f"data:image/svg+xml;base64,{b64}",
            })
        cats[cat_dir.name] = items
    # Root stickers
    root_items = []
    for svg_file in sorted(stickers_dir.glob("*.svg")):
        name = svg_file.stem
        svg_bytes = svg_file.read_bytes()
        b64 = base64.b64encode(svg_bytes).decode()
        root_items.append({
            "name": name,
            "src": f"stickers/{svg_file.name}",
            "thumb": f"data:image/svg+xml;base64,{b64}",
        })
    if root_items:
        cats["basic"] = root_items
    return {"categories": cats}

@app.post("/api/render")
def api_render(
    req: RenderRequest = Body(...),
    format: str = Query("png"),
    width: int = Query(1080),
    scale: float = Query(1.0),
):
    from shouzhang.models.document import Canvas, Layer, Document
    from shouzhang.models.element import TextElement, StickerElement, ImageElement
    from shouzhang.models.style import FontStyle, Style

    canvas = Canvas(
        width=req.canvas.width,
        height=req.canvas.height,
        background=req.canvas.background,
        pattern=req.canvas.pattern,
        pattern_spacing=36,
    )

    elements = []
    for el in req.elements:
        style = Style(
            font=FontStyle(
                family=el.style.font.family,
                size=el.style.font.size,
                weight=el.style.font.weight,
                color=el.style.font.color,
                line_height=el.style.font.line_height,
                letter_spacing=el.style.font.letter_spacing,
            ),
            opacity=el.style.opacity,
        )
        if el.type == "text":
            elements.append(TextElement(
                id=el.id, x=el.x, y=el.y, w=el.w, h=el.h,
                rotation=el.rotation, z_index=el.z_index,
                align=el.align, valign=el.valign,
                text=el.text or el.default, style=style,
            ))
        elif el.type == "sticker":
            sticker_src = el.file or el.src  # prefer original file path
            elements.append(StickerElement(
                id=el.id, x=el.x, y=el.y, w=el.w, h=el.h,
                rotation=el.rotation, z_index=el.z_index,
                src=sticker_src, style=style,
            ))
        elif el.type == "image":
            elements.append(ImageElement(
                id=el.id, x=el.x, y=el.y, w=el.w, h=el.h,
                rotation=el.rotation, z_index=el.z_index,
                src=el.src, style=style,
            ))

    layer = Layer(id="main", name="图层1", elements=elements)
    doc = Document(id="render", name="预览", canvas=canvas, layers=[layer])

    svg_compiler = SVGCompiler(font_registry=font_reg)
    ir = compiler.compile(doc)
    svg = svg_compiler.render(ir)

    if format == "svg":
        return Response(svg, media_type="image/svg+xml",
                        headers={"Content-Disposition": "attachment; filename=render.svg"})

    use_browser = bool(svg_compiler.used_fonts) and raster.has_browser()
    png_bytes = raster.to_png(svg, output_width=width, scale=scale, use_browser=use_browser)
    return Response(png_bytes, media_type="image/png",
                    headers={"Content-Disposition": "attachment; filename=render.png"})


@app.get("/api/presets")
def api_presets():
    presets_dir = ROOT / "assets" / "presets"
    canvases = []
    if presets_dir.is_dir():
        for f in sorted(presets_dir.glob("*.json")):
            data = _json.loads(f.read_text(encoding="utf-8"))
            canvases.append({
                "id": f.stem,
                "name": data.get("name", f.stem),
                "width": data["width"],
                "height": data["height"],
                "background": data.get("background", "#fbfaf6"),
                "pattern": data.get("pattern", "none"),
            })
    return {
        "canvases": canvases,
        "backgrounds": [
            {"id": "#fbfaf6", "name": "暖白", "hex": "#fbfaf6"},
            {"id": "#ffffff", "name": "纯白", "hex": "#ffffff"},
            {"id": "#f5f0e8", "name": "牛皮纸", "hex": "#f5f0e8"},
            {"id": "#f2f7f2", "name": "薄荷", "hex": "#f2f7f2"},
            {"id": "#1a1a2e", "name": "深夜", "hex": "#1a1a2e"},
            {"id": "#0a0e14", "name": "纯黑", "hex": "#0a0e14"},
        ],
        "patterns": [
            {"id": "none", "name": "无"},
            {"id": "lines", "name": "横线"},
            {"id": "grid", "name": "网格"},
            {"id": "dots", "name": "点阵"},
        ],
    }


# 开发时 Vite 前端通过 proxy 或直接访问，生产时无需以下
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
