"""
手账编辑器 Web 服务

提供素材查询和渲染 API，配合前端画布实现所见即所得编辑。
启动: python web/server.py
访问: http://localhost:8128
"""
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from shouzhang.engine.fonts import FontRegistry
from shouzhang.render import DocumentCompiler, SVGCompiler, Rasterizer
from shouzhang.models.document import Canvas, Document, Layer
from shouzhang.models.element import TextElement, StickerElement
from shouzhang.models.style import Style, FontStyle

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS_DIR = ROOT / "src" / "font"
STATIC = Path(__file__).resolve().parent / "static"

# ---- 全局资源 ----
font_reg = FontRegistry()
font_reg.scan(FONTS_DIR)

_stickers: dict[str, list[dict]] = {}
_backgrounds: list[dict] = []


def _scan_assets():
    _stickers.clear()
    _backgrounds.clear()
    stickers_dir = ASSETS / "stickers"
    if stickers_dir.is_dir():
        for d in sorted(stickers_dir.iterdir()):
            if d.is_dir():
                cats = []
                for f in sorted(d.glob("*.svg")):
                    cats.append({"name": f.stem, "path": str(f.relative_to(ASSETS))})
                if cats:
                    _stickers[d.name] = cats
        root_svgs = [{"name": f.stem, "path": str(f.relative_to(ASSETS))}
                     for f in sorted(stickers_dir.glob("*.svg"))]
        if root_svgs:
            _stickers["根目录"] = root_svgs
    bg_dir = ASSETS / "backgrounds"
    if bg_dir.is_dir():
        for f in sorted(bg_dir.glob("*.svg")):
            _backgrounds.append({"name": f.stem, "path": str(f.relative_to(ASSETS))})

_scan_assets()

# ---- FastAPI ----
app = FastAPI(title="手账编辑器", version="0.1.0")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


# ========== API ==========

@app.get("/api/fonts")
async def list_fonts():
    families = font_reg.list_families()
    return [
        {"family": f, "count": len(font_reg.get_entries(f))}
        for f in families
    ]


@app.get("/api/stickers")
async def list_stickers():
    return {"categories": _stickers}


@app.get("/api/backgrounds")
async def list_backgrounds():
    return [{"name": b["name"], "path": b["path"]} for b in _backgrounds]


@app.get("/api/background/{bg_id}")
async def get_background(bg_id: str):
    """返回背景 SVG 内容，用于前端画布渲染。"""
    for b in _backgrounds:
        if b["name"] == bg_id:
            svg_path = ASSETS / b["path"]
            if svg_path.exists():
                return Response(svg_path.read_text(encoding="utf-8"), media_type="image/svg+xml")
    return Response(status=404)


@app.post("/api/render")
async def render_to_png(data: dict):
    """
    接收前端传来的 JSON（包含 canvas + elements），
    渲染为 PNG 返回。

    Body:
      {
        "width": 1080,
        "height": 1527,
        "background": "#fbfaf6",
        "elements": [
          {
            "type": "text",
            "id": "t1", "x": 100, "y": 200, "w": 500, "h": 60,
            "text": "你好世界",
            "family": "Noto Sans SC",
            "size": 36,
            "weight": 400,
            "color": "#333",
            "align": "left",
            "rotation": 0
          },
          {
            "type": "sticker",
            "id": "s1", "x": 300, "y": 400, "w": 80, "h": 80,
            "src": "stickers/star.svg",
            "rotation": 15
          }
        ]
      }
    """
    from shouzhang.render.protocol import RenderIR, DrawGroup, DrawText, DrawSVG, Transform

    w = data.get("width", 1080)
    h = data.get("height", 1527)
    bg = data.get("background", "#fbfaf6")
    elements = data.get("elements", [])

    commands: list = []
    has_custom_fonts = False

    for el in elements:
        t = Transform(
            translate_x=el.get("x", 0),
            translate_y=el.get("y", 0),
            rotate=el.get("rotation", 0),
            rotate_cx=el.get("w", 100) / 2,
            rotate_cy=el.get("h", 100) / 2,
        )
        el_type = el.get("type", "text")

        if el_type == "text":
            family = el.get("family", "sans-serif")
            if family not in ("serif", "sans-serif", "monospace", "cursive", "fantasy"):
                has_custom_fonts = True
            text_cmd = DrawText(
                x=0, y=0,
                w=el.get("w", 200), h=el.get("h", 60),
                text=el.get("text", ""),
                family=family,
                size=el.get("size", 24),
                weight=el.get("weight", 400),
                color=el.get("color", "#333"),
                align=el.get("align", "left"),
                valign="top",
                line_height=el.get("line_height", 1.5),
            )
            commands.append(DrawGroup(transform=t, children=[text_cmd]))

        elif el_type == "sticker":
            src = el.get("src", "")
            full_src = str(ASSETS / src) if src else ""
            sticker = DrawSVG(
                x=0, y=0,
                w=el.get("w", 80), h=el.get("h", 80),
                src=full_src,
            )
            commands.append(DrawGroup(transform=t, children=[sticker]))

    ir = RenderIR(width=w, height=h, background=bg, commands=commands)

    svgc = SVGCompiler(font_registry=font_reg)
    svg_str = svgc.render(ir)

    raster = Rasterizer()
    use_browser = bool(has_custom_fonts) and raster.has_browser()
    png_bytes = raster.to_png(svg_str, output_width=w, use_browser=use_browser)

    return Response(content=png_bytes, media_type="image/png")


