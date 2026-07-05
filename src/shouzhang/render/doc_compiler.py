from pathlib import Path
from typing import Optional, Union

from ..models.document import Document
from ..models.element import (
    Element,
    TextElement,
    ImageElement,
    StickerElement,
    TapeElement,
    ShapeElement,
    BackgroundElement,
)
from ..engine.text_layout import wrap_text
from ..engine.rich_text import has_markup, parse_rich_text, wrap_spans, rich_plain_text
from .protocol import (
    DrawGroup,
    DrawImage,
    DrawPath,
    DrawRect,
    DrawSVG,
    DrawText,
    DrawCommandUnion,
    RenderIR,
    Transform,
)


class DocumentCompiler:
    """把 Document 编译成渲染 IR。每个元素 → 一个 DrawGroup（携带变换/透明度/阴影）。"""

    def __init__(self, assets_root: Optional[Union[str, Path]] = None) -> None:
        self.assets_root = Path(assets_root) if assets_root else None

    def compile(self, doc: Document) -> RenderIR:
        commands: list[DrawCommandUnion] = []
        commands.append(self._compile_canvas(doc))
        for el in doc.all_elements():
            group = self._compile_element(el)
            if group is not None:
                commands.append(group)
        return RenderIR(
            width=doc.canvas.width,
            height=doc.canvas.height,
            background=doc.canvas.background,
            commands=commands,
        )

    def _resolve_src(self, src: str) -> str:
        if self.assets_root and not Path(src).is_absolute():
            return str(self.assets_root / src)
        return src

    def _element_transform(self, el: Element) -> Transform:
        return Transform(
            translate_x=el.x,
            translate_y=el.y,
            rotate=el.rotation,
            rotate_cx=el.w / 2,
            rotate_cy=el.h / 2,
        )

    def _compile_canvas(self, doc: Document) -> DrawGroup:
        c = doc.canvas
        children: list[DrawCommandUnion] = [
            DrawRect(x=0, y=0, w=c.width, h=c.height, fill=c.background)
        ]
        children.extend(self._pattern_commands(c))
        return DrawGroup(children=children)

    def _pattern_commands(self, canvas) -> list[DrawCommandUnion]:
        if canvas.pattern == "none":
            return []
        s = canvas.pattern_spacing
        color = canvas.pattern_color
        out: list[DrawCommandUnion] = []
        if canvas.pattern in ("lines", "grid"):
            y = s
            while y < canvas.height:
                out.append(
                    DrawPath(
                        d=f"M 0 {y} L {canvas.width} {y}",
                        stroke=color,
                        stroke_width=1.0,
                    )
                )
                y += s
        if canvas.pattern == "grid":
            x = s
            while x < canvas.width:
                out.append(
                    DrawPath(
                        d=f"M {x} 0 L {x} {canvas.height}",
                        stroke=color,
                        stroke_width=1.0,
                    )
                )
                x += s
        if canvas.pattern == "dots":
            y = s
            while y < canvas.height:
                x = s
                while x < canvas.width:
                    out.append(
                        DrawRect(
                            x=x - 0.6, y=y - 0.6, w=1.2, h=1.2, fill=color
                        )
                    )
                    x += s
                y += s
        return out

    def _compile_element(self, el: Element) -> Optional[DrawGroup]:
        transform = self._element_transform(el)
        opacity = el.style.opacity
        shadow = el.style.shadow if el.style.shadow and el.style.shadow.blur > 0 else None
        if isinstance(el, TextElement):
            children = self._compile_text(el)
        elif isinstance(el, ImageElement):
            children = self._compile_image(el)
        elif isinstance(el, StickerElement):
            children = self._compile_sticker(el)
        elif isinstance(el, TapeElement):
            children = self._compile_tape(el)
        elif isinstance(el, ShapeElement):
            children = self._compile_shape(el)
        elif isinstance(el, BackgroundElement):
            children = self._compile_bg_element(el)
        else:
            return None
        if not children:
            return None
        return DrawGroup(transform=transform, opacity=opacity, shadow=shadow, children=children)

    def _compile_text(self, el: TextElement) -> list[DrawCommandUnion]:
        f = el.style.font
        text = el.text
        spans: list = []
        if el.direction == "horizontal":
            if has_markup(text):
                parsed = parse_rich_text(text)
                lines = wrap_spans(parsed, f.size, el.w, f.letter_spacing)
                spans = [s for line in lines for s in line]
                text = "\n".join("".join(s.text for s in line) for line in lines)
            else:
                text = wrap_text(text, f.size, el.w, f.letter_spacing)
        return [
            DrawText(
                x=0, y=0, w=el.w, h=el.h,
                text=text,
                family=f.family, size=f.size, weight=f.weight, color=f.color,
                line_height=f.line_height, letter_spacing=f.letter_spacing,
                italic=f.italic, underline=f.underline,
                align=el.align, valign=el.valign, direction=el.direction,
                spans=spans,
            )
        ]

    def _compile_image(self, el: ImageElement) -> list[DrawCommandUnion]:
        if not el.src:
            return []
        return [DrawImage(x=0, y=0, w=el.w, h=el.h, src=self._resolve_src(el.src), fit=el.fit)]

    def _compile_sticker(self, el: StickerElement) -> list[DrawCommandUnion]:
        if not el.src:
            return []
        return [DrawSVG(x=0, y=0, w=el.w, h=el.h, src=self._resolve_src(el.src))]

    def _compile_tape(self, el: TapeElement) -> list[DrawCommandUnion]:
        if not el.src:
            return []
        return [DrawSVG(x=0, y=0, w=el.w, h=el.h, src=self._resolve_src(el.src))]

    def _compile_shape(self, el: ShapeElement) -> list[DrawCommandUnion]:
        fill = el.style.fill.color if el.style.fill.type != "none" else "none"
        b = el.style.border
        stroke = b.color if b.width > 0 else "none"
        if el.shape == "rect":
            return [
                DrawRect(
                    x=0, y=0, w=el.w, h=el.h, rx=b.radius, ry=b.radius,
                    fill=fill, stroke=stroke, stroke_width=b.width,
                )
            ]
        if el.shape == "ellipse":
            cx, cy, rx, ry = el.w / 2, el.h / 2, el.w / 2, el.h / 2
            return [
                DrawPath(
                    d=f"M {cx - rx} {cy} a {rx} {ry} 0 1 0 {rx * 2} 0 a {rx} {ry} 0 1 0 {-rx * 2} 0 Z",
                    fill=fill, stroke=stroke, stroke_width=b.width,
                )
            ]
        if el.shape == "line":
            return [
                DrawPath(d=f"M 0 0 L {el.w} {el.h}", stroke=stroke or "#000", stroke_width=b.width or 1.0)
            ]
        if el.shape == "path" and el.path:
            return [DrawPath(d=el.path, fill=fill, stroke=stroke, stroke_width=b.width)]
        return []

    def _compile_bg_element(self, el: BackgroundElement) -> list[DrawCommandUnion]:
        if el.src:
            return [DrawSVG(x=0, y=0, w=el.w, h=el.h, src=self._resolve_src(el.src))]
        return []
