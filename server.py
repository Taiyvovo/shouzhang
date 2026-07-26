"""手账编辑器后端 — FastAPI 服务"""
from pathlib import Path
import base64
import json as _json
from urllib.parse import quote

from fastapi import FastAPI, Query, Body, HTTPException
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

compiler = DocumentCompiler(assets_root=ASSETS, restrict_assets=True)
raster = Rasterizer()

app = FastAPI(title="手账编辑器")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── 数据模型 ──

class FontStyle(BaseModel):
    family: str = Field("sans-serif", max_length=200)
    size: float = Field(36, gt=0, le=1000)
    weight: int = Field(400, ge=100, le=900)
    color: str = Field("#333333", max_length=100)
    line_height: float = Field(1.6, gt=0, le=10)
    letter_spacing: float = Field(0, ge=-100, le=1000)

class Style(BaseModel):
    font: FontStyle = Field(default_factory=FontStyle)
    opacity: float = Field(1.0, ge=0, le=1)

class CanvasModel(BaseModel):
    width: float = Field(1080, gt=0, le=10000)
    height: float = Field(1527, gt=0, le=10000)
    background: str = Field("#fbfaf6", max_length=100)
    pattern: str = Field("none", pattern="^(none|lines|grid|dots)$")

class Element(BaseModel):
    id: str = Field(max_length=200)
    type: str = Field(pattern="^(text|sticker|image)$")
    x: float = Field(0, ge=-20000, le=20000)
    y: float = Field(0, ge=-20000, le=20000)
    w: float = Field(200, gt=0, le=10000)
    h: float = Field(80, gt=0, le=10000)
    rotation: float = Field(0, ge=-36000, le=36000)
    z_index: int = 0
    visible: bool = True
    align: str = Field("left", pattern="^(left|center|right)$")
    valign: str = Field("top", pattern="^(top|middle|bottom)$")
    style: Style = Field(default_factory=Style)
    text: str = Field("", max_length=100000)
    src: str = Field("", max_length=15_000_000)
    file: str = Field("", max_length=1000)
    default: str = Field("", max_length=100000)

class RenderRequest(BaseModel):
    canvas: CanvasModel = Field(default_factory=CanvasModel)
    elements: list[Element] = Field(default_factory=list, max_length=500)

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
            lines.append(
                f'@font-face {{ font-family: "{entry.family}"; '
                f'src: url("/api/font-file/{quote(entry.family, safe="")}?weight={entry.weight}&italic={str(entry.italic).lower()}"); '
                f'font-weight: {entry.weight}; '
                f'font-style: {fstyle}; }}'
            )
    css = "\n".join(lines)
    return Response(css, media_type="text/css")


@app.get("/api/font-file/{family:path}")
def api_font_file_path(
    family: str,
    weight: int = Query(400, ge=100, le=900),
    italic: bool = Query(False),
):
    """通过字族名直接获取字体文件，URL 编码支持含空格/中文的字体名"""
    entry = font_reg.find(family, weight=weight, italic=italic)
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
        for svg_file in sorted(cat_dir.rglob("*.svg")):
            name = svg_file.stem
            svg_bytes = svg_file.read_bytes()
            b64 = base64.b64encode(svg_bytes).decode()
            relative = svg_file.relative_to(stickers_dir).as_posix()
            items.append({
                "name": name,
                "src": f"stickers/{relative}",
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


@app.get("/api/images")
def api_images():
    images_dir = ASSETS / "images"
    categories = {}
    if not images_dir.is_dir():
        return {"categories": categories}
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    directories = [images_dir, *(p for p in sorted(images_dir.iterdir()) if p.is_dir())]
    for directory in directories:
        items = []
        for image_file in sorted(directory.iterdir()):
            if not image_file.is_file() or image_file.suffix.lower() not in allowed:
                continue
            relative = image_file.relative_to(images_dir).as_posix()
            items.append({
                "name": image_file.stem,
                "src": f"images/{relative}",
                "thumb": f"/api/image-file/{quote(relative)}",
            })
        if items:
            categories["basic" if directory == images_dir else directory.name] = items
    return {"categories": categories}


@app.get("/api/image-file/{path:path}")
def api_image_file(path: str):
    images_dir = (ASSETS / "images").resolve()
    candidate = (images_dir / path).resolve()
    try:
        candidate.relative_to(images_dir)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Image not found") from exc
    if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"} or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(candidate)

@app.post("/api/render")
def api_render(
    req: RenderRequest = Body(...),
    format: str = Query("png", pattern="^(png|svg)$"),
    width: int = Query(1080, ge=1, le=5000),
    scale: float = Query(1.0, ge=0.25, le=4),
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
        if not el.visible:
            continue
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
                visible=el.visible,
                align=el.align, valign=el.valign,
                text=el.text or el.default, style=style,
            ))
        elif el.type == "sticker":
            sticker_src = el.file or el.src  # prefer original file path
            elements.append(StickerElement(
                id=el.id, x=el.x, y=el.y, w=el.w, h=el.h,
                rotation=el.rotation, z_index=el.z_index,
                visible=el.visible,
                src=sticker_src, style=style,
            ))
        elif el.type == "image":
            elements.append(ImageElement(
                id=el.id, x=el.x, y=el.y, w=el.w, h=el.h,
                rotation=el.rotation, z_index=el.z_index,
                visible=el.visible,
                src=el.src, style=style,
            ))

    layer = Layer(id="main", name="图层1", elements=elements)
    doc = Document(id="render", name="预览", canvas=canvas, layers=[layer])

    if format == "png" and width * scale > 10000:
        raise HTTPException(status_code=422, detail="Final PNG width cannot exceed 10000 pixels")

    svg_compiler = SVGCompiler(font_registry=font_reg)
    try:
        ir = compiler.compile(doc)
        svg = svg_compiler.render(ir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if format == "svg":
        return Response(svg, media_type="image/svg+xml",
                        headers={"Content-Disposition": "attachment; filename=render.svg"})

    use_browser = bool(svg_compiler.used_fonts) and raster.has_browser()
    png_bytes = raster.to_png(svg, output_width=round(width * scale), use_browser=use_browser)
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
