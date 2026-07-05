from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from ..models.style import ShadowStyle, TextSpan


class Transform(BaseModel):
    translate_x: float = 0.0
    translate_y: float = 0.0
    rotate: float = 0.0
    rotate_cx: float = 0.0
    rotate_cy: float = 0.0
    scale: float = 1.0


class DrawCommand(BaseModel):
    cmd: str


class DrawRect(DrawCommand):
    cmd: Literal["rect"] = "rect"
    x: float = 0.0
    y: float = 0.0
    w: float
    h: float
    rx: float = 0.0
    ry: float = 0.0
    fill: str = "none"
    stroke: str = "none"
    stroke_width: float = 0.0
    stroke_dash: Optional[str] = None
    opacity: float = 1.0


class DrawText(DrawCommand):
    cmd: Literal["text"] = "text"
    x: float = 0.0
    y: float = 0.0
    w: float
    h: float
    text: str
    family: str = "sans-serif"
    size: float = 16.0
    weight: int = 400
    color: str = "#000000"
    line_height: float = 1.6
    letter_spacing: float = 0.0
    italic: bool = False
    underline: bool = False
    align: Literal["left", "center", "right"] = "left"
    valign: Literal["top", "middle", "bottom"] = "top"
    direction: Literal["horizontal", "vertical"] = "horizontal"
    opacity: float = 1.0
    spans: list[TextSpan] = Field(default_factory=list)


class DrawImage(DrawCommand):
    cmd: Literal["image"] = "image"
    x: float = 0.0
    y: float = 0.0
    w: float
    h: float
    src: str
    fit: Literal["cover", "contain", "fill"] = "cover"
    opacity: float = 1.0


class DrawPath(DrawCommand):
    cmd: Literal["path"] = "path"
    d: str
    x: float = 0.0
    y: float = 0.0
    fill: str = "none"
    stroke: str = "none"
    stroke_width: float = 0.0
    opacity: float = 1.0


class DrawSVG(DrawCommand):
    cmd: Literal["svg"] = "svg"
    x: float = 0.0
    y: float = 0.0
    w: float
    h: float
    src: str
    opacity: float = 1.0


class DrawGroup(DrawCommand):
    cmd: Literal["group"] = "group"
    transform: Transform = Field(default_factory=Transform)
    opacity: float = 1.0
    shadow: Optional[ShadowStyle] = None
    children: list["DrawCommandUnion"] = Field(default_factory=list)


DrawCommandUnion = Annotated[
    Union[DrawRect, DrawText, DrawImage, DrawPath, DrawSVG, DrawGroup],
    Field(discriminator="cmd"),
]


class RenderIR(BaseModel):
    width: float
    height: float
    background: str
    commands: list[DrawCommandUnion] = Field(default_factory=list)


DrawGroup.model_rebuild()
