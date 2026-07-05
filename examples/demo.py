from pathlib import Path

from shouzhang.render import DocumentCompiler, Rasterizer, SVGCompiler
from shouzhang.engine.fonts import FontRegistry
from shouzhang.templates import TemplateRegistry

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "examples" / "out"


def main() -> None:
    reg = TemplateRegistry()
    n = reg.load_dir(ROOT / "src" / "shouzhang" / "templates" / "builtin")
    print(f"已加载模板 {n} 个: {[t.id for t in reg.list()]}")

    font_reg = FontRegistry()
    n_fonts = font_reg.scan(ROOT / "src" / "font")
    print(f"字体 {n_fonts} 个")

    compiler = DocumentCompiler(assets_root=ROOT / "assets")
    svg_compiler = SVGCompiler(font_registry=font_reg)
    raster = Rasterizer()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"PNG 后端: {raster.backend}, 浏览器: {'Edge' if raster.has_browser() else '无'}")

    for tpl in reg.list():
        doc = reg.instantiate(tpl.id)
        ir = compiler.compile(doc)
        svg = svg_compiler.render(ir)
        (OUT / f"{tpl.id}.svg").write_text(svg, encoding="utf-8")

        use_browser = bool(svg_compiler.used_fonts) and raster.has_browser()
        mode = "edge" if use_browser else "resvg"

        if use_browser or raster.available():
            raster.to_file(svg, OUT / f"{tpl.id}.png", output_width=1080, use_browser=use_browser)
            print(f"  {tpl.id} -> {tpl.id}.svg + {tpl.id}.png [{mode}]")
        else:
            print(f"  {tpl.id} -> {tpl.id}.svg [无可用PNG后端]")


if __name__ == "__main__":
    main()
