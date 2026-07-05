import base64
import re
from pathlib import Path
from typing import Optional, Union

from .protocol import (
    DrawCommand,
    DrawGroup,
    DrawImage,
    DrawPath,
    DrawRect,
    DrawSVG,
    DrawText,
    RenderIR,
)
from ..models.style import TextSpan
from ..engine.fonts import FontRegistry


def _f(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return f"{v:.3f}".rstrip("0").rstrip(".")


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _family(s: str) -> str:
    if " " in s:
        return f"'{s}'"
    return s


def _split_rgba(color: str) -> tuple[str, float]:
    m = re.match(r"rgba?\(([^)]+)\)", color.strip())
    if not m:
        return color, 1.0
    parts = [p.strip() for p in m.group(1).split(",")]
    if len(parts) == 4:
        r, g, b, a = parts
        return f"rgb({r},{g},{b})", float(a)
    return f"rgb({parts[0]},{parts[1]},{parts[2]})", 1.0


def _split_spans_by_lines(spans: list[TextSpan], text_lines: list[str]) -> list[list[TextSpan]]:
    """将平铺的 spans 按文本行切分成每行一组。"""
    result: list[list[TextSpan]] = []
    si = 0
    for line in text_lines:
        line_spans: list[TextSpan] = []
        remaining = line
        while remaining and si < len(spans):
            sp = spans[si]
            if len(sp.text) <= len(remaining) and remaining.startswith(sp.text):
                line_spans.append(sp)
                remaining = remaining[len(sp.text) :]
                si += 1
            else:
                break
        result.append(line_spans)
    return result


class SVGCompiler:
    """渲染 IR → SVG 字符串。矢量输出，天然清晰，可缩放。"""

    def __init__(self, assets_root: Optional[Union[str, Path]] = None, font_registry: Optional[FontRegistry] = None) -> None:
        self.assets_root = Path(assets_root) if assets_root else None
        self.font_registry = font_registry
        self._filters: dict[tuple, str] = {}
        self._symbols: dict[str, str] = {}
        self._used_fonts: set[str] = set()

    @property
    def used_fonts(self) -> set[str]:
        return self._used_fonts.copy()

    def render(self, ir: RenderIR) -> str:
        self._filters.clear()
        self._symbols.clear()
        self._used_fonts.clear()
        body: list[str] = []
        for cmd in ir.commands:
            body.append(self._render(cmd))
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{_f(ir.width)}" height="{_f(ir.height)}" '
            f'viewBox="0 0 {_f(ir.width)} {_f(ir.height)}">',
            self._defs(),
            f'<rect width="{_f(ir.width)}" height="{_f(ir.height)}" fill="{_esc(ir.background)}"/>',
            *body,
            "</svg>",
        ]
        return "\n".join(out)

    def _defs(self) -> str:
        if not self._filters and not self._symbols and not self._used_fonts:
            return ""
        parts = ["<defs>"]
        if self.font_registry and self._used_fonts:
            parts.append("<style>")
            for family in sorted(self._used_fonts):
                entry = self.font_registry.find(family)
                if entry:
                    fpath = entry.path.resolve().as_uri()
                    parts.append(
                        f'@font-face {{ font-family: "{family}"; '
                        f'src: url("{_esc(fpath)}"); }}'
                    )
            parts.append("</style>")
        for (color, blur, ox, oy), fid in self._filters.items():
            base, alpha = _split_rgba(color)
            parts.append(
                f'<filter id="{fid}" x="-30%" y="-30%" width="160%" height="160%">'
                f'<feGaussianBlur in="SourceAlpha" stdDeviation="{_f(blur)}"/>'
                f'<feOffset dx="{_f(ox)}" dy="{_f(oy)}" result="ob"/>'
                f'<feComponentTransfer in="ob" result="s">'
                f'<feFuncA type="linear" slope="{_f(alpha)}"/></feComponentTransfer>'
                f'<feFlood flood-color="{base}" result="c"/>'
                f'<feComposite in="c" in2="s" operator="in"/>'
                f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
                f"</filter>"
            )
        for sid, inner in self._symbols.items():
            parts.append(f"<symbol id=\"{sid}\">{inner}</symbol>")
        parts.append("</defs>")
        return "\n".join(parts)

    def _render(self, cmd: DrawCommand) -> str:
        if isinstance(cmd, DrawGroup):
            return self._render_group(cmd)
        if isinstance(cmd, DrawRect):
            return self._render_rect(cmd)
        if isinstance(cmd, DrawText):
            return self._render_text(cmd)
        if isinstance(cmd, DrawImage):
            return self._render_image(cmd)
        if isinstance(cmd, DrawPath):
            return self._render_path(cmd)
        if isinstance(cmd, DrawSVG):
            return self._render_svg(cmd)
        return ""

    def _render_group(self, g: DrawGroup) -> str:
        attrs: list[str] = []
        t = g.transform
        tf: list[str] = []
        if t.translate_x or t.translate_y:
            tf.append(f"translate({_f(t.translate_x)},{_f(t.translate_y)})")
        if t.rotate:
            tf.append(f"rotate({_f(t.rotate)},{_f(t.rotate_cx)},{_f(t.rotate_cy)})")
        if t.scale != 1.0:
            tf.append(f"scale({_f(t.scale)})")
        if tf:
            attrs.append(f'transform="{" ".join(tf)}"')
        if g.opacity != 1.0:
            attrs.append(f'opacity="{_f(g.opacity)}"')
        if g.shadow:
            fid = self._shadow_filter_id(g.shadow)
            attrs.append(f'filter="url(#{fid})"')
        inner = "\n".join(self._render(c) for c in g.children)
        a = (" " + " ".join(attrs)) if attrs else ""
        return f"<g{a}>\n{inner}\n</g>"

    def _shadow_filter_id(self, shadow) -> str:
        base, alpha = _split_rgba(shadow.color)
        key = (base, alpha, shadow.blur, shadow.offset_x, shadow.offset_y)
        if key in self._filters:
            return self._filters[key]
        fid = f"sh{len(self._filters)}"
        self._filters[key] = fid
        return fid

    def _track_font(self, family: str) -> None:
        generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
        if family.lower() not in generic and self.font_registry:
            if self.font_registry.find(family):
                self._used_fonts.add(family)

    def _render_rect(self, r: DrawRect) -> str:
        attrs = [
            f'x="{_f(r.x)}"', f'y="{_f(r.y)}"',
            f'width="{_f(r.w)}"', f'height="{_f(r.h)}"',
        ]
        if r.rx:
            attrs.append(f'rx="{_f(r.rx)}"')
        if r.ry:
            attrs.append(f'ry="{_f(r.ry)}"')
        attrs.append(f'fill="{_esc(r.fill)}"')
        if r.stroke != "none":
            attrs.append(f'stroke="{_esc(r.stroke)}"')
            attrs.append(f'stroke-width="{_f(r.stroke_width)}"')
            if r.stroke_dash:
                attrs.append(f'stroke-dasharray="{r.stroke_dash}"')
        if r.opacity != 1.0:
            attrs.append(f'opacity="{_f(r.opacity)}"')
        return f"<rect {' '.join(attrs)}/>"

    def _render_path(self, p: DrawPath) -> str:
        attrs = [f'd="{p.d}"', f'fill="{_esc(p.fill)}"']
        if p.stroke != "none":
            attrs.append(f'stroke="{_esc(p.stroke)}"')
            attrs.append(f'stroke-width="{_f(p.stroke_width)}"')
        if p.opacity != 1.0:
            attrs.append(f'opacity="{_f(p.opacity)}"')
        return f"<path {' '.join(attrs)}/>"

    def _render_text(self, t: DrawText) -> str:
        self._track_font(t.family)
        if t.spans:
            return self._render_rich_text(t)
        lines = t.text.split("\n")
        anchor = {"left": "start", "center": "middle", "right": "end"}[t.align]
        attrs = [
            f'font-family="{_family(t.family)}"',
            f'font-size="{_f(t.size)}"',
            f'font-weight="{t.weight}"',
            f'fill="{_esc(t.color)}"',
            f'text-anchor="{anchor}"',
        ]
        if t.italic:
            attrs.append('font-style="italic"')
        if t.letter_spacing:
            attrs.append(f'letter-spacing="{_f(t.letter_spacing)}"')
        if t.opacity != 1.0:
            attrs.append(f'opacity="{_f(t.opacity)}"')
        lh = t.size * t.line_height
        total_h = len(lines) * lh
        ascent = t.size * 0.8
        if t.valign == "middle":
            start_y = (t.h - total_h) / 2 + ascent
        elif t.valign == "bottom":
            start_y = t.h - total_h + ascent
        else:
            start_y = ascent
        if t.align == "left":
            x = t.x
        elif t.align == "center":
            x = t.x + t.w / 2
        else:
            x = t.x + t.w
        tspans = []
        for i, line in enumerate(lines):
            ly = start_y + i * lh
            tspans.append(f'<tspan x="{_f(x)}" y="{_f(ly)}">{_esc(line)}</tspan>')
        return f"<text {' '.join(attrs)}>{''.join(tspans)}</text>"

    def _render_rich_text(self, t: DrawText) -> str:
        self._track_font(t.family)
        from ..engine.text_layout import char_width

        text_lines = t.text.split("\n")
        anchor = {"left": "start", "center": "middle", "right": "end"}[t.align]
        base_attrs = f'font-family="{_family(t.family)}" font-size="{_f(t.size)}" fill="{_esc(t.color)}" text-anchor="{anchor}"'
        if t.letter_spacing:
            base_attrs += f' letter-spacing="{_f(t.letter_spacing)}"'
        if t.opacity != 1.0:
            base_attrs += f' opacity="{_f(t.opacity)}"'

        lh = t.size * t.line_height
        total_h = len(text_lines) * lh
        ascent = t.size * 0.8
        if t.valign == "middle":
            start_y = (t.h - total_h) / 2 + ascent
        elif t.valign == "bottom":
            start_y = t.h - total_h + ascent
        else:
            start_y = ascent

        # 按 line 切分 spans（每行的 spans 列表来自 t.spans）
        line_spans = _split_spans_by_lines(t.spans, text_lines)

        parts: list[str] = []
        deco_parts: list[str] = []

        for li, (line_text, spans) in enumerate(zip(text_lines, line_spans)):
            ly = start_y + li * lh
            if t.align == "left":
                cx = t.x
            elif t.align == "center":
                cx = t.x + t.w / 2
            else:
                cx = t.x + t.w

            for sp in spans:
                sp_size = sp.size_override or t.size
                sp_color = sp.color or t.color
                sp_weight = 700 if sp.bold else t.weight
                sp_attrs = f'font-size="{_f(sp_size)}" fill="{_esc(sp_color)}" font-weight="{sp_weight}"'
                if sp.italic:
                    sp_attrs += ' font-style="italic"'

                parts.append(
                    f'<tspan x="{_f(cx)}" y="{_f(ly)}" {sp_attrs}>{_esc(sp.text)}</tspan>'
                )

                sp_w = sum(char_width(c, sp_size) for c in sp.text)

                if sp.underline:
                    uly = ly + sp_size * 0.22
                    deco_parts.append(
                        f'<line x1="{_f(cx)}" y1="{_f(uly)}" x2="{_f(cx + sp_w)}" y2="{_f(uly)}" '
                        f'stroke="{sp_color}" stroke-width="{_f(sp_size * 0.06)}" stroke-linecap="round"/>'
                    )

                if sp.dots:
                    dot_y = ly + sp_size * 0.24
                    dot_r = sp_size * 0.08
                    acc = 0.0
                    for ch in sp.text:
                        cw = char_width(ch, sp_size)
                        dot_cx = cx + acc + cw / 2
                        deco_parts.append(
                            f'<circle cx="{_f(dot_cx)}" cy="{_f(dot_y)}" r="{_f(dot_r)}" fill="{sp_color}"/>'
                        )
                        acc += cw

                cx += sp_w

        result = f'<text {base_attrs}>{"".join(parts)}</text>'
        if deco_parts:
            result = result + "\n" + "\n".join(deco_parts)
        return result

    def _render_image(self, im: DrawImage) -> str:
        if im.src.startswith("data:"):
            href = im.src
        else:
            data, mime = self._load_image(im.src)
            href = f"data:{mime};base64,{base64.b64encode(data).decode()}"
        aspect = {"cover": "xMidYMid slice", "contain": "xMidYMid meet", "fill": "none"}[im.fit]
        attrs = [
            f'x="{_f(im.x)}"', f'y="{_f(im.y)}"',
            f'width="{_f(im.w)}"', f'height="{_f(im.h)}"',
            f'href="{href}"',
            f'preserveAspectRatio="{aspect}"',
        ]
        if im.opacity != 1.0:
            attrs.append(f'opacity="{_f(im.opacity)}"')
        return f"<image {' '.join(attrs)}/>"

    def _load_image(self, src: str) -> tuple[bytes, str]:
        p = Path(src)
        data = p.read_bytes()
        ext = p.suffix.lower().lstrip(".")
        mime = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
        }.get(ext, "image/png")
        return data, mime

    def _render_svg(self, s: DrawSVG) -> str:
        vb_w, vb_h, inner = self._load_svg(s.src)
        sx = s.w / vb_w if vb_w else 1.0
        sy = s.h / vb_h if vb_h else 1.0
        opacity = f' opacity="{_f(s.opacity)}"' if s.opacity != 1.0 else ""
        return (
            f'<g transform="translate({_f(s.x)},{_f(s.y)}) scale({_f(sx)},{_f(sy)})"{opacity}>\n'
            f"{inner}\n</g>"
        )

    def _load_svg(self, src: str) -> tuple[float, float, str]:
        content = Path(src).read_text(encoding="utf-8")
        m = re.search(r'viewBox="([\d.\s\-]+)"', content)
        if m:
            parts = m.group(1).split()
            vb_w, vb_h = float(parts[2]), float(parts[3])
        else:
            mw = re.search(r'width="([\d.]+)"', content)
            mh = re.search(r'height="([\d.]+)"', content)
            vb_w = float(mw.group(1)) if mw else 100.0
            vb_h = float(mh.group(1)) if mh else 100.0
        inner = re.search(r"<svg[^>]*>(.*)</svg>", content, re.DOTALL)
        inner_str = inner.group(1).strip() if inner else ""
        return vb_w, vb_h, inner_str
