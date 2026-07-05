from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field

from .style import Style


class ElementType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    STICKER = "sticker"
    TAPE = "tape"
    SHAPE = "shape"
    BACKGROUND = "background"


class Element(BaseModel):
    id: str
    x: float = 0.0
    y: float = 0.0
    w: float = 100.0
    h: float = 100.0
    rotation: float = 0.0
    z_index: int = 0
    visible: bool = True
    locked: bool = False
    style: Style = Field(default_factory=Style)


class TextElement(Element):
    type: Literal["text"] = "text"
    text: str = ""
    direction: Literal["horizontal", "vertical"] = "horizontal"
    align: Literal["left", "center", "right"] = "left"
    valign: Literal["top", "middle", "bottom"] = "top"


class ImageElement(Element):
    type: Literal["image"] = "image"
    src: str = ""
    fit: Literal["cover", "contain", "fill"] = "cover"


class StickerElement(Element):
    type: Literal["sticker"] = "sticker"
    src: str = ""


class TapeElement(Element):
    type: Literal["tape"] = "tape"
    src: str = ""


class ShapeElement(Element):
    type: Literal["shape"] = "shape"
    shape: Literal["rect", "ellipse", "line", "path"] = "rect"
    path: Optional[str] = None


class BackgroundElement(Element):
    type: Literal["background"] = "background"
    src: Optional[str] = None
    pattern: Literal["none", "lines", "grid", "dots"] = "none"


ElementUnion = Annotated[
    Union[
        TextElement,
        ImageElement,
        StickerElement,
        TapeElement,
        ShapeElement,
        BackgroundElement,
    ],
    Field(discriminator="type"),
]