@app.get("/api/sticker-svg/{path:path}")
async def get_sticker_svg(path: str):
    full = ASSETS / path
    if full.exists() and full.suffix == ".svg":
        return Response(full.read_text(encoding="utf-8"), media_type="image/svg+xml")
    return Response(status=404)


@app.get("/api/font-file/{family}")
async def get_font_file(family: str):
    try:
        entry = font_reg.find(family)
        if entry and entry.path.exists():
            return FileResponse(entry.path, media_type="font/ttf")
    except Exception:
        pass
    return Response(status=404)


@app.post("/api/render-svg")
async def render_to_svg(data: dict):
    """返回渲染后的 SVG 字符串（含 @font-face）。"""
    from shouzhang.render.protocol import RenderIR, DrawGroup, DrawText, DrawSVG, Transform

    w = data.get("width", 1080)
    h = data.get("height", 1527)
    bg = data.get("background", "#fbfaf6")
    elements = data.get("elements", [])

    commands: list = []
    for el in elements:
        t = Transform(
            translate_x=el.get("x", 0), translate_y=el.get("y", 0),
            rotate=el.get("rotation", 0),
            rotate_cx=el.get("w", 100) / 2, rotate_cy=el.get("h", 100) / 2,
        )
        el_type = el.get("type", "text")
        if el_type == "text":
            commands.append(DrawGroup(transform=t, children=[DrawText(
                x=0, y=0, w=el.get("w", 200), h=el.get("h", 60),
                text=el.get("text", ""),
                family=el.get("family", "sans-serif"),
                size=el.get("size", 24), weight=el.get("weight", 400),
                color=el.get("color", "#333"),
                align=el.get("align", "left"), valign="top",
                line_height=el.get("line_height", 1.5),
            )]))
        elif el_type == "sticker":
            src = el.get("src", "")
            full_src = str(ASSETS / src) if src else ""
            commands.append(DrawGroup(transform=t, children=[DrawSVG(
                x=0, y=0, w=el.get("w", 80), h=el.get("h", 80), src=full_src,
            )]))

    ir = RenderIR(width=w, height=h, background=bg, commands=commands)
    svgc = SVGCompiler(font_registry=font_reg)
    svg_str = svgc.render(ir)
    return Response(content=svg_str, media_type="image/svg+xml")


# ========== 启动 ==========
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

if __name__ == "__main__":
    import uvicorn
    print(f"  素材目录: {ASSETS}")
    print(f"  字体目录: {FONTS_DIR}")
    print(f"  贴纸: {sum(len(v) for v in _stickers.values())} 个")
    print(f"  字体: {len(font_reg.list_families())} 种")
    print(f"\n  编辑器: http://localhost:8128")
    try:
        import webbrowser
        webbrowser.open("http://localhost:8128")
    except Exception:
        pass
    uvicorn.run(app, host="0.0.0.0", port=8128, log_level="warning")
